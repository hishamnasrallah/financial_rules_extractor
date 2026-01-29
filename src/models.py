"""
Data models for the Financial Rules Extraction Agent.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    """Types of documents that can be processed."""
    PDF = "pdf"
    WEB_PAGE = "web_page"
    TEXT = "text"


class DocumentStatus(str, Enum):
    """Status of document processing."""
    PENDING = "pending"
    PROCESSING = "processing"
    INDEXED = "indexed"
    FAILED = "failed"


class RuleStatus(str, Enum):
    """Status of extracted rules."""
    EXTRACTED = "extracted"
    MAPPED = "mapped"
    REQUIRES_REVIEW = "requires_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class SourceReference(BaseModel):
    """Reference to the source of a rule."""
    document_name: str = Field(..., description="Name of the source document")
    document_url: Optional[str] = Field(None, description="URL of the source document")
    page_number: Optional[int] = Field(None, description="Page number (for PDFs)")
    section: Optional[str] = Field(None, description="Section identifier")
    paragraph: Optional[str] = Field(None, description="Paragraph text or identifier")
    confidence_score: float = Field(default=0.0, description="Confidence score (0-1)")


class ExtractedRule(BaseModel):
    """Represents a rule extracted from a document."""
    rule_id: str = Field(..., description="Unique identifier for the rule")
    text_ar: str = Field(..., description="Rule text in Arabic")
    text_en: Optional[str] = Field(None, description="Rule text in English (if translated)")
    source_reference: SourceReference = Field(..., description="Source reference")
    status: RuleStatus = Field(default=RuleStatus.EXTRACTED, description="Rule status")
    track_id: Optional[str] = Field(None, description="Mapped track ID")
    mapping_confidence: float = Field(default=0.0, description="Confidence of track mapping (0-1)")
    extracted_at: datetime = Field(default_factory=datetime.now, description="Extraction timestamp")
    notes: Optional[str] = Field(None, description="Additional notes or flags")


class GapAnalysis(BaseModel):
    """Represents a gap in rule coverage."""
    gap_id: str = Field(..., description="Unique identifier for the gap")
    track_id: str = Field(..., description="Track where gap exists")
    extracted_rule: ExtractedRule = Field(..., description="The extracted rule not covered")
    similar_existing_rules: List[str] = Field(default_factory=list, description="Similar existing rule IDs")
    gap_type: str = Field(..., description="Type of gap: 'missing', 'partial', 'conflicting'")
    severity: str = Field(default="medium", description="Severity: 'low', 'medium', 'high', 'critical'")
    recommendation: str = Field(..., description="Recommendation for addressing the gap")


class Document(BaseModel):
    """Represents a document to be processed."""
    document_id: str = Field(..., description="Unique identifier for the document")
    name: str = Field(..., description="Document name")
    url: Optional[str] = Field(None, description="Document URL")
    file_path: Optional[str] = Field(None, description="Local file path")
    document_type: DocumentType = Field(..., description="Type of document")
    status: DocumentStatus = Field(default=DocumentStatus.PENDING, description="Processing status")
    content: Optional[str] = Field(None, description="Extracted text content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    processed_at: Optional[datetime] = Field(None, description="Processing timestamp")


class ExtractionResult(BaseModel):
    """Result of the extraction process."""
    document_id: str = Field(..., description="Document ID")
    extracted_rules: List[ExtractedRule] = Field(default_factory=list, description="Extracted rules")
    gaps: List[GapAnalysis] = Field(default_factory=list, description="Identified gaps")
    statistics: Dict[str, Any] = Field(default_factory=dict, description="Extraction statistics")
    processing_time_seconds: float = Field(..., description="Processing time in seconds")
    created_at: datetime = Field(default_factory=datetime.now, description="Result timestamp")


class ValidationResult(BaseModel):
    """Result of HITL validation."""
    rule_id: str = Field(..., description="Rule ID being validated")
    validator_name: Optional[str] = Field(None, description="Name of the validator")
    validated_at: datetime = Field(default_factory=datetime.now, description="Validation timestamp")
    decision: str = Field(..., description="approve, reject, or modify")
    comments: Optional[str] = Field(None, description="Validator comments")
    modified_text: Optional[str] = Field(None, description="Modified rule text if applicable")
    modified_track: Optional[str] = Field(None, description="Modified track mapping if applicable")
