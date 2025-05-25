"""API client management for DataInsightKit."""
from typing import Optional
from openai import OpenAI
from ..config import config

class APIClients:
    """Manages API clients for various services."""
    
    _openai_client = None
    
    @classmethod
    def get_openai_client(cls) -> OpenAI:
        """
        Get or create an OpenAI client.
        
        Returns:
            OpenAI: An instance of the OpenAI client.
            
        Raises:
            ValueError: If the OpenAI API key is not configured.
        """
        if cls._openai_client is None:
            if not config.openai_api_key:
                raise ValueError(
                    "OpenAI API key not found. "
                    "Please set the OPENAI_API_KEY environment variable."
                )
            cls._openai_client = OpenAI(api_key=config.openai_api_key)
        return cls._openai_client
    
    @classmethod
    def set_openai_client(cls, client: OpenAI) -> None:
        """
        Set a custom OpenAI client (useful for testing).
        
        Args:
            client: An instance of the OpenAI client.
        """
        cls._openai_client = client

# Create a singleton instance
api_clients = APIClients()

def get_openai_client() -> OpenAI:
    """
    Helper function to get the OpenAI client.
    
    Returns:
        OpenAI: An instance of the OpenAI client.
    """
    return api_clients.get_openai_client()
