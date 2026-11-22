from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession


class Reversibility(str, Enum):
    REVERSIBLE = "REVERSIBLE"
    DELAYED_UNDO = "DELAYED_UNDO"
    IRREVERSIBLE = "IRREVERSIBLE"


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
    def reversibility(self) -> Reversibility:
        """Tool reversibility contract: REVERSIBLE, DELAYED_UNDO, or IRREVERSIBLE."""
        return Reversibility.REVERSIBLE

    @property
    def is_mutating(self) -> bool:
        """Whether this tool modifies persistent state, database entities, or external systems."""
        return False

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

    async def dry_run(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        args: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Simulate the action without committing any mutations.
        Returns a structured DryRunDiff preview:
        {
            "action_summary": str,
            "target_entity": str,
            "before_state": dict,
            "after_state": dict,
            "risk_level": "LOW" | "MEDIUM" | "HIGH",
            "reversibility": "REVERSIBLE" | "DELAYED_UNDO" | "IRREVERSIBLE"
        }
        """
        return {
            "action_summary": f"Execute {self.name}",
            "target_entity": self.name,
            "before_state": {},
            "after_state": dict(args),
            "risk_level": self.risk_level.upper(),
            "reversibility": self.reversibility.value,
        }

    async def compensate(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        snapshot: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Reverse/rollback the mutation using pre-execution or post-execution snapshot.
        Returns:
        {
            "success": bool,
            "restored_entity_id": Optional[str],
            "details": str,
            "error": Optional[str]
        }
        """
        return {
            "success": False,
            "error": f"Tool '{self.name}' does not implement compensating rollback logic.",
            "restored_entity_id": None,
            "details": "Rollback not supported.",
        }
