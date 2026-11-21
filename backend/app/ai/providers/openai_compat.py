import json
from typing import Any, Dict, List, Optional
import httpx
from app.ai.providers.base import BaseAIProvider
from app.core.config import settings


class OpenAICompatibleProvider(BaseAIProvider):
    """Provider for OpenAI, Groq, DeepSeek, Together AI, vLLM, and any OpenAI-compatible API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        chat_model: Optional[str] = None,
        embedding_model: Optional[str] = None,
        timeout: float = 30.0,
    ):
        self.api_key = api_key or getattr(settings, "OPENAI_API_KEY", "")
        self.base_url = (base_url or getattr(settings, "OPENAI_BASE_URL", "https://api.openai.com/v1")).rstrip("/")
        self.chat_model = chat_model or getattr(settings, "DEFAULT_CHAT_MODEL", "gpt-4o-mini")
        self.embedding_model = embedding_model or getattr(settings, "DEFAULT_EMBEDDING_MODEL", "text-embedding-3-small")
        self.timeout = timeout

    @property
    def provider_name(self) -> str:
        return "openai_compatible"

    async def chat_complete(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: Optional[int] = 1500,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[str]:
        if not self.api_key or not self.api_key.strip() or "your-key" in self.api_key:
            return None

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload: Dict[str, Any] = {
            "model": model or self.chat_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if tools:
            payload["tools"] = tools

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                if response.status_code == 200:
                    data = response.json()
                    choices = data.get("choices", [])
                    if choices:
                        return choices[0].get("message", {}).get("content")
        except Exception:
            return None
        return None

    async def chat_complete_with_tools(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
        model: Optional[str] = None,
        temperature: float = 0.2,
    ) -> Dict[str, Any]:
        if not self.api_key or not self.api_key.strip() or "your-key" in self.api_key:
            return {"content": None, "tool_calls": []}

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model or self.chat_model,
            "messages": messages,
            "temperature": temperature,
            "tools": tools,
            "tool_choice": "auto",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                if response.status_code == 200:
                    data = response.json()
                    choices = data.get("choices", [])
                    if choices:
                        msg = choices[0].get("message", {})
                        content = msg.get("content")
                        tool_calls = []
                        for tc in msg.get("tool_calls", []):
                            fn = tc.get("function", {})
                            name = fn.get("name")
                            args_raw = fn.get("arguments", "{}")
                            if isinstance(args_raw, str):
                                try:
                                    args = json.loads(args_raw)
                                except Exception:
                                    args = {}
                            else:
                                args = args_raw
                            tool_calls.append({"name": name, "arguments": args})
                        return {"content": content, "tool_calls": tool_calls}
        except Exception:
            pass
        return {"content": None, "tool_calls": []}


    async def generate_embedding(
        self,
        text: str,
        model: Optional[str] = None,
    ) -> Optional[List[float]]:
        if not self.api_key or not self.api_key.strip() or "your-key" in self.api_key:
            return None

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model or self.embedding_model,
            "input": text[:8000],
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/embeddings",
                    headers=headers,
                    json=payload,
                )
                if response.status_code == 200:
                    data = response.json()
                    items = data.get("data", [])
                    if items and "embedding" in items[0]:
                        return items[0]["embedding"]
        except Exception:
            return None
        return None
