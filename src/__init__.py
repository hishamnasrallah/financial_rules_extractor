"""
Financial Rules Extraction Agent package.
"""

__version__ = "1.0.0"
__author__ = "Financial Rules Extraction Team"
__description__ = "AI agent for extracting and analyzing financial rules from official documents"

from src.agent import FinancialRulesAgent
from src.models import (
    Document,
    DocumentType,
    ExtractedRule,
    ExtractionResult,
    GapAnalysis,
    ValidationResult
)
from src.tracks import TracksRepository

__all__ = [
    'FinancialRulesAgent',
    'Document',
    'DocumentType',
    'ExtractedRule',
    'ExtractionResult',
    'GapAnalysis',
    'ValidationResult',
    'TracksRepository'
]
