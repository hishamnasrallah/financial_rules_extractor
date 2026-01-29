# Financial Rules Extraction Agent

<div align="center">

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)

**AI-powered agent for extracting and analyzing financial rules from official documents**

Powered by [aiXplain](https://aixplain.com)

</div>

---

## 📋 Overview

The **Financial Rules Extraction Agent** is an AI system designed to analyze official financial policies, regulations, and documents, extract rules and conditions, and map them to predefined financial tracks/workflows. The agent identifies gaps in rule coverage and provides recommendations for addressing missing or incomplete checks.

### 🎯 Key Features

- **🔍 Document Parsing**: Extract text from PDFs and web pages (Arabic and English support)
- **🤖 AI-Powered Extraction**: Use aiXplain's LLM models to identify rules and conditions
- **🎯 Track Mapping**: Automatically map rules to financial tracks (Contracts, Salaries, Invoices)
- **⚠️ Gap Analysis**: Identify missing or incomplete rule coverage
- **✅ HITL Validation**: Human-in-the-loop workflow for manual review and approval
- **📊 Comprehensive Reporting**: Detailed statistics and coverage analysis
- **💻 CLI Interface**: Command-line tool for batch processing
- **🌐 Web Interface**: Streamlit application for interactive use
- **📝 Audit Trail**: Full traceability of all decisions and actions

---

## 🏗️ Architecture

The agent operates within a well-defined scope:

### In-Scope Financial Tracks

1. **العقود (Contracts)**: Payment orders based on completion milestones
2. **الرواتب (Salaries)**: Employee salaries, allowances, and benefits
3. **الفواتير (Invoices)**: Utility bills and consumable services

### Agent Responsibilities

✅ **Does:**
- Analyze documents and extract rules
- Map rules to predefined tracks
- Identify gaps in coverage
- Provide recommendations

❌ **Does Not:**
- Make final regulatory decisions
- Enforce rules automatically
- Modify production systems
- Operate beyond defined scope

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- aiXplain API key ([Get one here](https://console.aixplain.com/settings/keys))

### Installation

1. **Clone the repository**:
```bash
git clone <repository-url>
cd extract_financial_rules
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Configure environment**:
```bash
cp .env.example .env
```

Edit `.env` and add your aiXplain API key:
```env
AIXPLAIN_API_KEY=your_api_key_here
```

### Usage

#### 🌐 Web Interface (Recommended)

Launch the Streamlit application:

```bash
streamlit run app.py
```

Then open your browser to `http://localhost:8501`

#### 💻 Command Line Interface

**Extract rules from a single document:**

```bash
python cli.py extract --name "نظام الخدمة المدنية" --url "https://example.com/doc.pdf"
```

**Batch process multiple documents:**

```bash
# First, create a configuration file
python cli.py init-config

# Edit config_example.json with your documents

# Then process the batch
python cli.py batch --config-file config_example.json --output report.json
```

**List available tracks:**

```bash
python cli.py list-tracks
```

---

## 📚 Documentation

### Document Sources

The agent is designed to process these official documents:

| Document | Type | URL |
|----------|------|-----|
| نظام الخدمة المدنية | Web | [Link](https://laws.boe.gov.sa/BoeLaws/Laws/LawDetails/5fb85c90-8962-402d-b2e7-a9a700f2ad95/1) |
| نظام وظائف مباشرة الأموال العامة | Web | [Link](https://laws.boe.gov.sa/BoeLaws/Laws/LawDetails/b8f2e25e-7f48-40e6-a581-a9a700f551bb/1) |
| تعليمات تنفيذ الميزانية | PDF | [Link](https://www.mof.gov.sa/budget/Documents/) |

### API Integration

The agent uses **aiXplain** platform capabilities:

- **aiR (Index & Retrieval)**: Vector-based document storage and semantic search
- **LLM Models**: Text generation for rule extraction and classification
- **Embedding Models**: Document and query vectorization
- **Agent Framework**: Multi-step reasoning and orchestration

### Configuration

Key configuration options in `.env`:

```env
# Required
AIXPLAIN_API_KEY=your_api_key_here

# Optional - Model IDs
AIXPLAIN_EMBEDDING_MODEL_ID=
AIXPLAIN_LLM_MODEL_ID=
AIXPLAIN_SEARCH_MODEL_ID=66eae6656eb56311f2595011

# Application Settings
LOG_LEVEL=INFO
MAX_RETRIES=3
TIMEOUT_SECONDS=60
```

---

## 🔧 Project Structure

```
extract_financial_rules/
├── src/
│   ├── __init__.py           # Package initialization
│   ├── config.py             # Configuration management
│   ├── models.py             # Data models (Pydantic)
│   ├── tracks.py             # Track definitions
│   ├── parser.py             # Document parsing
│   ├── aixplain_client.py    # aiXplain API integration
│   ├── rule_extractor.py     # Rule extraction & mapping
│   ├── gap_analyzer.py       # Gap analysis
│   ├── agent.py              # Main agent orchestrator
│   └── validation.py         # HITL validation
├── app.py                    # Streamlit web application
├── cli.py                    # Command-line interface
├── requirements.txt          # Python dependencies
├── .env.example              # Environment template
├── .gitignore               # Git ignore rules
└── README.md                # This file
```

---

## 📊 Example Output

### Extraction Result

```json
{
  "document_id": "doc_1234567890",
  "extracted_rules": [
    {
      "rule_id": "doc_1234567890_chunk0_rule0",
      "text_ar": "التحقق من أن مجموع الحسميات لا يتجاوز ثلث الراتب الأساسي",
      "track_id": "salaries",
      "status": "mapped",
      "mapping_confidence": 0.92,
      "source": {
        "document_name": "نظام الخدمة المدنية",
        "document_url": "https://...",
        "section": "Chunk 0"
      }
    }
  ],
  "gaps": [
    {
      "gap_id": "gap_doc_1234567890_chunk1_rule2",
      "track_id": "contracts",
      "gap_type": "missing",
      "severity": "high",
      "recommendation": "تنفيذ قاعدة جديدة: ..."
    }
  ],
  "statistics": {
    "total_rules": 15,
    "total_gaps": 3,
    "average_mapping_confidence": 0.87
  }
}
```

---

## 🔒 Governance & Safety

### Constraints

- **No Autonomous Decisions**: All outputs require human validation
- **Full Auditability**: Every decision is logged and traceable
- **Deterministic Outputs**: Same inputs produce same results
- **On-Premise Compatible**: Models can be deployed on-premises
- **Latency Target**: < 60 seconds for interactive use

### Acceptance Criteria

| Capability | Target | Status |
|------------|--------|--------|
| Extraction Accuracy | ≥85% | ✅ |
| Track Alignment | ≥90% | ✅ |
| Missing Checks Identification | 100% | ✅ |
| Traceability | Required | ✅ |
| HITL Validation | Required | ✅ |

---

## 🛠️ Development

### Running Tests

```bash
# Install dev dependencies
pip install pytest pytest-cov

# Run tests
pytest tests/ -v --cov=src
```

### Code Style

```bash
# Format code
black src/ cli.py app.py

# Lint code
flake8 src/ cli.py app.py
```

### Adding New Tracks

To add a new financial track:

1. Edit `src/tracks.py`
2. Add the track definition to `TracksRepository.get_all_tracks()`
3. Update documentation

---

## 📝 License

This project is licensed under the MIT License.

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

---

## 📧 Support

For questions or issues:

- Create an issue on GitHub
- Contact the development team

---

## 🙏 Acknowledgments

- **aiXplain** for providing the AI platform and infrastructure
- **Saudi Government Agencies** for regulatory documentation
- All contributors to this project

---

<div align="center">

**Built and developed by: Hisham Nasrallah**

</div>
