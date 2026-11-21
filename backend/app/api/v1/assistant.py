# Module re-export for conversational assistant endpoints
from app.api.v1.agents_memory import router as assistant_router

__all__ = ["assistant_router"]
