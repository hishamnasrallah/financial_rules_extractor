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
    search_model_id: Optional[str] = Field(None, description="aiR Search model ID")
    index_name: str = Field("financial_rules_index", description="Index name for document storage")
    dataset_name: str = Field("financial_rules_dataset", description="Dataset name for aiR")
    chunk_size: int = Field(2000, description="Document chunk size for indexing")
    chunk_overlap: int = Field(200, description="Overlap between chunks")
    retrieval_top_k: int = Field(5, description="Number of chunks to retrieve")


class IntegrationConfig(BaseModel):
    """External integrations configuration."""
    # Slack
    slack_webhook_url: Optional[str] = Field(None, description="Slack webhook URL")
    slack_channel: str = Field("#financial-rules", description="Slack channel")
    
    # Discord
    discord_webhook_url: Optional[str] = Field(None, description="Discord webhook URL")
    
    # Email
    smtp_host: Optional[str] = Field(None, description="SMTP host")
    smtp_port: int = Field(587, description="SMTP port")
    smtp_user: Optional[str] = Field(None, description="SMTP user")
    smtp_password: Optional[str] = Field(None, description="SMTP password")
    smtp_from: Optional[str] = Field(None, description="From email address")
    notification_email: Optional[str] = Field(None, description="Notification recipient email")
    
    # Generic Webhook
    custom_webhook_url: Optional[str] = Field(None, description="Custom webhook URL")
    
    # Feature Flags
    enable_notifications: bool = Field(False, description="Enable notifications")


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
    
    # RAG Configuration
    use_rag: bool = Field(True, description="Use RAG approach (retrieval-based)")
    enable_dynamic_tracks: bool = Field(False, description="Enable dynamic track management")


class Config:
    """Main configuration class."""
    
    def __init__(self):
        self.aixplain = AIXplainConfig(
            api_key=os.getenv("AIXPLAIN_API_KEY", ""),
            embedding_model_id=os.getenv("AIXPLAIN_EMBEDDING_MODEL_ID"),
            llm_model_id=os.getenv("AIXPLAIN_LLM_MODEL_ID"),
            search_model_id=os.getenv("AIXPLAIN_SEARCH_MODEL_ID"),
            index_name=os.getenv("AIXPLAIN_INDEX_NAME", "financial_rules_index"),
            dataset_name=os.getenv("AIXPLAIN_DATASET_NAME", "financial_rules_dataset"),
            chunk_size=int(os.getenv("CHUNK_SIZE", "2000")),
            chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "200")),
            retrieval_top_k=int(os.getenv("RETRIEVAL_TOP_K", "5"))
        )
        
        self.integrations = IntegrationConfig(
            slack_webhook_url=os.getenv("SLACK_WEBHOOK_URL"),
            slack_channel=os.getenv("SLACK_CHANNEL", "#financial-rules"),
            discord_webhook_url=os.getenv("DISCORD_WEBHOOK_URL"),
            smtp_host=os.getenv("SMTP_HOST"),
            smtp_port=int(os.getenv("SMTP_PORT", "587")),
            smtp_user=os.getenv("SMTP_USER"),
            smtp_password=os.getenv("SMTP_PASSWORD"),
            smtp_from=os.getenv("SMTP_FROM"),
            notification_email=os.getenv("NOTIFICATION_EMAIL"),
            custom_webhook_url=os.getenv("CUSTOM_WEBHOOK_URL"),
            enable_notifications=os.getenv("ENABLE_NOTIFICATIONS", "false").lower() == "true"
        )
        
        self.app = AppConfig(
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            max_retries=int(os.getenv("MAX_RETRIES", "3")),
            timeout_seconds=int(os.getenv("TIMEOUT_SECONDS", "60")),
            use_rag=os.getenv("USE_RAG", "true").lower() == "true",
            enable_dynamic_tracks=os.getenv("ENABLE_DYNAMIC_TRACKS", "false").lower() == "true"
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
