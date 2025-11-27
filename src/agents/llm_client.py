"""LLM Client for agent reasoning."""
import os
import json
from typing import Dict, Any, Optional


class LLMClient:
    """Client for LLM-powered agent reasoning."""
    
    def __init__(self, model: str = "gpt-4o-mini", temperature: float = 0.7):
        self.model = model
        self.temperature = temperature
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.client = None
        
        if self.api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
            except ImportError:
                print("⚠️  OpenAI package not installed. Using rule-based fallback.")
    
    def generate(self, prompt: str, system_prompt: str = None, 
                 response_format: str = "json") -> Dict[str, Any]:
        """Generate response from LLM."""
        if not self.client:
            return self._fallback_response()
        
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                response_format={"type": "json_object"} if response_format == "json" else None
            )
            
            content = response.choices[0].message.content
            
            if response_format == "json":
                return json.loads(content)
            return {"response": content}
            
        except Exception as e:
            print(f"⚠️  LLM error: {e}. Using rule-based fallback.")
            return self._fallback_response()
    
    def _fallback_response(self) -> Dict[str, Any]:
        """Fallback response when LLM is unavailable."""
        return {
            "status": "fallback",
            "message": "Using rule-based reasoning"
        }
    
    def is_available(self) -> bool:
        """Check if LLM is available."""
        return self.client is not None
