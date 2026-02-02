# Financial Rules Extraction Agent

![Version](https://img.shields.io/badge/version-2.1.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)

AI-powered agent for extracting and analyzing financial rules from Saudi government documents.

## Overview

Analyzes Saudi government financial policies and extracts rules mapped to three tracks:
- **العقود (Contracts)**: Payment orders and milestones
- **الرواتب (Salaries)**: Employee compensation and benefits  
- **الفواتير (Invoices)**: Utility bills and services

## Features

- PDF and web document parsing (Arabic/English)
- True RAG with ChromaDB vector database
- aiXplain LLM integration
- Gap analysis against existing rules
- Streamlit web UI + CLI interface
- MCP server for external integration
- Slack, Discord, Email, Webhook notifications

## Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Configure API key
cp .env.example .env
# Edit .env: AIXPLAIN_API_KEY=your_key_here
```

### Usage

**Web Interface:**
```bash
streamlit run app.py
```

**Command Line:**
```bash
python cli.py extract --name "Document" --url "https://laws.boe.gov.sa/..."
```

**MCP Server:**
```bash
python mcp_server.py
```

## Configuration

Edit `.env`:

```bash
AIXPLAIN_API_KEY=your_api_key_here
CHUNK_SIZE=500
USE_RAG=true
```

## Architecture

```
Document → Parse → Chunk → Embeddings → ChromaDB
                                            ↓
Query → Vector Search → Retrieve → aiXplain LLM → Extract Rules
                                                        ↓
                                                  Map to Tracks
```

**Technologies:**
- **aiXplain**: LLM models and embeddings
- **ChromaDB**: Persistent vector database
- **Streamlit**: Web UI
- **MCP**: Model Context Protocol server

## Project Structure

```
extract_financial_rules/
├── src/
│   ├── agent.py              # Main orchestrator
│   ├── aixplain_client.py    # RAG + ChromaDB
│   ├── rule_extractor.py     # Rule extraction
│   ├── parser.py             # Document parsing
│   ├── integrations.py       # External integrations
│   └── tracks_api.py         # Dynamic tracks
├── app.py                    # Streamlit UI
├── cli.py                    # CLI
├── mcp_server.py             # MCP server
└── test_chromadb.py          # Test script
```

## Documentation

- [Installation Guide](INSTALLATION.md)
- [Quick Start](QUICKSTART.md)
- [User Guide](docs/USER_GUIDE.md)
- [Technical Architecture](docs/TECHNICAL_ARCHITECTURE.md)
- [MCP Server Guide](MCP_SERVER.md)

## Testing

```bash
# Test ChromaDB
python test_chromadb.py

# Test extraction
python cli.py extract --name "Test" --url "https://..."

# Run web UI
streamlit run app.py
```

## License

MIT License
