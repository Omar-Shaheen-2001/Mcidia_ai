import os
import json
import requests
from typing import Optional
from . import AIProvider


class HuggingFaceProvider(AIProvider):
    """
    HuggingFace Inference Providers (FREE with Token!)
    
    Uses HuggingFace's 2025 OpenAI-compatible API with multi-provider routing.
    Free tier includes monthly credits for all users.
    
    Supported chat-compatible models (Auto-routed to best available provider):
    - deepseek-ai/DeepSeek-V3 (Best for complex reasoning)
    - deepseek-ai/DeepSeek-R1 (Math, logic, coding with chain-of-thought)
    - meta-llama/Llama-3.3-70B-Instruct (Powerful instruction-following)
    - meta-llama/Llama-3.1-8B-Instruct (Fast, efficient, default)
    - Qwen/Qwen2.5-72B-Instruct (Multilingual, strong performance)
    - Qwen/Qwen2.5-Coder-32B-Instruct (Specialized for code generation)
    """
    
    DEFAULT_MODELS = {
        'deepseek': 'deepseek-ai/DeepSeek-V3',
        'deepseek-r1': 'deepseek-ai/DeepSeek-R1',
        'llama3-70b': 'meta-llama/Llama-3.3-70B-Instruct',
        'llama3': 'meta-llama/Llama-3.1-8B-Instruct',
        'qwen-72b': 'Qwen/Qwen2.5-72B-Instruct',
        'qwen-coder': 'Qwen/Qwen2.5-Coder-32B-Instruct',
    }
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = 'llama3',
        api_url: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        **kwargs
    ):
        super().__init__(api_key, **kwargs)
        
        self.api_key = api_key or os.getenv('HUGGINGFACE_TOKEN') or os.getenv('HUGGINGFACE_API_KEY', '')
        
        if model in self.DEFAULT_MODELS:
            self.model = self.DEFAULT_MODELS[model]
        else:
            self.model = model
        
        self.api_url = api_url or "https://router.huggingface.co/v1/chat/completions"
        
        self.headers = {
            "Content-Type": "application/json"
        }
        
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"
        
        # Store defaults from config
        self.default_temperature = temperature
        self.default_max_tokens = max_tokens
    
    def chat(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format: Optional[str] = None,
        **kwargs
    ) -> str:
        """Send chat completion using OpenAI-compatible HuggingFace API"""
        
        if not self.api_key:
            raise Exception(
                "HuggingFace token is required. Please set HUGGINGFACE_TOKEN environment variable. "
                "Get your free token at: https://huggingface.co/settings/tokens"
            )
        
        temperature = temperature if temperature is not None else self.default_temperature
        max_tokens = max_tokens if max_tokens is not None else self.default_max_tokens
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        if response_format == 'json':
            payload["response_format"] = {"type": "json_object"}
        
        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=60
            )
            
            response.raise_for_status()
            
            result = response.json()
            
            if 'choices' in result and len(result['choices']) > 0:
                return result['choices'][0]['message']['content'].strip()
            else:
                raise Exception(f"Unexpected response format: {result}")
            
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            try:
                if hasattr(e, 'response') and e.response is not None:
                    error_detail = e.response.json()
                    if 'error' in error_detail:
                        error_msg = error_detail['error'].get('message', error_msg)
            except:
                pass
            raise Exception(f"HuggingFace API error: {error_msg}")
    
    
    def get_model_name(self) -> str:
        """Return current model name"""
        return self.model
    
    def get_provider_name(self) -> str:
        """Return provider name"""
        return "HuggingFace"
