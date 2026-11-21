# Module re-export for clean route organization
from app.api.v1.agents_memory import router as memory_router

__all__ = ["memory_router"]
