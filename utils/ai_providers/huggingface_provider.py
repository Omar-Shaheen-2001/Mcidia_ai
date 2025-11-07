import os
import json
import requests
from typing import Optional
from . import AIProvider


class HuggingFaceProvider(AIProvider):
    """
    HuggingFace Inference API Provider (100% FREE!)
    
    Supports models like:
    - meta-llama/Meta-Llama-3.1-8B-Instruct (Latest Llama 3.1)
    - mistralai/Mistral-7B-Instruct-v0.3 (Latest with function calling)
    - mistralai/Mixtral-8x7B-Instruct-v0.1
    """
    
    DEFAULT_MODELS = {
        'llama3': 'meta-llama/Meta-Llama-3.1-8B-Instruct',
        'mistral': 'mistralai/Mistral-7B-Instruct-v0.3',
        'mixtral': 'mistralai/Mixtral-8x7B-Instruct-v0.1',
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
        
        self.api_key = api_key or os.getenv('HUGGINGFACE_API_KEY', '')
        
        if model in self.DEFAULT_MODELS:
            self.model = self.DEFAULT_MODELS[model]
        else:
            self.model = model
        
        if api_url:
            self.api_url = api_url
        else:
            self.api_url = f"https://api-inference.huggingface.co/models/{self.model}"
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}" if self.api_key else "",
            "Content-Type": "application/json"
        }
        
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
        """Send chat completion to HuggingFace Inference API"""
        
        # Use config defaults if not provided
        temperature = temperature if temperature is not None else self.default_temperature
        max_tokens = max_tokens if max_tokens is not None else self.default_max_tokens
        
        full_prompt = self._build_prompt(prompt, system_prompt)
        
        payload = {
            "inputs": full_prompt,
            "parameters": {
                "temperature": temperature,
                "max_new_tokens": max_tokens,
                "return_full_text": False,
                "do_sample": True,
                "top_p": 0.9,
            }
        }
        
        if response_format == 'json':
            payload["parameters"]["format"] = "json"
        
        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 503:
                return self._handle_model_loading(payload)
            
            response.raise_for_status()
            
            result = response.json()
            
            if isinstance(result, list) and len(result) > 0:
                generated_text = result[0].get('generated_text', '')
            elif isinstance(result, dict):
                generated_text = result.get('generated_text', '')
            else:
                generated_text = str(result)
            
            return generated_text.strip()
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"HuggingFace API error: {str(e)}")
    
    def _build_prompt(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Build prompt in chat format for Llama3/Mistral models"""
        
        if 'llama' in self.model.lower():
            if system_prompt:
                return f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{system_prompt}<|eot_id|><|start_header_id|>user<|end_header_id|>\n\n{prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"
            else:
                return f"<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\n{prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"
        
        elif 'mistral' in self.model.lower():
            if system_prompt:
                return f"<s>[INST] {system_prompt}\n\n{prompt} [/INST]"
            else:
                return f"<s>[INST] {prompt} [/INST]"
        
        else:
            if system_prompt:
                return f"{system_prompt}\n\n{prompt}"
            else:
                return prompt
    
    def _handle_model_loading(self, payload: dict, max_retries: int = 3) -> str:
        """Handle model loading state (503 error)"""
        import time
        
        for i in range(max_retries):
            time.sleep(20)
            
            try:
                response = requests.post(
                    self.api_url,
                    headers=self.headers,
                    json=payload,
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if isinstance(result, list) and len(result) > 0:
                        if isinstance(result[0], dict):
                            return result[0].get('generated_text', '').strip()
                    elif isinstance(result, dict):
                        return result.get('generated_text', '').strip()
                    
            except Exception:
                continue
        
        raise Exception(
            "Model is loading. Please try again in a few moments. "
            "HuggingFace free tier models may take 20-30 seconds to wake up."
        )
    
    def get_model_name(self) -> str:
        """Return current model name"""
        return self.model
    
    def get_provider_name(self) -> str:
        """Return provider name"""
        return "HuggingFace"
