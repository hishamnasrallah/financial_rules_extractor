# Quick Start Guide

Get started with the Financial Rules Extraction Agent in 5 minutes!

## Prerequisites

- Python 3.8+
- aiXplain API key

## Installation

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure API key
cp .env.example .env
# Edit .env and add your AIXPLAIN_API_KEY

# 3. Verify installation
python examples/example.py
```

## Quick Examples

### Web Interface (Easiest)

```bash
streamlit run app.py
```

Then:
1. Enter your API key in the sidebar
2. Click "Initialize Agent"
3. Go to "Extract Rules"
4. Enter document details and click "Extract Rules"

### Command Line

```bash
# Extract from a URL
python cli.py extract \
  --name "نظام الخدمة المدنية" \
  --url "https://laws.boe.gov.sa/BoeLaws/Laws/LawDetails/5fb85c90-8962-402d-b2e7-a9a700f2ad95/1"

# Extract from a file
python cli.py extract \
  --name "My Document" \
  --file "/path/to/document.pdf"

# Batch processing
python cli.py batch \
  --config-file examples/batch_documents.json \
  --output report.json
```

### Python API

```python
from src.agent import FinancialRulesAgent

# Initialize agent
agent = FinancialRulesAgent(api_key="your_api_key")

# Process document
result = agent.process_document(
    name="Document Name",
    url="https://example.com/doc.pdf"
)

# View results
print(f"Extracted {len(result.extracted_rules)} rules")
print(f"Identified {len(result.gaps)} gaps")
```

## What's Next?

- 📖 Read the [User Guide](docs/USER_GUIDE.md)
- 📚 Check the [API Documentation](docs/API.md)
- 🔍 Review the [Example Scripts](examples/)

## Need Help?

- Check the [Troubleshooting](docs/USER_GUIDE.md#troubleshooting) section
- Review error logs in `logs/` directory
- Verify your API key is valid

## Key Features

✅ Extract rules from PDFs and web pages  
✅ Automatic mapping to financial tracks  
✅ Gap analysis and recommendations  
✅ HITL validation workflow  
✅ Full audit trail  
✅ CLI and Web interface  

Enjoy using the Financial Rules Extraction Agent! 🚀
