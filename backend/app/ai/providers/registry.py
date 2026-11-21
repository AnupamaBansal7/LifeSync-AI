from typing import Dict, Optional
from app.ai.providers.base import BaseAIProvider
from app.ai.providers.ollama_local import OllamaLocalProvider
from app.ai.providers.openai_compat import OpenAICompatibleProvider
from app.core.config import settings


class ProviderRegistry:
    """Registry allowing runtime selection, swapping, and fallback across AI providers."""

    _instances: Dict[str, BaseAIProvider] = {}

    @classmethod
    def get_provider(cls, provider_type: Optional[str] = None) -> BaseAIProvider:
        target = provider_type or getattr(settings, "DEFAULT_AI_PROVIDER", "openai_compatible")
        target = target.lower()

        if target not in cls._instances:
            if target == "ollama_local" or target == "ollama":
                cls._instances[target] = OllamaLocalProvider()
            else:
                cls._instances[target] = OpenAICompatibleProvider()

        return cls._instances[target]

    @classmethod
    def register_provider(cls, name: str, provider: BaseAIProvider) -> None:
        cls._instances[name.lower()] = provider

    @classmethod
    def list_providers(cls) -> list[str]:
        return ["openai_compatible", "ollama_local"]


def get_default_ai_provider() -> BaseAIProvider:
    return ProviderRegistry.get_provider()
