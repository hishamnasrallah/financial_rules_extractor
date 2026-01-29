# API Documentation

## Overview

This document provides detailed API documentation for the Financial Rules Extraction Agent.

## Core Components

### 1. FinancialRulesAgent

Main orchestrator class for the agent.

```python
from src.agent import FinancialRulesAgent

# Initialize agent
agent = FinancialRulesAgent(api_key="your_api_key")

# Process a document
result = agent.process_document(
    name="نظام الخدمة المدنية",
    url="https://example.com/doc.pdf",
    document_type=DocumentType.PDF
)

# Process multiple documents
documents = [
    {"name": "Doc 1", "url": "https://...", "type": "pdf"},
    {"name": "Doc 2", "url": "https://...", "type": "web_page"}
]
results = agent.process_multiple_documents(documents)

# Generate comprehensive report
report = agent.generate_comprehensive_report(results)
```

### 2. Document Parser

Extract text from various document formats.

```python
from src.parser import DocumentParser
from src.models import Document, DocumentType

parser = DocumentParser()

# Create document
doc = Document(
    document_id="doc_001",
    name="Test Document",
    url="https://example.com/doc.pdf",
    document_type=DocumentType.PDF
)

# Parse document
parsed_doc = parser.parse(doc)
print(parsed_doc.content)
```

### 3. Rule Extractor

Extract rules from parsed documents.

```python
from src.rule_extractor import RuleExtractor
from src.aixplain_client import AIXplainClient

client = AIXplainClient(api_key="your_api_key")
extractor = RuleExtractor(client)

# Extract rules
rules = extractor.extract_rules_from_document(document)

# Map rules to tracks
from src.rule_extractor import RuleMapper
mapper = RuleMapper(client)
mapped_rules = mapper.map_rules_to_tracks(rules)
```

### 4. Gap Analyzer

Analyze gaps in rule coverage.

```python
from src.gap_analyzer import GapAnalyzer, CoverageAnalyzer

gap_analyzer = GapAnalyzer()
coverage_analyzer = CoverageAnalyzer()

# Analyze gaps
gaps = gap_analyzer.analyze_gaps(extracted_rules)

# Generate gap report
gap_report = gap_analyzer.generate_gap_report(gaps)

# Analyze coverage
coverage_report = coverage_analyzer.analyze_coverage(
    extracted_rules,
    gaps
)
```

### 5. Validation Manager

HITL validation workflow.

```python
from src.validation import ValidationManager

validator = ValidationManager()

# Submit rules for review
submission = validator.submit_for_review(
    rules=extracted_rules,
    reason="Low confidence mappings"
)

# Validate a rule
validation = validator.validate_rule(
    rule_id="rule_001",
    decision="approve",
    validator_name="John Doe",
    comments="Looks good"
)

# Apply validations
updated_rules = validator.apply_validations(rules, [validation])
```

### 6. Audit Trail

Maintain audit logs.

```python
from src.validation import AuditTrail

audit = AuditTrail()

# Log an event
audit.log_event(
    event_type="rule_extracted",
    details={"rule_id": "rule_001", "track": "salaries"},
    user="system"
)

# Get audit log
entries = audit.get_audit_log(
    event_type="rule_extracted",
    start_date=datetime(2024, 1, 1)
)

# Generate report
report = audit.generate_audit_report()
```

## Data Models

### Document

```python
from src.models import Document, DocumentType

doc = Document(
    document_id="doc_001",
    name="Document Name",
    url="https://example.com/doc.pdf",
    document_type=DocumentType.PDF,
    status=DocumentStatus.PENDING,
    content=None,
    metadata={}
)
```

### ExtractedRule

```python
from src.models import ExtractedRule, SourceReference, RuleStatus

rule = ExtractedRule(
    rule_id="rule_001",
    text_ar="نص القاعدة بالعربية",
    source_reference=SourceReference(
        document_name="Document Name",
        document_url="https://...",
        page_number=5,
        section="Section 3",
        confidence_score=0.9
    ),
    status=RuleStatus.EXTRACTED,
    track_id="salaries",
    mapping_confidence=0.85
)
```

### GapAnalysis

```python
from src.models import GapAnalysis

gap = GapAnalysis(
    gap_id="gap_001",
    track_id="contracts",
    extracted_rule=rule,
    similar_existing_rules=["CON-001", "CON-002"],
    gap_type="missing",
    severity="high",
    recommendation="Implement new rule..."
)
```

## Configuration

### Environment Variables

```env
# Required
AIXPLAIN_API_KEY=your_api_key_here

# Optional
AIXPLAIN_EMBEDDING_MODEL_ID=
AIXPLAIN_LLM_MODEL_ID=
AIXPLAIN_SEARCH_MODEL_ID=66eae6656eb56311f2595011
AIXPLAIN_INDEX_NAME=financial_rules_index

# Application Settings
LOG_LEVEL=INFO
MAX_RETRIES=3
TIMEOUT_SECONDS=60
```

### Programmatic Configuration

```python
from src.config import config

# Access configuration
api_key = config.aixplain.api_key
log_level = config.app.log_level
data_dir = config.app.data_dir

# Validate configuration
config.validate()
```

## Error Handling

```python
from src.agent import FinancialRulesAgent

try:
    agent = FinancialRulesAgent(api_key="your_api_key")
    result = agent.process_document(
        name="Document",
        url="https://example.com/doc.pdf"
    )
except ValueError as e:
    print(f"Configuration error: {e}")
except Exception as e:
    print(f"Processing error: {e}")
```

## Best Practices

1. **Always validate input documents** before processing
2. **Use batch processing** for multiple documents
3. **Enable HITL validation** for low-confidence rules
4. **Check audit logs** regularly
5. **Monitor extraction accuracy** and adjust prompts as needed
6. **Keep API keys secure** - never commit them to version control

## Performance Optimization

```python
# Use batch processing for multiple documents
results = agent.process_multiple_documents(documents)

# Index documents once, search multiple times
index_manager.index_documents(documents)
results1 = client.search("query 1")
results2 = client.search("query 2")

# Adjust chunk size for better performance
extractor._chunk_document(content, chunk_size=1500)
```

## Troubleshooting

### Common Issues

1. **API Key Invalid**: Check `.env` file and aiXplain console
2. **Document Parsing Failed**: Verify document URL/path is accessible
3. **Low Extraction Accuracy**: Adjust prompts in `rule_extractor.py`
4. **Slow Processing**: Use smaller chunk sizes or faster models
5. **Memory Issues**: Process documents in smaller batches

### Debug Mode

```python
import logging
from loguru import logger

# Enable debug logging
logger.add("debug.log", level="DEBUG")

# Run with verbose output
agent = FinancialRulesAgent(api_key="your_api_key")
result = agent.process_document(name="Doc", url="https://...")
```
