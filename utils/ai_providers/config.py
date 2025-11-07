import os
from typing import Optional, Dict, Any


class AIConfig:
    """
    AI Provider Configuration Manager
    
    Manages provider selection, model selection, and feature flags
    """
    
    PROVIDERS = {
        'huggingface': {
            'name': 'HuggingFace',
            'free': True,
            'models': {
                'llama3': 'meta-llama/Meta-Llama-3-8B-Instruct',
                'mistral': 'mistralai/Mistral-7B-Instruct-v0.2',
                'mixtral': 'mistralai/Mixtral-8x7B-Instruct-v0.1',
            },
            'default_model': 'llama3',
            'requires_api_key': False,
        },
        'openai': {
            'name': 'OpenAI',
            'free': False,
            'models': {
                'gpt-4': 'gpt-4',
                'gpt-3.5-turbo': 'gpt-3.5-turbo',
            },
            'default_model': 'gpt-4',
            'requires_api_key': True,
        },
    }
    
    USE_CASES = {
        'swot_analysis': {
            'provider': 'huggingface',
            'model': 'llama3',
            'temperature': 0.7,
            'max_tokens': 2000,
        },
        'pestel_analysis': {
            'provider': 'huggingface',
            'model': 'llama3',
            'temperature': 0.7,
            'max_tokens': 2000,
        },
        'vision_mission': {
            'provider': 'huggingface',
            'model': 'mistral',
            'temperature': 0.8,
            'max_tokens': 1500,
        },
        'strategic_goals': {
            'provider': 'huggingface',
            'model': 'mistral',
            'temperature': 0.7,
            'max_tokens': 2000,
        },
        'kpi_generation': {
            'provider': 'huggingface',
            'model': 'llama3',
            'temperature': 0.6,
            'max_tokens': 3000,
        },
        'initiatives': {
            'provider': 'huggingface',
            'model': 'llama3',
            'temperature': 0.7,
            'max_tokens': 2000,
        },
    }
    
    @classmethod
    def get_default_provider(cls) -> str:
        """Get default provider (HuggingFace for free tier)"""
        return os.getenv('AI_PROVIDER', 'huggingface')
    
    @classmethod
    def get_provider_config(cls, provider: str) -> Dict[str, Any]:
        """Get configuration for a specific provider"""
        return cls.PROVIDERS.get(provider.lower(), cls.PROVIDERS['huggingface'])
    
    @classmethod
    def get_use_case_config(cls, use_case: str) -> Dict[str, Any]:
        """Get AI configuration for a specific use case (returns defensive copy)"""
        default_config = {
            'provider': cls.get_default_provider(),
            'model': 'llama3',
            'temperature': 0.7,
            'max_tokens': 2000,
        }
        
        # Get config and create defensive copy to prevent mutation
        config = cls.USE_CASES.get(use_case, default_config).copy()
        
        provider_override = os.getenv(f'AI_PROVIDER_{use_case.upper()}')
        if provider_override:
            config['provider'] = provider_override
        
        return config
    
    @classmethod
    def is_provider_available(cls, provider: str) -> bool:
        """Check if a provider is available"""
        if provider.lower() == 'openai':
            return bool(os.getenv('OPENAI_API_KEY'))
        elif provider.lower() == 'huggingface':
            return True
        return False
    
    @classmethod
    def get_available_providers(cls) -> list:
        """Get list of available providers"""
        available = []
        for provider_name in cls.PROVIDERS.keys():
            if cls.is_provider_available(provider_name):
                available.append(provider_name)
        return available
