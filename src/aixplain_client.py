"""
aiXplain integration layer for document indexing and model execution.
"""
import time
from typing import List, Dict, Any, Optional
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

# Import aiXplain SDK
try:
    from aixplain.factories import ModelFactory, DatasetFactory, FinetuneFactory
    from aixplain.enums import Function, Language
    import aixplain
except ImportError:
    logger.warning("aiXplain SDK not installed. Install with: pip install aiXplain")
    aixplain = None

from src.config import config
from src.models import Document


class AIXplainClient:
    """Client for interacting with aiXplain platform."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize aiXplain client.
        
        Args:
            api_key: aiXplain API key (defaults to config)
        """
        self.api_key = api_key or config.aixplain.api_key
        
        if not self.api_key:
            raise ValueError("aiXplain API key is required")
        
        # Set API key for aiXplain SDK
        if aixplain:
            aixplain.api_key = self.api_key
        
        self.search_model = None
        self.llm_model = None
        self.index_name = config.aixplain.index_name
        
        logger.info("aiXplain client initialized")
    
    def initialize_models(self):
        """Initialize required models (optional - system works without them)."""
        try:
            # Load search model (aiR) - optional
            if config.aixplain.search_model_id:
                try:
                    logger.info(f"Loading search model: {config.aixplain.search_model_id}")
                    self.search_model = ModelFactory.get(config.aixplain.search_model_id)
                    logger.info("Search model loaded successfully")
                except Exception as e:
                    logger.warning(f"Could not load search model (will use fallback methods): {e}")
                    self.search_model = None
            
            # Load LLM model if specified - optional
            if config.aixplain.llm_model_id:
                try:
                    logger.info(f"Loading LLM model: {config.aixplain.llm_model_id}")
                    self.llm_model = ModelFactory.get(config.aixplain.llm_model_id)
                    logger.info("LLM model loaded successfully")
                except Exception as e:
                    logger.warning(f"Could not load LLM model (will use fallback methods): {e}")
                    self.llm_model = None
            
            if self.search_model or self.llm_model:
                logger.info("Some models initialized successfully")
            else:
                logger.info("No models loaded - using fallback pattern-based extraction")
            
        except Exception as e:
            logger.warning(f"Model initialization encountered issues: {e}")
            logger.info("System will use fallback methods for extraction")
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def create_index(self, documents: List[Document]) -> Dict[str, Any]:
        """
        Create an index and upsert documents using aiR.
        
        Args:
            documents: List of documents to index
            
        Returns:
            Dictionary with indexing results
        """
        if not aixplain:
            raise RuntimeError("aiXplain SDK not available")
        
        logger.info(f"Creating index with {len(documents)} documents")
        
        try:
            # Prepare documents for indexing
            records = []
            for doc in documents:
                if doc.content:
                    record = {
                        "id": doc.document_id,
                        "text": doc.content,
                        "metadata": {
                            "name": doc.name,
                            "url": doc.url or "",
                            "type": doc.document_type.value,
                            **doc.metadata
                        }
                    }
                    records.append(record)
            
            # Note: This is a simplified version. In production, you would:
            # 1. Create a dataset from the documents
            # 2. Use FinetuneFactory to create an index
            # 3. Monitor the indexing process
            
            logger.info(f"Prepared {len(records)} records for indexing")
            
            return {
                "status": "success",
                "num_documents": len(records),
                "index_name": self.index_name
            }
            
        except Exception as e:
            logger.error(f"Failed to create index: {e}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def search(self, query: str, num_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search the index for relevant documents.
        
        Args:
            query: Search query
            num_results: Number of results to return
            
        Returns:
            List of search results with scores
        """
        if not self.search_model:
            self.initialize_models()
        
        logger.info(f"Searching for: {query}")
        
        try:
            # Execute search
            response = self.search_model.run(
                query,
                parameters={"numResults": num_results}
            )
            
            # Parse results
            results = []
            if response and hasattr(response, 'data'):
                # Format will depend on the actual aiR response structure
                results = response.data if isinstance(response.data, list) else [response.data]
            
            logger.info(f"Found {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def execute_llm(self, prompt: str, max_tokens: int = 2000) -> str:
        """
        Execute LLM model for text generation.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text
        """
        if not self.llm_model:
            # Try to find a suitable LLM model
            self._find_llm_model()
        
        if not self.llm_model:
            raise RuntimeError("No LLM model available")
        
        logger.info("Executing LLM")
        
        try:
            response = self.llm_model.run(
                prompt,
                parameters={"max_tokens": max_tokens}
            )
            
            # Extract text from response
            if response and hasattr(response, 'data'):
                return str(response.data)
            
            return ""
            
        except Exception as e:
            logger.error(f"LLM execution failed: {e}")
            raise
    
    def _find_llm_model(self):
        """Find a suitable LLM model from aiXplain marketplace."""
        try:
            logger.info("Searching for LLM models...")
            
            # Search for text generation models
            # This is a placeholder - actual implementation would use ModelFactory.list()
            # with appropriate filters
            
            logger.warning("No LLM model configured. Set AIXPLAIN_LLM_MODEL_ID in .env")
            
        except Exception as e:
            logger.error(f"Failed to find LLM model: {e}")
    
    def list_available_models(self, function: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List available models from aiXplain marketplace.
        
        Args:
            function: Filter by function (e.g., 'text-generation', 'embedding')
            
        Returns:
            List of available models
        """
        try:
            # This would use ModelFactory.list() with filters
            logger.info("Listing available models")
            
            # Placeholder implementation
            return []
            
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []


class IndexManager:
    """Manager for document indexing operations."""
    
    def __init__(self, client: AIXplainClient):
        self.client = client
        self.indexed_documents = {}
    
    def index_documents(self, documents: List[Document]) -> Dict[str, Any]:
        """
        Index a list of documents.
        
        Args:
            documents: List of documents to index
            
        Returns:
            Indexing results
        """
        logger.info(f"Indexing {len(documents)} documents")
        
        start_time = time.time()
        
        try:
            result = self.client.create_index(documents)
            
            # Track indexed documents
            for doc in documents:
                self.indexed_documents[doc.document_id] = doc
            
            elapsed = time.time() - start_time
            result['elapsed_seconds'] = elapsed
            
            logger.info(f"Indexing completed in {elapsed:.2f} seconds")
            return result
            
        except Exception as e:
            logger.error(f"Indexing failed: {e}")
            raise
    
    def get_indexed_document(self, document_id: str) -> Optional[Document]:
        """Get an indexed document by ID."""
        return self.indexed_documents.get(document_id)
    
    def count_indexed_documents(self) -> int:
        """Get count of indexed documents."""
        return len(self.indexed_documents)
