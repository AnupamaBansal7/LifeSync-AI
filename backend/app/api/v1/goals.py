# Module re-export for clean route organization
from app.api.v1.goals_habits import router as goals_router

__all__ = ["goals_router"]
