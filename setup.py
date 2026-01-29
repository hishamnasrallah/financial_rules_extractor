"""
Setup script for installing the Financial Rules Extraction Agent.
"""
from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    requirements = [
        line.strip() 
        for line in requirements_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]

setup(
    name="financial-rules-extractor",
    version="1.0.0",
    author="Financial Rules Extraction Team",
    description="AI agent for extracting and analyzing financial rules from official documents",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/extract_financial_rules",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "Intended Audience :: Government",
        "Topic :: Office/Business :: Financial",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "extract-rules=cli:cli",
        ],
    },
    include_package_data=True,
    keywords="financial rules extraction ai compliance aixplain",
    project_urls={
        "Documentation": "https://github.com/yourusername/extract_financial_rules/docs",
        "Source": "https://github.com/yourusername/extract_financial_rules",
        "Tracker": "https://github.com/yourusername/extract_financial_rules/issues",
    },
)
