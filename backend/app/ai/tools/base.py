from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession


class BaseTool(ABC):
    """Abstract base class for all callable tools in LifeSync AI."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Machine identifier of the tool."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable explanation of what the tool accomplishes."""
        pass

    @property
    def requires_approval(self) -> bool:
        """Whether human-in-the-loop confirmation is recommended before applying changes."""
        return False

    @property
    def risk_level(self) -> str:
        """Risk classification: 'low', 'medium', 'high', 'destructive'."""
        return "low"

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        """JSON schema describing acceptable arguments."""
        return {}

    @abstractmethod
    async def execute(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        args: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute the tool action against the database or external services."""
        pass
