"""
Document parser for extracting text from PDFs and web pages.
"""
import re
from typing import Optional, Dict, Any
from pathlib import Path
import requests
from bs4 import BeautifulSoup
import PyPDF2
import pdfplumber
from loguru import logger

from src.models import Document, DocumentType, DocumentStatus


class DocumentParser:
    """Parser for extracting text from various document types."""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def parse(self, document: Document) -> Document:
        """
        Parse a document and extract its text content.
        
        Args:
            document: Document object to parse
            
        Returns:
            Updated Document object with extracted content
        """
        try:
            document.status = DocumentStatus.PROCESSING
            
            if document.document_type == DocumentType.PDF:
                if document.url:
                    content = self._parse_pdf_from_url(document.url)
                elif document.file_path:
                    content = self._parse_pdf_from_file(document.file_path)
                else:
                    raise ValueError("PDF document must have either URL or file_path")
            
            elif document.document_type == DocumentType.WEB_PAGE:
                if not document.url:
                    raise ValueError("Web page document must have a URL")
                content = self._parse_web_page(document.url)
            
            elif document.document_type == DocumentType.TEXT:
                if document.file_path:
                    content = self._parse_text_file(document.file_path)
                else:
                    content = document.content or ""
            
            else:
                raise ValueError(f"Unsupported document type: {document.document_type}")
            
            document.content = self._clean_text(content)
            document.status = DocumentStatus.INDEXED
            
            logger.info(f"Successfully parsed document: {document.name}")
            
        except Exception as e:
            logger.error(f"Failed to parse document {document.name}: {str(e)}")
            document.status = DocumentStatus.FAILED
            document.metadata["error"] = str(e)
        
        return document
    
    def _parse_pdf_from_url(self, url: str) -> str:
        """Download and parse PDF from URL."""
        logger.info(f"Downloading PDF from: {url}")
        
        try:
            response = requests.get(url, headers=self.headers, timeout=30, verify=True)
            response.raise_for_status()
        except requests.exceptions.SSLError:
            logger.warning(f"SSL verification failed, retrying without verification...")
            response = requests.get(url, headers=self.headers, timeout=30, verify=False)
            response.raise_for_status()
        
        # Save temporarily
        temp_path = Path("temp_download.pdf")
        temp_path.write_bytes(response.content)
        
        try:
            content = self._parse_pdf_from_file(str(temp_path))
        finally:
            if temp_path.exists():
                temp_path.unlink()
        
        return content
    
    def _parse_pdf_from_file(self, file_path: str) -> str:
        """Parse PDF from local file using pdfplumber (better for Arabic text)."""
        logger.info(f"Parsing PDF file: {file_path}")
        
        text_parts = []
        
        try:
            # Try pdfplumber first (better for Arabic and tables)
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    text = page.extract_text()
                    if text:
                        text_parts.append(f"\n--- Page {page_num} ---\n{text}")
        except Exception as e:
            logger.warning(f"pdfplumber failed: {e}, trying PyPDF2")
            
            # Fallback to PyPDF2
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num, page in enumerate(pdf_reader.pages, start=1):
                    text = page.extract_text()
                    if text:
                        text_parts.append(f"\n--- Page {page_num} ---\n{text}")
        
        return "\n".join(text_parts)
    
    def _parse_web_page(self, url: str) -> str:
        """Parse text content from a web page."""
        logger.info(f"Parsing web page: {url}")
        
        try:
            response = requests.get(url, headers=self.headers, timeout=30, verify=True)
            response.raise_for_status()
        except requests.exceptions.SSLError as e:
            logger.warning(f"SSL verification failed for {url}, retrying without verification...")
            # Disable SSL warnings for this request
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            response = requests.get(url, headers=self.headers, timeout=30, verify=False)
            response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'lxml')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        # Get text
        text = soup.get_text(separator='\n', strip=True)
        
        return text
    
    def _parse_text_file(self, file_path: str) -> str:
        """Parse plain text file."""
        logger.info(f"Parsing text file: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text."""
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        
        # Remove excessive dashes or underscores (often from headers/footers)
        text = re.sub(r'[-_]{4,}', '', text)
        
        return text.strip()
    
    def extract_metadata(self, document: Document) -> Dict[str, Any]:
        """Extract metadata from document."""
        metadata = {}
        
        if document.document_type == DocumentType.PDF and document.file_path:
            try:
                with open(document.file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    metadata['num_pages'] = len(pdf_reader.pages)
                    
                    if pdf_reader.metadata:
                        metadata['title'] = pdf_reader.metadata.get('/Title', '')
                        metadata['author'] = pdf_reader.metadata.get('/Author', '')
                        metadata['subject'] = pdf_reader.metadata.get('/Subject', '')
            except Exception as e:
                logger.warning(f"Failed to extract PDF metadata: {e}")
        
        if document.content:
            metadata['content_length'] = len(document.content)
            metadata['word_count'] = len(document.content.split())
        
        return metadata
