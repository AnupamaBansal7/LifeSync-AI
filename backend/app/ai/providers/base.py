from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseAIProvider(ABC):
    """Abstract base class for all LLM and embedding providers in LifeSync AI."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Unique identifier for this provider."""
        pass

    @abstractmethod
    async def chat_complete(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: Optional[int] = 1500,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[str]:
        """Generate a chat completion response given a conversation message history."""
        pass

    @abstractmethod
    async def generate_embedding(
        self,
        text: str,
        model: Optional[str] = None,
    ) -> Optional[List[float]]:
        """Generate an embedding vector for the supplied text."""
        pass

    async def chat_complete_with_tools(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
        model: Optional[str] = None,
        temperature: float = 0.2,
    ) -> Dict[str, Any]:
        """Generate a chat response and detect structured tool calls."""
        content = await self.chat_complete(messages, model=model, temperature=temperature, tools=tools)
        return {"content": content, "tool_calls": []}

