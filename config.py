"""Configuration management for DataInsightKit."""
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

class Config:
    """Configuration class for DataInsightKit."""
    
    def __init__(self):
        """Initialize configuration with default values."""
        # API Keys
        self.openai_api_key: Optional[str] = os.getenv('OPENAI_API_KEY')
        
        # API Settings
        self.openai_model: str = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
        self.openai_temperature: float = float(os.getenv('OPENAI_TEMPERATURE', '0.7'))
        self.openai_max_tokens: int = int(os.getenv('OPENAI_MAX_TOKENS', '1000'))
        
        # Application Settings
        self.debug: bool = os.getenv('DEBUG', 'False').lower() == 'true'
        self.log_level: str = os.getenv('LOG_LEVEL', 'INFO')
    
    def validate(self) -> bool:
        """Validate that all required configurations are set."""
        # Add validation logic here
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Return configuration as a dictionary, excluding sensitive data."""
        return {
            'openai_model': self.openai_model,
            'openai_temperature': self.openai_temperature,
            'openai_max_tokens': self.openai_max_tokens,
            'debug': self.debug,
            'log_level': self.log_level,
            # Note: We don't include API keys in the dict
        }

# Create a singleton instance
config = Config()

# Validate configuration on import
if not config.validate():
    raise RuntimeError("Invalid configuration. Please check your environment variables.")
