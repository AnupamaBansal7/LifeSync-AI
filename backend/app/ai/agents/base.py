from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseAgent(ABC):
    """Abstract base class for all specialized and role-specific agents in LifeSync AI."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Internal unique agent identifier."""
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """User-facing friendly title."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """What this agent owns and accomplishes."""
        pass

    @property
    def category(self) -> str:
        """'common' or 'role_specific'."""
        return "common"

    @property
    def supported_roles(self) -> List[str]:
        """Roles for which this agent is active. ['*'] means all roles."""
        return ["*"]

    @property
    def allowed_tools(self) -> List[str]:
        """Tools this agent has access to call."""
        return []

    def get_system_prompt(
        self,
        user_name: str,
        role_context: str = "personal",
        context_details: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generate a tailored prompt embedding user identity, active role, and system objectives."""
        ctx_str = ""
        if context_details:
            ctx_items = [f"- {k}: {v}" for k, v in context_details.items() if v]
            if ctx_items:
                ctx_str = "\nActive User Context:\n" + "\n".join(ctx_items)

        return (
            f"You are {self.display_name}, a specialized AI agent in the LifeSync AI Personal Life OS.\n"
            f"User: {user_name}\n"
            f"Active Role Context: {role_context.upper()}\n"
            f"Your Role: {self.description}\n"
            f"{ctx_str}\n\n"
            f"Guidelines:\n"
            f"1. Respond directly, concisely, and actionably.\n"
            f"2. Never fabricate completion of actions that require application tools.\n"
            f"3. Frame plans and tasks realistically, considering available energy and schedule balance.\n"
            f"4. Maintain a supportive, highly competent, proactive tone."
        )
