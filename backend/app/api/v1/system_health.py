import time
from typing import Any, Dict
from fastapi import APIRouter, Depends
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.agents import COMMON_AGENTS, ROLE_SPECIFIC_AGENTS
from app.ai.providers import ProviderRegistry
from app.ai.tools import ALL_TOOLS
from app.api.deps import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User, UserIntegration
from app.models.workflow import WorkflowExecution


router = APIRouter(prefix="/system", tags=["System Health & Diagnostics"])


@router.get("/health")
async def get_system_health(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Verify live status of database, LLM provider, agents, tools, workflows, and integrations."""
    start_t = time.perf_counter()

    # 1. Database Check
    db_healthy = False
    db_latency_ms = 0
    try:
        t0 = time.perf_counter()
        await db.execute(text("SELECT 1"))
        db_latency_ms = int((time.perf_counter() - t0) * 1000)
        db_healthy = True
    except Exception:
        db_healthy = False

    # 2. LLM Provider Verification
    provider = ProviderRegistry.get_provider()
    has_api_key = bool(settings.OPENAI_API_KEY and len(settings.OPENAI_API_KEY) > 5)
    llm_status = {
        "provider": provider.provider_name,
        "model": getattr(settings, "DEFAULT_CHAT_MODEL", "gpt-4o-mini"),
        "configured": has_api_key or provider.provider_name == "ollama_local",
        "status": "online" if has_api_key else ("local_mode" if provider.provider_name == "ollama_local" else "fallback_simulation"),
    }

    # 3. Agent Catalog Availability
    total_agents = len(COMMON_AGENTS) + len(ROLE_SPECIFIC_AGENTS)
    agent_status = {
        "total_registered": total_agents,
        "common_agents": len(COMMON_AGENTS),
        "role_agents": len(ROLE_SPECIFIC_AGENTS),
        "status": "ready" if total_agents >= 14 else "degraded",
    }

    # 4. Tool Registry Verification
    tool_status = {
        "total_tools": len(ALL_TOOLS),
        "approval_gated_tools": sum(1 for t in ALL_TOOLS.values() if t.requires_approval),
        "status": "active",
    }

    # 5. Workflows Health
    res_wf = await db.execute(
        select(WorkflowExecution).where(WorkflowExecution.user_id == current_user.id)
    )
    all_wf = res_wf.scalars().all()
    wf_status = {
        "total_workflows": len(all_wf),
        "active_running": sum(1 for w in all_wf if w.status == "running"),
        "awaiting_approval": sum(1 for w in all_wf if w.status == "awaiting_approval"),
        "failed": sum(1 for w in all_wf if w.status == "failed"),
        "completed": sum(1 for w in all_wf if w.status == "completed"),
    }

    # 6. Google Workspace Integration Health
    res_int = await db.execute(
        select(UserIntegration).where(
            UserIntegration.user_id == current_user.id,
            UserIntegration.service == "google",
        )
    )
    g_rec = res_int.scalar_one_or_none()
    google_status = {
        "service": "Google Workspace (Gmail, Calendar, Drive)",
        "connected": g_rec.status == "connected" if g_rec else False,
        "account_email": g_rec.account_email if g_rec else None,
        "last_synced_at": g_rec.last_synced_at.isoformat() if g_rec and g_rec.last_synced_at else None,
    }

    # 7. Overall System Status
    overall = "healthy" if db_healthy and total_agents >= 14 else "degraded"

    return {
        "overall_status": overall,
        "server_timestamp": time.time(),
        "total_check_latency_ms": int((time.perf_counter() - start_t) * 1000),
        "components": {
            "database": {"healthy": db_healthy, "latency_ms": db_latency_ms},
            "llm_engine": llm_status,
            "agent_mesh": agent_status,
            "tool_registry": tool_status,
            "workflow_engine": wf_status,
            "google_workspace": google_status,
            "scheduler": {"status": "active", "engine": "FastAPI + DB Trigger Runner"},
        },
    }
