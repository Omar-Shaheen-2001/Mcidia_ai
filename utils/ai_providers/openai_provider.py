import os
import json
from typing import Optional
from openai import OpenAI
from . import AIProvider


class OpenAIProvider(AIProvider):
    """
    OpenAI API Provider
    Supports GPT-4, GPT-3.5-Turbo, and other OpenAI models
    """
    
    DEFAULT_MODEL = "gpt-4"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4",
        temperature: float = 0.7,
        max_tokens: int = 4000,
        **kwargs
    ):
        super().__init__(api_key, **kwargs)
        
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        self.model = model
        self.client = OpenAI(api_key=self.api_key)
        
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
        """Send chat completion to OpenAI API"""
        
        # Use config defaults if not provided
        temperature = temperature if temperature is not None else self.default_temperature
        max_tokens = max_tokens if max_tokens is not None else self.default_max_tokens
        
        messages = []
        
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        request_params = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        if response_format == 'json':
            request_params["response_format"] = {"type": "json_object"}
        
        try:
            response = self.client.chat.completions.create(**request_params)
            return response.choices[0].message.content
            
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")
    
    def get_model_name(self) -> str:
        """Return current model name"""
        return self.model
    
    def get_provider_name(self) -> str:
        """Return provider name"""
        return "OpenAI"
