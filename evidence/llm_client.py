"""
LLM Client Helper for RAG Research Scientist Agent.
Supports Anthropic, OpenAI, and Gemini APIs with graceful fallback when no API key is provided.
"""

import os
import json
import logging
import urllib.request
import urllib.error
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class LLMClient:
    """Lightweight LLM client supporting Anthropic, OpenAI, and Gemini APIs without external dependencies."""

    def __init__(
        self,
        anthropic_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        gemini_api_key: Optional[str] = None,
        timeout: int = 15
    ):
        self.anthropic_api_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY")
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        self.timeout = timeout

        if self.anthropic_api_key:
            self.provider = "anthropic"
            logger.info("LLMClient initialized with Anthropic API key. LLM mode active.")
        elif self.openai_api_key:
            self.provider = "openai"
            logger.info("LLMClient initialized with OpenAI/Compatible API key. LLM mode active.")
        elif self.gemini_api_key:
            self.provider = "gemini"
            logger.info("LLMClient initialized with Gemini API key. LLM mode active.")
        else:
            self.provider = None
            logger.info("No LLM API key configured. Operating in heuristic fallback mode.")

    def is_available(self) -> bool:
        """Check if any LLM API provider is configured."""
        return self.provider is not None

    def generate(self, prompt: str, system_prompt: str = "") -> Optional[str]:
        """Send prompt to configured LLM provider and return response text."""
        if not self.is_available():
            return None

        try:
            if self.provider == "anthropic":
                return self._call_anthropic(prompt, system_prompt)
            elif self.provider == "openai":
                return self._call_openai(prompt, system_prompt)
            elif self.provider == "gemini":
                return self._call_gemini(prompt, system_prompt)
        except Exception as e:
            logger.warning(f"LLM generation failed via provider '{self.provider}': {e}. Falling back to heuristic mode.")
            return None

    def _call_anthropic(self, prompt: str, system_prompt: str) -> Optional[str]:
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.anthropic_api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        payload = {
            "model": os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"),
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": prompt}]
        }
        if system_prompt:
            payload["system"] = system_prompt

        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            content_list = data.get("content", [])
            if content_list and content_list[0].get("type") == "text":
                return content_list[0].get("text", "").strip()
        return None

    def _call_openai(self, prompt: str, system_prompt: str) -> Optional[str]:
        url = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1") + "/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json"
        }
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            "messages": messages,
            "temperature": 0.3
        }

        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            choices = data.get("choices", [])
            if choices:
                return choices[0].get("message", {}).get("content", "").strip()
        return None

    def _call_gemini(self, prompt: str, system_prompt: str) -> Optional[str]:
        model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.gemini_api_key}"
        headers = {"Content-Type": "application/json"}
        
        contents = []
        if system_prompt:
            contents.append({"role": "user", "parts": [{"text": f"System Instruction: {system_prompt}\n\nTask: {prompt}"}]})
        else:
            contents.append({"role": "user", "parts": [{"text": prompt}]})

        payload = {"contents": contents}
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "").strip()
        return None
