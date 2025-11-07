from typing import Optional
from .config import AIConfig
from . import AIProviderFactory, AIProvider
from .huggingface_provider import HuggingFaceProvider
from .openai_provider import OpenAIProvider


AIProviderFactory.register('huggingface', HuggingFaceProvider)
AIProviderFactory.register('openai', OpenAIProvider)


class AIManager:
    """
    Simplified AI Manager for easy use across the application
    
    Usage:
        ai = AIManager.for_use_case('swot_analysis')
        response = ai.chat("Analyze this company...")
        
    Or:
        ai = AIManager.create('huggingface', model='llama3')
        response = ai.chat("Generate ideas...")
    """
    
    @classmethod
    def for_use_case(
        cls,
        use_case: str,
        api_key: Optional[str] = None,
        **override_config
    ) -> AIProvider:
        """
        Create AI provider optimized for specific use case
        
        Args:
            use_case: Use case name (e.g., 'swot_analysis', 'kpi_generation')
            api_key: Optional API key override
            **override_config: Override default configuration
        
        Returns:
            Configured AIProvider instance
        """
        config = AIConfig.get_use_case_config(use_case)
        config.update(override_config)
        
        provider_name = config.pop('provider')
        model = config.pop('model', None)
        
        return cls.create(
            provider_name,
            api_key=api_key,
            model=model,
            **config
        )
    
    @classmethod
    def create(
        cls,
        provider: str = 'huggingface',
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        **config
    ) -> AIProvider:
        """
        Create AI provider instance
        
        Args:
            provider: Provider name ('huggingface', 'openai')
            model: Model name or alias
            api_key: Optional API key
            **config: Additional provider configuration
        
        Returns:
            AIProvider instance
        """
        if not AIConfig.is_provider_available(provider):
            available = AIConfig.get_available_providers()
            if available:
                provider = available[0]
            else:
                raise Exception("No AI providers available. Please configure API keys.")
        
        provider_config = AIConfig.get_provider_config(provider)
        
        if model is None:
            model = provider_config['default_model']
        
        return AIProviderFactory.create(
            provider,
            api_key=api_key,
            model=model,
            **config
        )
    
    @classmethod
    def get_available_providers(cls) -> list:
        """Get list of available AI providers"""
        return AIConfig.get_available_providers()
    
    @classmethod
    def get_provider_info(cls, provider: str) -> dict:
        """Get information about a specific provider"""
        return AIConfig.get_provider_config(provider)
