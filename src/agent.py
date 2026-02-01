"""
Main orchestrator for the Financial Rules Extraction Agent with RAG support.
"""
import time
from typing import List, Optional, Dict, Any
from datetime import datetime
from loguru import logger

from src.models import Document, ExtractedRule, ExtractionResult, DocumentType, DocumentStatus
from src.parser import DocumentParser
from src.aixplain_client import AIXplainClient, IndexManager
from src.rule_extractor import RuleExtractor, RuleMapper
from src.gap_analyzer import GapAnalyzer, CoverageAnalyzer
from src.integrations import NotificationManager
from src.config import config


class FinancialRulesAgent:
    """
    Main agent for extracting and analyzing financial rules from documents.
    Now with TRUE RAG (Retrieval-Augmented Generation) support.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Financial Rules Extraction Agent.
        
        Args:
            api_key: aiXplain API key (optional, defaults to config)
        """
        logger.info("Initializing Financial Rules Extraction Agent with RAG capabilities")
        
        # Initialize components
        self.client = AIXplainClient(api_key)
        self.parser = DocumentParser()
        self.index_manager = IndexManager(self.client)
        self.rule_extractor = RuleExtractor(self.client)
        self.rule_mapper = RuleMapper(self.client)
        self.gap_analyzer = GapAnalyzer()
        self.coverage_analyzer = CoverageAnalyzer()
        
        # Initialize notification manager
        self.notification_manager = NotificationManager()
        if self.notification_manager.is_configured():
            logger.info(f"Notifications enabled for: {', '.join(self.notification_manager.get_configured_channels())}")
        
        # Initialize models (optional - system works with fallback methods)
        try:
            self.client.initialize_models()
        except Exception as e:
            logger.warning(f"Model initialization had issues: {e}")
            logger.info("System will use pattern-based extraction as fallback")
    
    def _generate_track_queries(self) -> Dict[str, List[str]]:
        """
        Generate search queries for each financial track.
        Used for RAG-based extraction.
        
        OPTIMIZED: Using 1 comprehensive query per track instead of 4
        to reduce LLM calls while maintaining aiXplain usage.
        
        Returns:
            Dictionary mapping track IDs to their queries
        """
        return {
            'contracts': [
                'ما هي جميع القواعد والشروط المتعلقة بالعقود والمستخلصات والترسية والمنافسات؟'
            ],
            'salaries': [
                'ما هي جميع القواعد والشروط المتعلقة بالرواتب والحسميات والبدلات والدرجات الوظيفية؟'
            ],
            'invoices': [
                'ما هي جميع القواعد والشروط المتعلقة بالفواتير والخدمات الاستهلاكية والتسعيرة الحكومية؟'
            ]
        }
    
    def _get_all_queries(self) -> List[str]:
        """Get all queries for all tracks."""
        all_queries = []
        for queries in self._generate_track_queries().values():
            all_queries.extend(queries)
        return all_queries
    
    def process_document(
        self, 
        name: str,
        url: Optional[str] = None,
        file_path: Optional[str] = None,
        document_type: Optional[DocumentType] = None,
        use_rag: bool = None
    ) -> ExtractionResult:
        """
        Process a document and extract financial rules using RAG or legacy method.
        
        Args:
            name: Document name
            url: Document URL (for PDFs or web pages)
            file_path: Local file path
            document_type: Type of document (auto-detected if not provided)
            use_rag: Whether to use RAG approach (defaults to config)
            
        Returns:
            ExtractionResult with extracted rules and gap analysis
        """
        start_time = time.time()
        
        # Determine if using RAG
        if use_rag is None:
            use_rag = config.app.use_rag
        
        logger.info(f"Processing document: {name} (RAG={'enabled' if use_rag else 'disabled'})")
        
        # Create document object
        if not document_type:
            document_type = self._detect_document_type(url, file_path)
        
        document = Document(
            document_id=f"doc_{int(datetime.now().timestamp())}",
            name=name,
            url=url,
            file_path=file_path,
            document_type=document_type
        )
        
        # Step 1: Parse document
        logger.info("Step 1: Parsing document")
        document = self.parser.parse(document)
        
        if document.status == DocumentStatus.FAILED:
            logger.error(f"Failed to parse document: {name}")
            result = ExtractionResult(
                document_id=document.document_id,
                extracted_rules=[],
                gaps=[],
                statistics=self._get_empty_statistics('Document parsing failed'),
                processing_time_seconds=time.time() - start_time
            )
            # Send notification even on failure
            if self.notification_manager.is_configured():
                self.notification_manager.notify_extraction_complete(result, name)
            return result
        
        # Step 2: Index document for RAG
        if use_rag:
            logger.info("Step 2: Indexing document with vector storage (RAG mode)")
            try:
                index_result = self.index_manager.index_single_document(
                    document,
                    use_chunking=True
                )
                logger.info(f"Indexed {index_result.get('num_chunks', 0)} chunks")
            except Exception as e:
                logger.warning(f"Failed to index document: {e}")
                logger.info("Falling back to non-RAG extraction")
                use_rag = False
        
        # Step 3: Extract rules
        if use_rag and self.client.indexed_chunks:
            logger.info("Step 3: Extracting rules using RAG (retrieval-based)")
            # Generate queries for all tracks
            all_queries = self._get_all_queries()
            extracted_rules = self.rule_extractor.extract_rules_with_retrieval(
                document_id=document.document_id,
                queries=all_queries,
                document_name=document.name
            )
        else:
            logger.info("Step 3: Extracting rules using legacy method (full document)")
            extracted_rules = self.rule_extractor.extract_rules_from_document(document)
        
        # Step 4: Map rules to tracks
        logger.info("Step 4: Mapping rules to financial tracks")
        mapped_rules = self.rule_mapper.map_rules_to_tracks(extracted_rules)
        
        # Step 5: Analyze gaps
        logger.info("Step 5: Analyzing gaps in rule coverage")
        gaps = self.gap_analyzer.analyze_gaps(mapped_rules)
        
        # Step 6: Calculate statistics
        logger.info("Step 6: Calculating statistics")
        statistics = self._calculate_statistics(mapped_rules, gaps)
        statistics['rag_enabled'] = use_rag
        statistics['num_chunks_indexed'] = len(self.client.indexed_chunks)
        
        processing_time = time.time() - start_time
        
        result = ExtractionResult(
            document_id=document.document_id,
            extracted_rules=mapped_rules,
            gaps=gaps,
            statistics=statistics,
            processing_time_seconds=processing_time
        )
        
        logger.info(f"Processing completed in {processing_time:.2f} seconds")
        logger.info(f"Extracted {len(mapped_rules)} rules, identified {len(gaps)} gaps")
        
        # Send notifications
        if self.notification_manager.is_configured():
            try:
                self.notification_manager.notify_extraction_complete(result, name)
            except Exception as e:
                logger.warning(f"Failed to send notifications: {e}")
        
        return result
    
    def process_multiple_documents(
        self, 
        documents: List[Dict[str, str]]
    ) -> List[ExtractionResult]:
        """
        Process multiple documents.
        
        Args:
            documents: List of document specifications (name, url, file_path, type)
            
        Returns:
            List of extraction results
        """
        logger.info(f"Processing {len(documents)} documents")
        
        results = []
        for doc_spec in documents:
            try:
                result = self.process_document(
                    name=doc_spec['name'],
                    url=doc_spec.get('url'),
                    file_path=doc_spec.get('file_path'),
                    document_type=doc_spec.get('type')
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to process document {doc_spec['name']}: {e}")
        
        return results
    
    def generate_comprehensive_report(
        self, 
        results: List[ExtractionResult]
    ) -> dict:
        """
        Generate a comprehensive report from multiple extraction results.
        
        Args:
            results: List of extraction results
            
        Returns:
            Comprehensive report dictionary
        """
        logger.info("Generating comprehensive report")
        
        # Aggregate all rules and gaps
        all_rules = []
        all_gaps = []
        
        for result in results:
            all_rules.extend(result.extracted_rules)
            all_gaps.extend(result.gaps)
        
        # Generate gap report
        gap_report = self.gap_analyzer.generate_gap_report(all_gaps)
        
        # Generate coverage analysis
        coverage_report = self.coverage_analyzer.analyze_coverage(all_rules, all_gaps)
        
        # Aggregate statistics
        total_processing_time = sum(r.processing_time_seconds for r in results)
        
        report = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'num_documents_processed': len(results),
                'total_processing_time_seconds': round(total_processing_time, 2)
            },
            'summary': {
                'total_rules_extracted': len(all_rules),
                'total_gaps_identified': len(all_gaps),
                'rules_by_track': self._count_rules_by_track(all_rules),
                'gaps_by_severity': gap_report['summary']['by_severity']
            },
            'gap_analysis': gap_report,
            'coverage_analysis': coverage_report,
            'document_results': [
                {
                    'document_id': r.document_id,
                    'num_rules': len(r.extracted_rules),
                    'num_gaps': len(r.gaps),
                    'processing_time': round(r.processing_time_seconds, 2)
                }
                for r in results
            ]
        }
        
        return report
    
    def _detect_document_type(
        self, 
        url: Optional[str],
        file_path: Optional[str]
    ) -> DocumentType:
        """Auto-detect document type."""
        
        if url:
            if url.lower().endswith('.pdf'):
                return DocumentType.PDF
            else:
                return DocumentType.WEB_PAGE
        
        elif file_path:
            if file_path.lower().endswith('.pdf'):
                return DocumentType.PDF
            else:
                return DocumentType.TEXT
        
        return DocumentType.TEXT
    
    def _calculate_statistics(
        self, 
        rules: List[ExtractedRule],
        gaps: List
    ) -> dict:
        """Calculate statistics for extraction result."""
        
        return {
            'total_rules': len(rules),
            'rules_by_status': {
                'extracted': len([r for r in rules if r.status.value == 'extracted']),
                'mapped': len([r for r in rules if r.status.value == 'mapped']),
                'requires_review': len([r for r in rules if r.status.value == 'requires_review'])
            },
            'rules_by_track': self._count_rules_by_track(rules),
            'average_mapping_confidence': round(
                sum(r.mapping_confidence for r in rules) / len(rules), 2
            ) if rules else 0.0,
            'total_gaps': len(gaps),
            'gaps_by_type': {
                'missing': len([g for g in gaps if g.gap_type == 'missing']),
                'partial': len([g for g in gaps if g.gap_type == 'partial']),
                'conflicting': len([g for g in gaps if g.gap_type == 'conflicting'])
            }
        }
    
    def _get_empty_statistics(self, error_message: Optional[str] = None) -> dict:
        """Get empty statistics structure (used when processing fails)."""
        stats = {
            'total_rules': 0,
            'rules_by_status': {
                'extracted': 0,
                'mapped': 0,
                'requires_review': 0
            },
            'rules_by_track': {
                'contracts': 0,
                'salaries': 0,
                'invoices': 0,
                'unmapped': 0
            },
            'average_mapping_confidence': 0.0,
            'total_gaps': 0,
            'gaps_by_type': {
                'missing': 0,
                'partial': 0,
                'conflicting': 0
            }
        }
        if error_message:
            stats['error'] = error_message
        return stats
    
    def _count_rules_by_track(self, rules: List[ExtractedRule]) -> dict:
        """Count rules by track."""
        
        counts = {
            'contracts': 0,
            'salaries': 0,
            'invoices': 0,
            'unmapped': 0
        }
        
        for rule in rules:
            if rule.track_id:
                counts[rule.track_id] = counts.get(rule.track_id, 0) + 1
            else:
                counts['unmapped'] += 1
        
        return counts
