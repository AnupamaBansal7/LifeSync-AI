# Module re-export for clean route organization
from app.api.v1.goals_habits import router as habits_router

__all__ = ["habits_router"]
