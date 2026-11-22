from fastapi import APIRouter
from app.api.v1 import (
    agents,
    agents_memory,
    analytics,
    auth,
    automations,
    calendar,
    dashboard,
    email,
    goals_habits,
    integrations,
    proactive,
    projects,
    system_health,
    tasks,
    users,
    workflows,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(dashboard.router)
api_router.include_router(tasks.router)
api_router.include_router(goals_habits.router)
api_router.include_router(calendar.router)
api_router.include_router(email.router)
api_router.include_router(agents.router)
api_router.include_router(agents_memory.router)
api_router.include_router(automations.router)
api_router.include_router(analytics.router)
api_router.include_router(integrations.router)
api_router.include_router(workflows.router)
api_router.include_router(projects.router)
api_router.include_router(proactive.router)
api_router.include_router(system_health.router)




