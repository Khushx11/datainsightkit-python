"""Configuration management for DataInsightKit.

This module provides centralized configuration management for the DataInsightKit package.
It handles loading configuration from environment variables and provides type-safe access
to configuration values.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional, Union
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
env_path = Path(__file__).parent.parent.parent / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

class Config:
    """Central configuration class for DataInsightKit.
    
    This class provides type-safe access to configuration values loaded from
    environment variables. It implements the singleton pattern to ensure
    consistent configuration access throughout the application.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        # API Keys
        self.openai_api_key: Optional[str] = os.getenv('OPENAI_API_KEY')
        
        # API Settings
        self.openai_model: str = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
        self.openai_temperature: float = float(os.getenv('OPENAI_TEMPERATURE', '0.7'))
        self.openai_max_tokens: int = int(os.getenv('OPENAI_MAX_TOKENS', '1000'))
        
        # Application Settings
        self.debug: bool = os.getenv('DEBUG', 'False').lower() == 'true'
        self.log_level: str = os.getenv('LOG_LEVEL', 'INFO')
        
        self._initialized = True
    
    def validate(self) -> bool:
        """Validate that all required configuration values are set.
        
        Returns:
            bool: True if all required configurations are valid, False otherwise.
        """
        # Add validation logic for required settings
        if not self.openai_api_key:
            return False
        return True
    
    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Convert configuration to a dictionary.
        
        Args:
            include_sensitive: If True, include sensitive values like API keys.
            
        Returns:
            Dict containing configuration values.
        """
        result = {
            'openai_model': self.openai_model,
            'openai_temperature': self.openai_temperature,
            'openai_max_tokens': self.openai_max_tokens,
            'debug': self.debug,
            'log_level': self.log_level,
        }
        
        if include_sensitive:
            result['openai_api_key'] = '***' if self.openai_api_key else None
            
        return result

# Create a singleton instance
config = Config()

# Validate configuration on import
if not config.validate():
    import warnings
    warnings.warn(
        "Some required configurations are missing. "
        "Please check your environment variables.",
        RuntimeWarning
    )

__all__ = ['config', 'Config']