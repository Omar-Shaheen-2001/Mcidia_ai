from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class AIProvider(ABC):
    """
    Abstract base class for AI providers (OpenAI, HuggingFace, Ollama, etc.)
    """
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        self.api_key = api_key
        self.config = kwargs
    
    @abstractmethod
    def chat(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        response_format: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Send a chat completion request to the AI provider
        
        Args:
            prompt: User message/prompt
            system_prompt: Optional system instructions
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens in response
            response_format: Optional format (e.g., 'json')
            **kwargs: Provider-specific parameters
        
        Returns:
            str: AI response content
        """
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """Return the current model name"""
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Return the provider name (e.g., 'OpenAI', 'HuggingFace')"""
        pass
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text
        Simple approximation: ~4 characters per token
        """
        return len(text) // 4


class AIProviderFactory:
    """Factory for creating AI provider instances"""
    
    _providers = {}
    
    @classmethod
    def register(cls, name: str, provider_class):
        """Register a new provider"""
        cls._providers[name.lower()] = provider_class
    
    @classmethod
    def create(cls, provider_name: str, **kwargs) -> AIProvider:
        """
        Create an AI provider instance
        
        Args:
            provider_name: Name of provider ('openai', 'huggingface', etc.)
            **kwargs: Provider-specific configuration
        
        Returns:
            AIProvider instance
        """
        provider_class = cls._providers.get(provider_name.lower())
        if not provider_class:
            raise ValueError(
                f"Unknown provider: {provider_name}. "
                f"Available: {list(cls._providers.keys())}"
            )
        return provider_class(**kwargs)
    
    @classmethod
    def get_available_providers(cls) -> list:
        """Get list of registered provider names"""
        return list(cls._providers.keys())
