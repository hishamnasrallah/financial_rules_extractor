"""
Configuration management for the Financial Rules Extraction Agent.
"""
import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class AIXplainConfig(BaseModel):
    """aiXplain platform configuration."""
    api_key: str = Field(..., description="aiXplain API key")
    embedding_model_id: Optional[str] = Field(None, description="Custom embedding model ID")
    llm_model_id: Optional[str] = Field(None, description="Custom LLM model ID")
    search_model_id: Optional[str] = Field(None, description="aiR Search model ID")  # Changed default to None
    index_name: str = Field("financial_rules_index", description="Index name for document storage")


class AppConfig(BaseModel):
    """Application configuration."""
    log_level: str = Field("INFO", description="Logging level")
    max_retries: int = Field(3, description="Maximum number of retries for API calls")
    timeout_seconds: int = Field(60, description="Timeout for API calls in seconds")
    
    # Paths
    base_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent)
    data_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent / "data")
    output_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent / "output")
    logs_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent / "logs")


class Config:
    """Main configuration class."""
    
    def __init__(self):
        self.aixplain = AIXplainConfig(
            api_key=os.getenv("AIXPLAIN_API_KEY", ""),
            embedding_model_id=os.getenv("AIXPLAIN_EMBEDDING_MODEL_ID"),
            llm_model_id=os.getenv("AIXPLAIN_LLM_MODEL_ID"),
            search_model_id=os.getenv("AIXPLAIN_SEARCH_MODEL_ID"),  # Removed default
            index_name=os.getenv("AIXPLAIN_INDEX_NAME", "financial_rules_index")
        )
        
        self.app = AppConfig(
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            max_retries=int(os.getenv("MAX_RETRIES", "3")),
            timeout_seconds=int(os.getenv("TIMEOUT_SECONDS", "60"))
        )
        
        # Create necessary directories
        self._create_directories()
    
    def _create_directories(self):
        """Create necessary directories if they don't exist."""
        for dir_path in [self.app.data_dir, self.app.output_dir, self.app.logs_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
            
            # Create subdirectories
            if dir_path == self.app.data_dir:
                (dir_path / "raw").mkdir(exist_ok=True)
                (dir_path / "processed").mkdir(exist_ok=True)
    
    def validate(self) -> bool:
        """Validate configuration."""
        if not self.aixplain.api_key:
            raise ValueError("AIXPLAIN_API_KEY is required. Please set it in .env file.")
        return True


# Global config instance
config = Config()
