"""
Rule extraction and mapping engine using aiXplain models.
"""
import json
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from loguru import logger

from src.models import (
    Document, ExtractedRule, SourceReference, RuleStatus
)
from src.tracks import TracksRepository, FinancialTrack
from src.aixplain_client import AIXplainClient
from src.config import config


class RuleExtractor:
    """Extracts rules from documents using AI models with RAG support."""
    
    def __init__(self, client: AIXplainClient):
        self.client = client
        self.tracks = TracksRepository.get_all_tracks()
        self.use_rag = True  # Enable RAG by default
    
    def extract_rules_with_retrieval(
        self,
        document_id: str,
        queries: List[str],
        document_name: str = None
    ) -> List[ExtractedRule]:
        """
        Extract rules using RAG approach (Retrieval-Augmented Generation).
        This is the TRUE RAG implementation - OPTIMIZED for efficiency.
        
        Args:
            document_id: ID of indexed document
            queries: List of queries to retrieve relevant chunks
            document_name: Name of document (for metadata)
            
        Returns:
            List of extracted rules
        """
        logger.info(f"Extracting rules with RAG for document: {document_id}")
        logger.info(f"Using {len(queries)} queries for retrieval")
        
        # Collect all unique chunks first
        all_retrieved_chunks = {}  # chunk_id -> chunk_data (for deduplication)
        
        for query_idx, query in enumerate(queries):
            logger.info(f"Retrieving chunks for query {query_idx + 1}/{len(queries)}: {query[:100]}...")
            
            try:
                # Step 1: Retrieve relevant chunks using semantic search
                retrieved_chunks = self.client.semantic_search(
                    query=query,
                    top_k=config.aixplain.retrieval_top_k
                )
                
                if not retrieved_chunks:
                    logger.warning(f"No chunks retrieved for query: {query[:50]}")
                    continue
                
                logger.info(f"Retrieved {len(retrieved_chunks)} chunks for this query")
                
                # Add to collection (deduplicates automatically by chunk_id)
                for chunk_data in retrieved_chunks:
                    chunk_id = chunk_data.get('id')
                    if chunk_id not in all_retrieved_chunks:
                        all_retrieved_chunks[chunk_id] = chunk_data
                
            except Exception as e:
                logger.error(f"Failed to retrieve for query '{query[:50]}': {e}")
                continue
        
        logger.info(f"Total unique chunks retrieved: {len(all_retrieved_chunks)}")
        
        # Step 2: Extract rules from all unique chunks (batch processing)
        all_rules = []
        
        if not all_retrieved_chunks:
            logger.warning("No chunks retrieved - falling back to pattern-based extraction")
            return []
        
        # Process chunks in batches to reduce LLM calls
        chunk_list = list(all_retrieved_chunks.values())
        batch_size = 5  # Process 5 chunks at once
        
        for batch_idx in range(0, len(chunk_list), batch_size):
            batch = chunk_list[batch_idx:batch_idx + batch_size]
            logger.info(f"Processing batch {batch_idx//batch_size + 1}/{(len(chunk_list) + batch_size - 1)//batch_size} ({len(batch)} chunks)")
            
            # Combine batch chunks for single LLM call
            batch_rules = self._extract_from_chunk_batch(
                chunks=batch,
                document_id=document_id,
                document_name=document_name
            )
            
            all_rules.extend(batch_rules)
        
        # Deduplicate rules by text
        unique_rules = []
        seen_texts = set()
        
        for rule in all_rules:
            if rule.text_ar not in seen_texts:
                seen_texts.add(rule.text_ar)
                unique_rules.append(rule)
        
        logger.info(f"RAG extraction complete: {len(unique_rules)} unique rules extracted")
        return unique_rules
    
    def _extract_from_chunk_batch(
        self,
        chunks: List[Dict],
        document_id: str,
        document_name: str = None
    ) -> List[ExtractedRule]:
        """
        Extract rules from a batch of chunks using a SINGLE LLM call.
        This dramatically reduces API calls and processing time.
        
        Args:
            chunks: List of chunk dictionaries
            document_id: Document ID
            document_name: Document name
            
        Returns:
            List of extracted rules from all chunks in batch
        """
        # Check if LLM is available
        if not self.client.llm_model:
            logger.info("No LLM available, using pattern-based extraction for batch")
            # Process with pattern-based
            all_rules = []
            for chunk_data in chunks:
                rules = self._pattern_based_extraction_from_chunk(
                    chunk_data['text'],
                    chunk_data,
                    chunk_data.get('score', 0.5)
                )
                all_rules.extend(rules)
            return all_rules
        
        # Combine chunks into single context
        combined_text = "\n\n---\n\n".join([
            f"[مقطع {i+1}]\n{chunk['text']}"
            for i, chunk in enumerate(chunks)
        ])
        
        # Build batch extraction prompt
        prompt = self._build_batch_extraction_prompt(combined_text)
        
        try:
            logger.info(f"Executing LLM on batch of {len(chunks)} chunks (SINGLE API CALL)")
            response = self.client.execute_llm(prompt, max_tokens=4000)
            
            # Parse response
            rules = self._parse_extraction_response(
                response,
                document_id=document_id,
                document_name=document_name,
                chunk_idx=0
            )
            
            # Add metadata from chunks
            avg_retrieval_score = sum(c.get('score', 0.5) for c in chunks) / len(chunks)
            for rule in rules:
                rule.source_reference.confidence_score = (
                    rule.source_reference.confidence_score * 0.7 + 
                    avg_retrieval_score * 0.3
                )
                rule.notes = f"Extracted from batch of {len(chunks)} chunks"
            
            logger.info(f"Extracted {len(rules)} rules from batch")
            return rules
            
        except Exception as e:
            logger.warning(f"Batch LLM extraction failed, falling back to pattern-based: {e}")
            # Fallback to pattern-based for all chunks
            all_rules = []
            for chunk_data in chunks:
                rules = self._pattern_based_extraction_from_chunk(
                    chunk_data['text'],
                    chunk_data,
                    chunk_data.get('score', 0.5)
                )
                all_rules.extend(rules)
            return all_rules
    
    def _build_batch_extraction_prompt(self, combined_text: str) -> str:
        """
        Build extraction prompt for batch of chunks.
        
        Args:
            combined_text: Combined text from multiple chunks
            
        Returns:
            Extraction prompt
        """
        track_descriptions = "\n".join([
            f"- {track.name_ar} ({track.name_en}): {track.definition_ar}"
            for track in self.tracks.values()
        ])
        
        prompt = f"""أنت محلل امتثال مالي متخصص في استخراج القواعد والشروط من الوثائق الرسمية.

المسارات المالية المحددة:
{track_descriptions}

مهمتك:
1. استخرج جميع القواعد والشروط والمتطلبات من المقاطع التالية
2. لكل قاعدة، حدد:
   - نص القاعدة بالعربية
   - المسار المالي المرتبط: contracts, salaries, أو invoices
   - مستوى الثقة في التصنيف (0-1)

المقاطع المسترجعة:
{combined_text[:8000]}

قم بإرجاع النتيجة بصيغة JSON فقط بدون أي نص إضافي:
{{
    "rules": [
        {{
            "text": "نص القاعدة",
            "track": "contracts|salaries|invoices|unknown",
            "confidence": 0.9,
            "notes": "ملاحظات"
        }}
    ]
}}"""
        
        return prompt
    
    def _extract_from_retrieved_chunk(
        self,
        chunk_text: str,
        chunk_metadata: Dict,
        retrieval_score: float,
        query: str
    ) -> List[ExtractedRule]:
        """
        DEPRECATED: Use _extract_from_chunk_batch instead for better performance.
        Extract rules from a single retrieved chunk.
        
        Args:
            chunk_text: Text of the retrieved chunk
            chunk_metadata: Metadata about the chunk
            retrieval_score: Relevance score from retrieval
            query: The query that retrieved this chunk
            
        Returns:
            List of extracted rules
        """
        logger.warning("Using single-chunk extraction (slow). Consider using batch mode.")
        
        # Use batch extraction with single chunk
        return self._extract_from_chunk_batch(
            chunks=[chunk_metadata],
            document_id=chunk_metadata.get('document_id'),
            document_name=chunk_metadata.get('document_name')
        )
    
    def _build_rag_extraction_prompt(self, chunk_text: str, query: str) -> str:
        """
        Build extraction prompt for RAG approach.
        
        Args:
            chunk_text: Retrieved chunk text
            query: The query that retrieved this chunk
            
        Returns:
            Extraction prompt
        """
        track_descriptions = "\n".join([
            f"- {track.name_ar} ({track.name_en}): {track.definition_ar}"
            for track in self.tracks.values()
        ])
        
        prompt = f"""أنت محلل امتثال مالي متخصص في استخراج القواعد والشروط من الوثائق الرسمية.

السياق: تم استرجاع هذا النص بناءً على الاستعلام التالي:
"{query}"

المسارات المالية المحددة:
{track_descriptions}

مهمتك:
1. استخرج جميع القواعد والشروط والمتطلبات من النص المسترجع التالي
2. ركز على القواعد المرتبطة بالاستعلام أعلاه
3. لكل قاعدة، حدد:
   - نص القاعدة بالعربية
   - المسار المالي المرتبط (إن وجد): العقود، الرواتب، أو الفواتير
   - مستوى الثقة في التصنيف (0-1)

النص المسترجع:
{chunk_text}

قم بإرجاع النتيجة بصيغة JSON كالتالي:
{{
    "rules": [
        {{
            "text": "نص القاعدة",
            "track": "contracts|salaries|invoices|unknown",
            "confidence": 0.0-1.0,
            "notes": "ملاحظات إضافية"
        }}
    ]
}}

JSON:"""
        
        return prompt
    
    def _pattern_based_extraction_from_chunk(
        self,
        chunk_text: str,
        chunk_metadata: Dict,
        retrieval_score: float
    ) -> List[ExtractedRule]:
        """
        Fallback pattern-based extraction from retrieved chunk.
        
        Args:
            chunk_text: Chunk text
            chunk_metadata: Chunk metadata
            retrieval_score: Retrieval score
            
        Returns:
            List of extracted rules
        """
        rules = []
        
        # Patterns that typically indicate rules
        patterns = [
            r'يجب\s+[^.]*[.]',
            r'لا\s+يجوز\s+[^.]*[.]',
            r'يشترط\s+[^.]*[.]',
            r'التحقق\s+من\s+[^.]*[.]',
            r'على\s+[^.]*\s+أن\s+[^.]*[.]',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, chunk_text, re.UNICODE)
            
            for idx, match in enumerate(matches):
                rule_text = match.group().strip()
                
                if len(rule_text) > 20:
                    rule = ExtractedRule(
                        rule_id=f"{chunk_metadata.get('document_id', 'unknown')}_chunk{chunk_metadata.get('chunk_index', 0)}_pattern{idx}",
                        text_ar=rule_text,
                        source_reference=SourceReference(
                            document_name=chunk_metadata.get('document_name', 'Unknown'),
                            document_url=chunk_metadata.get('metadata', {}).get('url'),
                            section=f"Chunk {chunk_metadata.get('chunk_index', 0)}",
                            paragraph=rule_text[:100],
                            confidence_score=retrieval_score * 0.5  # Lower confidence for pattern-based
                        ),
                        status=RuleStatus.REQUIRES_REVIEW
                    )
                    rules.append(rule)
        
        return rules
    
    def extract_rules_from_document(self, document: Document) -> List[ExtractedRule]:
        """
        Extract rules from a document (legacy method).
        Kept for backwards compatibility but not using RAG.
        
        Args:
            document: Document to extract rules from
            
        Returns:
            List of extracted rules
        """
        logger.info(f"Extracting rules from document (legacy mode): {document.name}")
        
        if not document.content:
            logger.warning(f"Document {document.name} has no content")
            return []
        
        # Split document into chunks for processing
        chunks = self._chunk_document(document.content)
        
        all_rules = []
        for chunk_idx, chunk in enumerate(chunks):
            logger.info(f"Processing chunk {chunk_idx + 1}/{len(chunks)}")
            
            # Extract rules from chunk
            chunk_rules = self._extract_rules_from_chunk(
                chunk, 
                document,
                chunk_idx
            )
            all_rules.extend(chunk_rules)
        
        logger.info(f"Extracted {len(all_rules)} rules from {document.name}")
        return all_rules
    
    def _chunk_document(self, content: str, chunk_size: int = 2000) -> List[str]:
        """
        Split document into processable chunks.
        
        Args:
            content: Document content
            chunk_size: Approximate chunk size in characters
            
        Returns:
            List of text chunks
        """
        # Split by paragraphs first
        paragraphs = content.split('\n\n')
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for para in paragraphs:
            para_size = len(para)
            
            if current_size + para_size > chunk_size and current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = [para]
                current_size = para_size
            else:
                current_chunk.append(para)
                current_size += para_size
        
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
        
        return chunks
    
    def _extract_rules_from_chunk(
        self, 
        chunk: str, 
        document: Document,
        chunk_idx: int
    ) -> List[ExtractedRule]:
        """Extract rules from a text chunk using LLM."""
        
        # Build prompt for rule extraction
        prompt = self._build_extraction_prompt(chunk)
        
        try:
            # Execute LLM
            response = self.client.execute_llm(prompt, max_tokens=2000)
            
            # Parse response
            rules = self._parse_extraction_response(response, document, chunk_idx)
            
            return rules
            
        except Exception as e:
            logger.error(f"Failed to extract rules from chunk {chunk_idx}: {e}")
            
            # Fallback to pattern-based extraction
            return self._pattern_based_extraction(chunk, document, chunk_idx)
    
    def _build_extraction_prompt(self, text: str) -> str:
        """Build prompt for rule extraction."""
        
        track_descriptions = "\n".join([
            f"- {track.name_ar} ({track.name_en}): {track.definition_ar}"
            for track in self.tracks.values()
        ])
        
        prompt = f"""أنت محلل امتثال مالي متخصص في استخراج القواعد والشروط من الوثائق الرسمية.

المسارات المالية المحددة:
{track_descriptions}

مهمتك:
1. استخرج جميع القواعد والشروط والمتطلبات من النص التالي
2. لكل قاعدة، حدد:
   - نص القاعدة بالعربية
   - المسار المالي المرتبط (إن وجد): العقود، الرواتب، أو الفواتير
   - مستوى الثقة في التصنيف (0-1)
3. ركز على القواعد التي تتعلق بالتحقق والمطابقة والشروط

النص:
{text}

قم بإرجاع النتيجة بصيغة JSON كالتالي:
{{
    "rules": [
        {{
            "text": "نص القاعدة",
            "track": "contracts|salaries|invoices|unknown",
            "confidence": 0.0-1.0,
            "notes": "ملاحظات إضافية"
        }}
    ]
}}

JSON:"""
        
        return prompt
    
    def _parse_extraction_response(
        self, 
        response: str, 
        document_id: str = None,
        document_name: str = None,
        chunk_idx: int = 0,
        document: Document = None
    ) -> List[ExtractedRule]:
        """Parse LLM response into ExtractedRule objects."""
        
        # Handle legacy calls with document parameter
        if document and not document_id:
            document_id = document.document_id
            document_name = document.name
        
        rules = []
        
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                
                for idx, rule_data in enumerate(data.get('rules', [])):
                    rule = ExtractedRule(
                        rule_id=f"{document_id}_chunk{chunk_idx}_rule{idx}",
                        text_ar=rule_data.get('text', ''),
                        source_reference=SourceReference(
                            document_name=document_name or 'Unknown',
                            document_url=document.url if document else None,
                            section=f"Chunk {chunk_idx}",
                            confidence_score=rule_data.get('confidence', 0.5)
                        ),
                        status=RuleStatus.EXTRACTED,
                        track_id=rule_data.get('track') if rule_data.get('track') != 'unknown' else None,
                        mapping_confidence=rule_data.get('confidence', 0.5),
                        notes=rule_data.get('notes')
                    )
                    rules.append(rule)
        
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {e}")
        
        return rules
    
    def _pattern_based_extraction(
        self, 
        text: str, 
        document: Document,
        chunk_idx: int
    ) -> List[ExtractedRule]:
        """
        Fallback pattern-based rule extraction.
        Looks for common patterns in Arabic regulatory text.
        """
        rules = []
        
        # Patterns that typically indicate rules
        patterns = [
            r'يجب\s+[^.]*[.]',  # "must" statements
            r'لا\s+يجوز\s+[^.]*[.]',  # "not permitted" statements
            r'يشترط\s+[^.]*[.]',  # "required" statements
            r'التحقق\s+من\s+[^.]*[.]',  # "verify that" statements
            r'على\s+[^.]*\s+أن\s+[^.]*[.]',  # "should" statements
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.UNICODE)
            
            for idx, match in enumerate(matches):
                rule_text = match.group().strip()
                
                if len(rule_text) > 20:  # Minimum meaningful length
                    rule = ExtractedRule(
                        rule_id=f"{document.document_id}_chunk{chunk_idx}_pattern{idx}",
                        text_ar=rule_text,
                        source_reference=SourceReference(
                            document_name=document.name,
                            document_url=document.url,
                            section=f"Chunk {chunk_idx}",
                            paragraph=rule_text[:100],
                            confidence_score=0.3  # Lower confidence for pattern-based
                        ),
                        status=RuleStatus.REQUIRES_REVIEW
                    )
                    rules.append(rule)
        
        return rules


class RuleMapper:
    """Maps extracted rules to financial tracks."""
    
    def __init__(self, client: AIXplainClient):
        self.client = client
        self.tracks = TracksRepository.get_all_tracks()
    
    def map_rules_to_tracks(self, rules: List[ExtractedRule]) -> List[ExtractedRule]:
        """
        Map extracted rules to appropriate financial tracks.
        
        Args:
            rules: List of extracted rules
            
        Returns:
            Rules with updated track mappings
        """
        logger.info(f"Mapping {len(rules)} rules to tracks")
        
        for rule in rules:
            if not rule.track_id or rule.mapping_confidence < 0.7:
                # Need to map or re-map
                track_id, confidence = self._map_rule_to_track(rule)
                rule.track_id = track_id
                rule.mapping_confidence = confidence
                
                if confidence < 0.5:
                    rule.status = RuleStatus.REQUIRES_REVIEW
                    rule.notes = "Low confidence mapping - requires review"
                else:
                    rule.status = RuleStatus.MAPPED
        
        logger.info("Rule mapping completed")
        return rules
    
    def _map_rule_to_track(self, rule: ExtractedRule) -> Tuple[Optional[str], float]:
        """
        Map a single rule to a track.
        
        Returns:
            Tuple of (track_id, confidence_score)
        """
        # Build track context
        track_context = self._build_track_context()
        
        # Build mapping prompt
        prompt = f"""أنت محلل مالي متخصص في تصنيف القواعد المالية.

المسارات المالية المتاحة:
{track_context}

القاعدة المراد تصنيفها:
"{rule.text_ar}"

حدد المسار المالي الأنسب لهذه القاعدة ومستوى ثقتك في التصنيف.

أعد الإجابة بصيغة JSON:
{{
    "track_id": "contracts|salaries|invoices|none",
    "confidence": 0.0-1.0,
    "reasoning": "سبب التصنيف"
}}

JSON:"""
        
        try:
            response = self.client.execute_llm(prompt, max_tokens=500)
            
            # Parse response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                track_id = data.get('track_id')
                confidence = data.get('confidence', 0.5)
                
                if track_id == 'none':
                    track_id = None
                
                return track_id, confidence
        
        except Exception as e:
            logger.error(f"Failed to map rule: {e}")
        
        # Fallback to keyword-based mapping
        return self._keyword_based_mapping(rule.text_ar)
    
    def _build_track_context(self) -> str:
        """Build context description of all tracks."""
        lines = []
        for track in self.tracks.values():
            lines.append(f"- {track.track_id}: {track.name_ar} - {track.definition_ar}")
        return "\n".join(lines)
    
    def _keyword_based_mapping(self, rule_text: str) -> Tuple[Optional[str], float]:
        """Fallback keyword-based track mapping."""
        
        # Define keywords for each track
        track_keywords = {
            'contracts': ['عقد', 'مستخلص', 'ترسية', 'منافسات', 'مشتريات', 'إنشاءات', 'مقاول'],
            'salaries': ['راتب', 'موظف', 'حسميات', 'بدل', 'عمل إضافي', 'درجة وظيفية'],
            'invoices': ['فاتورة', 'كهرباء', 'مياه', 'جوال', 'خدمات', 'استهلاكية', 'تسعيرة']
        }
        
        # Count keyword matches
        scores = {}
        for track_id, keywords in track_keywords.items():
            score = sum(1 for keyword in keywords if keyword in rule_text)
            if score > 0:
                scores[track_id] = score
        
        if not scores:
            return None, 0.0
        
        # Get best match
        best_track = max(scores, key=scores.get)
        max_score = scores[best_track]
        total_keywords = len(track_keywords[best_track])
        
        confidence = min(max_score / total_keywords, 0.6)  # Cap at 0.6 for keyword-based
        
        return best_track, confidence
