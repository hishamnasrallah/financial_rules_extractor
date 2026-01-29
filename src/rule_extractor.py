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


class RuleExtractor:
    """Extracts rules from documents using AI models."""
    
    def __init__(self, client: AIXplainClient):
        self.client = client
        self.tracks = TracksRepository.get_all_tracks()
    
    def extract_rules_from_document(self, document: Document) -> List[ExtractedRule]:
        """
        Extract rules from a document.
        
        Args:
            document: Document to extract rules from
            
        Returns:
            List of extracted rules
        """
        logger.info(f"Extracting rules from document: {document.name}")
        
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
        document: Document,
        chunk_idx: int
    ) -> List[ExtractedRule]:
        """Parse LLM response into ExtractedRule objects."""
        
        rules = []
        
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                
                for idx, rule_data in enumerate(data.get('rules', [])):
                    rule = ExtractedRule(
                        rule_id=f"{document.document_id}_chunk{chunk_idx}_rule{idx}",
                        text_ar=rule_data.get('text', ''),
                        source_reference=SourceReference(
                            document_name=document.name,
                            document_url=document.url,
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
