from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User, UserIntegration
from app.services.integrations_service import IntegrationsService


router = APIRouter(prefix="/integrations", tags=["Ecosystem Integrations"])


class IntegrationStatusOut(BaseModel):
    id: Optional[str] = None
    service: str
    name: str
    category: str
    description: str
    status: str  # "connected" | "disconnected" | "error"
    account_email: Optional[str] = None
    scopes: List[str] = []
    last_synced_at: Optional[str] = None
    details: str
    auth_url: Optional[str] = None


class OAuthCallbackRequest(BaseModel):
    code: str
    state: Optional[str] = None


class MockConnectRequest(BaseModel):
    service: str
    account_email: Optional[str] = "connected-user@gmail.com"


KNOWN_INTEGRATIONS = [
    {
        "service": "google",
        "name": "Google Workspace & Gmail",
        "category": "Communication & Calendar",
        "description": "Send emails, manage drafts, inspect inbox messages, and sync calendar events.",
        "details": "Requires Gmail and Google Calendar OAuth permissions.",
    },
    {
        "service": "ollama",
        "name": "Ollama Local LLM Endpoint",
        "category": "AI Engine",
        "description": "Run offline open-source models (Llama 3.1, Mistral, Qwen) with zero external telemetry.",
        "details": f"Configured at {getattr(settings, 'LOCAL_LLM_BASE_URL', 'http://localhost:11434/v1')}",
    },
    {
        "service": "openai_compatible",
        "name": "Cloud AI Provider (OpenAI / Groq)",
        "category": "AI Engine",
        "description": "OpenAI, Groq, DeepSeek, or vLLM endpoint for fast cloud reasoning.",
        "details": f"Configured endpoint: {getattr(settings, 'OPENAI_BASE_URL', 'https://api.openai.com/v1')}",
    },
    {
        "service": "github",
        "name": "GitHub Repositories",
        "category": "Developer Tools",
        "description": "Sync pull request deadlines, issue milestones, and sprint backlog tasks.",
        "details": "Imports developer milestones into active tasks.",
    },
    {
        "service": "notion",
        "name": "Notion Workspace",
        "category": "Knowledge Base",
        "description": "Vectorize Notion documents into pgvector RAG memory.",
        "details": "RAG chunking and semantic query pipeline.",
    },
]


@router.get("", response_model=List[IntegrationStatusOut])
async def list_integrations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(UserIntegration).where(UserIntegration.user_id == current_user.id)
    res = await db.execute(stmt)
    records = {r.service: r for r in res.scalars().all()}

    output = []
    for ki in KNOWN_INTEGRATIONS:
        srv = ki["service"]
        rec = records.get(srv)

        # Provider defaults
        if srv == "ollama":
            current_status = "connected"
        elif srv == "openai_compatible":
            has_key = bool(settings.OPENAI_API_KEY and len(settings.OPENAI_API_KEY) > 5)
            current_status = "connected" if has_key else "disconnected"
        else:
            current_status = rec.status if rec else "disconnected"

        auth_link = None
        if srv == "google" and current_status != "connected":
            auth_link = IntegrationsService.get_google_auth_url(state=str(current_user.id))

        output.append(
            IntegrationStatusOut(
                id=str(rec.id) if rec else None,
                service=srv,
                name=ki["name"],
                category=ki["category"],
                description=ki["description"],
                status=current_status,
                account_email=rec.account_email if rec else None,
                scopes=rec.scopes if rec else [],
                last_synced_at=rec.last_synced_at.isoformat() if rec and rec.last_synced_at else None,
                details=ki["details"],
                auth_url=auth_link,
            )
        )
    return output


@router.post("/google/auth-url")
async def get_google_auth_url(
    current_user: User = Depends(get_current_user),
):
    url = IntegrationsService.get_google_auth_url(state=str(current_user.id))
    return {"auth_url": url}


@router.post("/google/callback")
async def handle_google_oauth_callback(
    payload: OAuthCallbackRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await IntegrationsService.exchange_google_code(
        db=db,
        user_id=current_user.id,
        code=payload.code,
    )
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "OAuth exchange failed"),
        )
    return result


@router.post("/mock-connect")
async def mock_connect(
    payload: MockConnectRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Allows instant connection in dev mode without external OAuth redirects."""
    rec = await IntegrationsService.get_or_create_integration(db, current_user.id, payload.service)
    rec.status = "connected"
    rec.account_email = payload.account_email
    rec.access_token = f"mock-token-{uuid.uuid4().hex[:12]}"
    rec.last_synced_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(rec)
    return {"success": True, "service": rec.service, "status": rec.status, "email": rec.account_email}


@router.post("/{service}/disconnect")
async def disconnect_integration(
    service: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    success = await IntegrationsService.disconnect(db, current_user.id, service)
    return {"success": success, "service": service, "status": "disconnected"}


@router.post("/{service}/sync")
async def sync_integration(
    service: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rec = await IntegrationsService.get_or_create_integration(db, current_user.id, service)
    rec.last_synced_at = datetime.now(timezone.utc)
    if service == "google":
        await IntegrationsService.sync_google_tasks_with_db(db, current_user.id)
    await db.commit()
    return {"success": True, "service": service, "last_synced_at": rec.last_synced_at.isoformat()}


@router.get("/google/emails")
async def get_google_emails(
    q: str = "",
    max_results: int = 5,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await IntegrationsService.search_emails(db, current_user.id, query=q, max_results=max_results)


@router.get("/google/calendar")
async def get_google_calendar(
    time_min: Optional[str] = None,
    time_max: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await IntegrationsService.list_google_calendar_events(db, current_user.id, time_min=time_min, time_max=time_max)


@router.get("/google/drive")
async def get_google_drive(
    q: str = "",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await IntegrationsService.search_drive_files(db, current_user.id, query=q)
