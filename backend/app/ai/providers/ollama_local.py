import json
from typing import Any, Dict, List, Optional
import httpx
from app.ai.providers.base import BaseAIProvider
from app.core.config import settings


class OllamaLocalProvider(BaseAIProvider):
    """Provider for locally hosted open-source LLMs via Ollama or compatible vLLM server."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        chat_model: Optional[str] = None,
        embedding_model: Optional[str] = None,
        timeout: float = 60.0,
    ):
        self.base_url = (base_url or getattr(settings, "LOCAL_LLM_BASE_URL", "http://localhost:11434/v1")).rstrip("/")
        self.chat_model = chat_model or getattr(settings, "LOCAL_CHAT_MODEL", "llama3.1:8b")
        self.embedding_model = embedding_model or getattr(settings, "LOCAL_EMBEDDING_MODEL", "nomic-embed-text")
        self.timeout = timeout

    @property
    def provider_name(self) -> str:
        return "ollama_local"

    async def chat_complete(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: Optional[int] = 1500,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[str]:
        headers = {"Content-Type": "application/json"}
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
        headers = {"Content-Type": "application/json"}
        payload = {
            "model": model or self.chat_model,
            "messages": messages,
            "temperature": temperature,
            "tools": tools,
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
        headers = {"Content-Type": "application/json"}
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
