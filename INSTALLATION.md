# Installation Guide

Complete installation guide for the Financial Rules Extraction Agent.

## System Requirements

### Minimum Requirements
- **OS**: Windows 10/11, macOS 10.14+, or Linux (Ubuntu 18.04+)
- **Python**: 3.8 or higher
- **RAM**: 4GB minimum (8GB recommended)
- **Storage**: 2GB free space
- **Internet**: Required for aiXplain API

### Recommended Requirements
- **Python**: 3.10 or 3.11
- **RAM**: 16GB
- **Storage**: 5GB free space
- **Internet**: High-speed connection for large documents

## Installation Methods

### Method 1: Quick Start (Windows)

1. **Download the project**:
   ```bash
   git clone <repository-url>
   cd extract_financial_rules
   ```

2. **Run quick start script**:
   ```bash
   quickstart.bat
   ```
   
   The script will:
   - Check Python installation
   - Create virtual environment
   - Install dependencies
   - Create .env file
   - Launch the application

### Method 2: Manual Installation (All Platforms)

#### Step 1: Install Python

**Windows**:
```bash
# Download from python.org
# Or use winget:
winget install Python.Python.3.11
```

**macOS**:
```bash
brew install python@3.11
```

**Linux (Ubuntu/Debian)**:
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip
```

#### Step 2: Create Virtual Environment

```bash
# Navigate to project directory
cd extract_financial_rules

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate

# macOS/Linux:
source venv/bin/activate
```

#### Step 3: Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt
```

#### Step 4: Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your API key
# Windows:
notepad .env

# macOS/Linux:
nano .env
```

Add your aiXplain API key:
```env
AIXPLAIN_API_KEY=your_actual_api_key_here
```

#### Step 5: Verify Installation

```bash
# Run test script
python tests/test_agent.py

# Run example
python examples/example.py
```

### Method 3: Package Installation

```bash
# Install as a package
pip install -e .

# Now you can use the CLI from anywhere
extract-rules --help
```

## Getting aiXplain API Key

1. **Sign up for aiXplain**:
   - Visit: https://console.aixplain.com
   - Click "Sign Up" or "Log In"
   - Complete registration

2. **Create API Key**:
   - Go to Settings → API Keys
   - Click "Create New Key"
   - Give it a name (e.g., "Financial Rules Agent")
   - Copy the key (you'll only see it once!)

3. **Add to Environment**:
   - Paste key in `.env` file
   - Or set environment variable:
     ```bash
     # Windows
     set AIXPLAIN_API_KEY=your_key_here
     
     # macOS/Linux
     export AIXPLAIN_API_KEY=your_key_here
     ```

## Verification

### Test CLI

```bash
# Check CLI is working
python cli.py --help

# List available tracks
python cli.py list-tracks
```

### Test Web Interface

```bash
# Launch Streamlit app
streamlit run app.py

# Should open browser at http://localhost:8501
```

### Test Python API

```python
# Create test script: test_install.py
from src.agent import FinancialRulesAgent
from src.tracks import TracksRepository

print("Testing installation...")

# Test tracks loading
tracks = TracksRepository.get_all_tracks()
print(f"✓ Loaded {len(tracks)} tracks")

# Test agent initialization (requires API key)
try:
    agent = FinancialRulesAgent(api_key="your_key_here")
    print("✓ Agent initialized")
except Exception as e:
    print(f"⚠ Agent initialization failed: {e}")

print("Installation test complete!")
```

Run it:
```bash
python test_install.py
```

## Troubleshooting Installation

### Issue: Python not found

**Solution**:
```bash
# Windows - Add Python to PATH
# Go to System Properties → Environment Variables
# Add Python installation directory to PATH

# macOS/Linux - Install Python
brew install python@3.11  # macOS
sudo apt install python3.11  # Linux
```

### Issue: pip install fails

**Solution**:
```bash
# Upgrade pip
python -m pip install --upgrade pip

# Try with verbose output
pip install -r requirements.txt -v

# Install packages one by one if needed
pip install aiXplain
pip install streamlit
# etc.
```

### Issue: Virtual environment activation fails

**Windows PowerShell**:
```powershell
# Enable script execution
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then activate
.\venv\Scripts\Activate.ps1
```

**Solution for all platforms**:
```bash
# Use python -m venv instead
python -m venv venv --clear
```

### Issue: aiXplain package not found

**Solution**:
```bash
# Install directly from PyPI
pip install aiXplain --upgrade

# Or install specific version
pip install aiXplain==0.2.30
```

### Issue: SSL certificate errors

**Solution**:
```bash
# Windows - Update certificates
pip install --upgrade certifi

# macOS - Install certificates
/Applications/Python\ 3.11/Install\ Certificates.command

# Linux - Update ca-certificates
sudo apt-get install ca-certificates
```

### Issue: Memory errors during large document processing

**Solution**:
```python
# Process in smaller chunks
# Edit src/rule_extractor.py
def _chunk_document(self, content: str, chunk_size: int = 1000):
    # Reduce chunk_size from 2000 to 1000
    ...
```

## Platform-Specific Notes

### Windows

- Use PowerShell or Command Prompt
- May need to install Microsoft C++ Build Tools for some packages
- Windows Defender may slow down first-time installation

### macOS

- May need to install Xcode Command Line Tools:
  ```bash
  xcode-select --install
  ```
- Use Homebrew for easiest Python installation

### Linux

- May need to install additional system packages:
  ```bash
  sudo apt-get install python3-dev build-essential
  ```
- Some PDF parsing may require poppler-utils:
  ```bash
  sudo apt-get install poppler-utils
  ```

## Optional Dependencies

### For Development

```bash
# Install dev dependencies
pip install pytest pytest-cov black flake8 mypy
```

### For Enhanced PDF Processing

```bash
# Install additional PDF tools
pip install pdf2image  # Requires poppler
pip install pytesseract  # For OCR
```

### For Performance

```bash
# Install accelerated JSON parsing
pip install orjson

# Install fast HTTP client
pip install httpx
```

## Docker Installation (Optional)

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Set environment
ENV AIXPLAIN_API_KEY=""

# Expose Streamlit port
EXPOSE 8501

# Run Streamlit
CMD ["streamlit", "run", "app.py"]
```

Build and run:
```bash
# Build image
docker build -t financial-rules-agent .

# Run container
docker run -p 8501:8501 \
  -e AIXPLAIN_API_KEY=your_key_here \
  financial-rules-agent
```

## Updating

### Update Dependencies

```bash
# Pull latest code
git pull

# Update packages
pip install -r requirements.txt --upgrade
```

### Update aiXplain SDK

```bash
# Check current version
pip show aiXplain

# Update to latest
pip install aiXplain --upgrade
```

## Uninstallation

```bash
# Remove virtual environment
rm -rf venv  # macOS/Linux
rmdir /s venv  # Windows

# Remove package if installed
pip uninstall financial-rules-extractor

# Remove project directory
cd ..
rm -rf extract_financial_rules
```

## Next Steps

After successful installation:

1. **Configure**: Edit `.env` with your API key
2. **Test**: Run `python tests/test_agent.py`
3. **Explore**: Try `python examples/example.py`
4. **Use**: Launch web UI with `streamlit run app.py`
5. **Learn**: Read [User Guide](docs/USER_GUIDE.md)

## Support

If you encounter installation issues:

1. Check Python version: `python --version`
2. Check pip version: `pip --version`
3. Review error logs in terminal
4. Check disk space: `df -h` (Linux/macOS) or `dir` (Windows)
5. Try clean reinstall with fresh virtual environment

## Verified Environments

The agent has been tested on:

- ✅ Windows 10/11 with Python 3.8-3.11
- ✅ macOS 12+ with Python 3.9-3.11
- ✅ Ubuntu 20.04/22.04 with Python 3.8-3.11
- ✅ Docker containers with Python 3.11-slim

## Quick Reference

| Task | Command |
|------|---------|
| Create venv | `python -m venv venv` |
| Activate (Win) | `venv\Scripts\activate` |
| Activate (Unix) | `source venv/bin/activate` |
| Install deps | `pip install -r requirements.txt` |
| Run tests | `python tests/test_agent.py` |
| Run web UI | `streamlit run app.py` |
| Run CLI | `python cli.py --help` |
| Deactivate | `deactivate` |

---

**Happy extracting! 🚀**
