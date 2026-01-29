"""
Test utilities for the Financial Rules Extraction Agent.
This module provides helpers for testing the agent without making real API calls.
"""
from typing import List, Optional
from datetime import datetime

from src.models import (
    Document, DocumentType, DocumentStatus,
    ExtractedRule, SourceReference, RuleStatus,
    ExtractionResult, GapAnalysis
)


class MockAIXplainClient:
    """Mock aiXplain client for testing without API calls."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or "mock_api_key"
        self.search_model = None
        self.llm_model = None
    
    def initialize_models(self):
        """Mock model initialization."""
        self.search_model = "mock_search_model"
        self.llm_model = "mock_llm_model"
    
    def create_index(self, documents: List[Document]) -> dict:
        """Mock index creation."""
        return {
            "status": "success",
            "num_documents": len(documents),
            "index_name": "mock_index"
        }
    
    def search(self, query: str, num_results: int = 10) -> List[dict]:
        """Mock search."""
        return [
            {
                "id": f"doc_{i}",
                "text": f"Mock result {i} for query: {query}",
                "score": 0.9 - (i * 0.1)
            }
            for i in range(min(num_results, 3))
        ]
    
    def execute_llm(self, prompt: str, max_tokens: int = 2000) -> str:
        """Mock LLM execution."""
        # Return a mock JSON response
        return """
{
    "rules": [
        {
            "text": "التحقق من أن مجموع الحسميات لا يتجاوز ثلث الراتب الأساسي",
            "track": "salaries",
            "confidence": 0.92,
            "notes": "Mock extracted rule"
        },
        {
            "text": "التحقق من مطابقة المبالغ المراد صرفها مع الفواتير",
            "track": "invoices",
            "confidence": 0.88,
            "notes": "Mock extracted rule"
        }
    ]
}
        """


def create_mock_document(
    doc_id: str = "test_doc",
    name: str = "Test Document",
    content: str = "Mock document content"
) -> Document:
    """Create a mock document for testing."""
    return Document(
        document_id=doc_id,
        name=name,
        document_type=DocumentType.TEXT,
        status=DocumentStatus.INDEXED,
        content=content,
        metadata={"test": True}
    )


def create_mock_extracted_rule(
    rule_id: str = "test_rule",
    text_ar: str = "قاعدة اختبارية",
    track_id: str = "salaries"
) -> ExtractedRule:
    """Create a mock extracted rule for testing."""
    return ExtractedRule(
        rule_id=rule_id,
        text_ar=text_ar,
        source_reference=SourceReference(
            document_name="Test Document",
            confidence_score=0.9
        ),
        status=RuleStatus.MAPPED,
        track_id=track_id,
        mapping_confidence=0.85
    )


def create_mock_extraction_result(
    num_rules: int = 5,
    num_gaps: int = 2
) -> ExtractionResult:
    """Create a mock extraction result for testing."""
    rules = [
        create_mock_extracted_rule(
            rule_id=f"rule_{i}",
            text_ar=f"قاعدة رقم {i}",
            track_id=["salaries", "contracts", "invoices"][i % 3]
        )
        for i in range(num_rules)
    ]
    
    gaps = [
        GapAnalysis(
            gap_id=f"gap_{i}",
            track_id="contracts",
            extracted_rule=rules[i],
            gap_type="missing",
            severity="high",
            recommendation=f"Implement new rule {i}"
        )
        for i in range(num_gaps)
    ]
    
    return ExtractionResult(
        document_id="test_doc",
        extracted_rules=rules,
        gaps=gaps,
        statistics={
            "total_rules": num_rules,
            "total_gaps": num_gaps,
            "average_mapping_confidence": 0.85
        },
        processing_time_seconds=1.5
    )


def test_basic_extraction():
    """Test basic extraction workflow."""
    print("Testing basic extraction...")
    
    # Create mock document
    doc = create_mock_document()
    assert doc.document_id == "test_doc"
    assert doc.status == DocumentStatus.INDEXED
    
    # Create mock rules
    rules = [create_mock_extracted_rule(f"rule_{i}") for i in range(3)]
    assert len(rules) == 3
    assert all(r.status == RuleStatus.MAPPED for r in rules)
    
    # Create mock result
    result = create_mock_extraction_result(num_rules=5, num_gaps=2)
    assert len(result.extracted_rules) == 5
    assert len(result.gaps) == 2
    
    print("✓ Basic extraction test passed")


def test_track_mapping():
    """Test track mapping logic."""
    print("Testing track mapping...")
    
    from src.tracks import TracksRepository
    
    # Get all tracks
    tracks = TracksRepository.get_all_tracks()
    assert len(tracks) == 3
    assert "contracts" in tracks
    assert "salaries" in tracks
    assert "invoices" in tracks
    
    # Check track structure
    for track_id, track in tracks.items():
        assert track.track_id == track_id
        assert track.name_ar
        assert track.name_en
        assert len(track.current_rules) > 0
    
    print("✓ Track mapping test passed")


def test_gap_analysis():
    """Test gap analysis logic."""
    print("Testing gap analysis...")
    
    from src.gap_analyzer import GapAnalyzer
    
    analyzer = GapAnalyzer()
    
    # Create mock rules
    rules = [
        create_mock_extracted_rule(f"rule_{i}", track_id="salaries")
        for i in range(5)
    ]
    
    # Analyze gaps
    gaps = analyzer.analyze_gaps(rules)
    
    # Check results
    assert isinstance(gaps, list)
    
    print(f"✓ Gap analysis test passed (found {len(gaps)} gaps)")


def test_validation_workflow():
    """Test HITL validation workflow."""
    print("Testing validation workflow...")
    
    from src.validation import ValidationManager
    from pathlib import Path
    import tempfile
    
    # Create temp directory for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        validator = ValidationManager(storage_path=Path(tmpdir))
        
        # Create mock rules
        rules = [create_mock_extracted_rule(f"rule_{i}") for i in range(3)]
        
        # Submit for review
        submission = validator.submit_for_review(rules, reason="Test review")
        assert "submission_id" in submission
        assert submission["num_rules"] == 3
        
        # Validate a rule
        validation = validator.validate_rule(
            rule_id="rule_0",
            decision="approve",
            validator_name="Test User"
        )
        assert validation.decision == "approve"
        assert validation.validator_name == "Test User"
        
        # Get history
        history = validator.get_validation_history()
        assert len(history) == 1
        
        print("✓ Validation workflow test passed")


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("Running Financial Rules Extraction Agent Tests")
    print("=" * 60)
    print()
    
    try:
        test_basic_extraction()
        test_track_mapping()
        test_gap_analysis()
        test_validation_workflow()
        
        print()
        print("=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)
        
    except Exception as e:
        print()
        print("=" * 60)
        print(f"✗ Test failed: {str(e)}")
        print("=" * 60)
        raise


if __name__ == "__main__":
    run_all_tests()
