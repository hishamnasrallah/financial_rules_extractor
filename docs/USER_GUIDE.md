# User Guide

## Getting Started

This guide will help you get started with the Financial Rules Extraction Agent.

## Installation

### Step 1: System Requirements

- Python 3.8 or higher
- Windows, macOS, or Linux
- 4GB RAM minimum (8GB recommended)
- Internet connection for aiXplain API

### Step 2: Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Get aiXplain API Key

1. Visit [aiXplain Console](https://console.aixplain.com)
2. Sign up or log in
3. Navigate to Settings > API Keys
4. Create a new API key
5. Copy the key

### Step 4: Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your API key
# AIXPLAIN_API_KEY=your_api_key_here
```

## Using the Web Interface

### Launch the Application

```bash
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`

### Extract Rules from a Document

1. **Enter API Key**: In the sidebar, enter your aiXplain API key and click "Initialize Agent"

2. **Go to "Extract Rules" page**

3. **Fill in Document Information**:
   - Document Name: e.g., "نظام الخدمة المدنية"
   - Document Type: Select from dropdown or use "Auto-detect"

4. **Provide Document Source**:
   - **Option A**: Enter URL in the "URL" tab
   - **Option B**: Upload file in the "Upload File" tab

5. **Click "Extract Rules"**: The agent will process the document

6. **Review Results**:
   - View extracted rules
   - Check identified gaps
   - Review statistics
   - Export results as JSON

### View Financial Tracks

Navigate to "View Tracks" to see:
- All predefined financial tracks
- Current rules for each track
- Track definitions

### Batch Processing

1. **Go to "Batch Processing" page**

2. **Create Configuration File**:
   - View the example configuration
   - Create a JSON file with your documents:

```json
[
  {
    "name": "نظام الخدمة المدنية",
    "url": "https://example.com/doc1.pdf",
    "type": "pdf"
  },
  {
    "name": "تعليمات الميزانية",
    "url": "https://example.com/doc2.html",
    "type": "web_page"
  }
]
```

3. **Upload Configuration**: Upload the JSON file

4. **Click "Process Batch"**: The agent will process all documents

5. **Review Comprehensive Report**:
   - Summary statistics
   - Coverage analysis by track
   - Aggregated gaps

### View Results History

Navigate to "Results History" to:
- See all previously processed documents
- View details of past extractions
- Compare results

## Using the CLI

### Basic Commands

#### Extract from a Single Document

```bash
python cli.py extract --name "Document Name" --url "https://example.com/doc.pdf"
```

#### With Additional Options

```bash
python cli.py extract \
  --name "نظام الخدمة المدنية" \
  --url "https://example.com/doc.pdf" \
  --type pdf \
  --output results.json \
  --api-key "your_api_key"
```

#### Extract from Local File

```bash
python cli.py extract \
  --name "Local Document" \
  --file "/path/to/document.pdf" \
  --output results.json
```

#### Batch Processing

```bash
# Create example config
python cli.py init-config

# Edit config_example.json with your documents

# Process batch
python cli.py batch \
  --config-file config_example.json \
  --output comprehensive_report.json
```

#### List Available Tracks

```bash
python cli.py list-tracks
```

### CLI Options Reference

#### `extract` Command

| Option | Short | Required | Description |
|--------|-------|----------|-------------|
| `--name` | `-n` | Yes | Document name |
| `--url` | `-u` | No* | Document URL |
| `--file` | `-f` | No* | Local file path |
| `--type` | `-t` | No | Document type (pdf, web_page, text) |
| `--output` | `-o` | No | Output file path (JSON) |
| `--api-key` | - | No** | aiXplain API key |

\* Either `--url` or `--file` must be provided  
\** Uses `AIXPLAIN_API_KEY` environment variable if not provided

#### `batch` Command

| Option | Short | Required | Description |
|--------|-------|----------|-------------|
| `--config-file` | `-c` | Yes | JSON config file path |
| `--output` | `-o` | No | Output file path (JSON) |
| `--api-key` | - | No* | aiXplain API key |

\* Uses `AIXPLAIN_API_KEY` environment variable if not provided

## Understanding Results

### Extracted Rules

Each extracted rule contains:

- **Rule ID**: Unique identifier
- **Text (Arabic)**: Original rule text
- **Track ID**: Mapped financial track (contracts, salaries, invoices)
- **Status**: extracted, mapped, or requires_review
- **Confidence**: Mapping confidence (0-1)
- **Source**: Document reference with page/section

### Gap Analysis

Gaps are categorized by:

- **Type**:
  - `missing`: Rule not covered at all
  - `partial`: Rule partially covered
  - `conflicting`: Rule conflicts with existing rules

- **Severity**:
  - `critical`: Must be addressed immediately
  - `high`: Should be addressed soon
  - `medium`: Should be reviewed
  - `low`: Nice to have

### Statistics

- **Total Rules**: Number of rules extracted
- **Rules by Track**: Distribution across tracks
- **Rules by Status**: Extraction status breakdown
- **Average Confidence**: Mean mapping confidence
- **Total Gaps**: Number of gaps identified
- **Gaps by Type**: Gap classification

## Best Practices

### Document Preparation

1. **Use official sources**: Always use official government documents
2. **Check accessibility**: Ensure URLs are publicly accessible
3. **Verify format**: PDF and HTML formats work best
4. **Consider size**: Large documents may take longer to process

### Extraction Quality

1. **Review low-confidence rules**: Check rules with confidence < 0.7
2. **Validate mappings**: Verify track assignments are correct
3. **Check source references**: Ensure references are accurate
4. **Use HITL validation**: Submit uncertain rules for human review

### Performance Tips

1. **Batch processing**: Process multiple documents together
2. **Use consistent naming**: Makes results easier to track
3. **Save outputs**: Always save JSON results for records
4. **Monitor logs**: Check logs for errors or warnings

## Troubleshooting

### Common Issues

#### "API Key is required" Error

**Problem**: Missing or invalid API key

**Solution**:
```bash
# Set in .env file
echo "AIXPLAIN_API_KEY=your_key_here" >> .env

# Or provide via command line
python cli.py extract --api-key "your_key_here" ...
```

#### "Failed to parse document" Error

**Problem**: Document is inaccessible or in unsupported format

**Solution**:
- Verify URL is accessible
- Check document format (PDF, HTML supported)
- Try downloading and using local file
- Check internet connection

#### Low Extraction Accuracy

**Problem**: Agent extracts too few or incorrect rules

**Solution**:
- Verify document contains financial rules
- Check document language (Arabic supported)
- Review document structure
- Consider manual preprocessing

#### Slow Processing

**Problem**: Processing takes too long

**Solution**:
- Process smaller documents first
- Use batch mode for multiple documents
- Check internet connection speed
- Consider using faster aiXplain models

### Getting Help

If you encounter issues:

1. Check the error message in logs: `logs/agent_*.log`
2. Review the API documentation
3. Check aiXplain service status
4. Contact support with:
   - Error message
   - Document type and size
   - Steps to reproduce

## Advanced Usage

### Custom Track Definitions

To add custom tracks, edit `src/tracks.py`:

```python
class TracksRepository:
    @staticmethod
    def get_all_tracks() -> Dict[str, FinancialTrack]:
        return {
            # ... existing tracks ...
            "custom_track": FinancialTrack(
                track_id="custom_track",
                name_ar="المسار المخصص",
                name_en="Custom Track",
                definition_ar="تعريف المسار...",
                definition_en="Track definition...",
                current_rules=[...]
            )
        }
```

### Custom Rule Extraction Prompts

To customize extraction prompts, edit `src/rule_extractor.py`:

```python
def _build_extraction_prompt(self, text: str) -> str:
    # Customize the prompt here
    prompt = f"""
    Your custom instructions...
    
    Text: {text}
    """
    return prompt
```

### Integration with External Systems

```python
from src.agent import FinancialRulesAgent

# Initialize agent
agent = FinancialRulesAgent(api_key="your_key")

# Process document
result = agent.process_document(
    name="Document",
    url="https://..."
)

# Export to your system
export_to_your_system(result.extracted_rules)
```

## Appendix

### Supported Document Formats

| Format | Extension | Support | Notes |
|--------|-----------|---------|-------|
| PDF | .pdf | ✅ Full | Best for official documents |
| HTML | .html, .htm | ✅ Full | Web pages |
| Text | .txt | ✅ Full | Plain text files |
| Word | .docx | ❌ No | Convert to PDF first |
| Excel | .xlsx | ❌ No | Not supported |

### Financial Tracks Reference

#### العقود (Contracts)

Covers:
- Payment orders based on milestones
- Construction contracts
- Procurement contracts
- Lease agreements

Current validation rules: 4

#### الرواتب (Salaries)

Covers:
- Employee salaries
- Allowances and benefits
- Deductions
- Overtime pay

Current validation rules: 4

#### الفواتير (Invoices)

Covers:
- Utility bills (electricity, water)
- Mobile/telecom bills
- Consumable services
- Government rate verification

Current validation rules: 4

### Glossary

- **HITL**: Human-in-the-Loop validation
- **aiXplain**: AI platform powering the agent
- **aiR**: aiXplain's Index & Retrieval system
- **Track**: Financial workflow category
- **Gap**: Missing or incomplete rule coverage
- **Confidence**: AI model certainty (0-1)
- **Extraction**: Process of identifying rules from documents
- **Mapping**: Assigning rules to tracks
