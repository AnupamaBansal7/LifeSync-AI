from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.services.seed_service import seed_default_roles


def _get_cors_origins() -> list[str]:
    if hasattr(settings, "cors_origins_list"):
        return settings.cors_origins_list
    raw = getattr(settings, "CORS_ORIGINS", ["http://localhost:5173", "http://127.0.0.1:5173"])
    if isinstance(raw, str):
        return [origin.strip() for origin in raw.split(",") if origin.strip()]
    return list(raw)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncSessionLocal() as db:
        await seed_default_roles(db)
    yield


app = FastAPI(
    title=getattr(settings, "APP_NAME", "LifeSync AI"),
    version="1.0.0",
    description="Multi-Agent Personal Life Management Operating System API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=getattr(settings, "API_V1_PREFIX", "/api/v1"))


@app.get("/", tags=["System"])
async def root():
    return {
        "message": "LifeSync AI API is running",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "healthy",
        "app": getattr(settings, "APP_NAME", "LifeSync AI"),
        "environment": getattr(settings, "ENVIRONMENT", "development"),
    }
