from typing import Any, Dict, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai.agents import COMMON_AGENTS, ROLE_SPECIFIC_AGENTS
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.ai_system import ActionApproval, AgentRun
from app.models.user import User

router = APIRouter(prefix="/agents", tags=["AI Agents Ecosystem"])


@router.get("/catalog")
async def get_agent_catalog(
    current_user: User = Depends(get_current_user),
):
    """Retrieve full catalog of Common and Role-Specific agents available in LifeSync OS."""
    catalog = []
    for a in COMMON_AGENTS:
        catalog.append({
            "name": a.name,
            "display_name": a.display_name,
            "description": a.description,
            "category": "common",
            "supported_roles": a.supported_roles,
            "allowed_tools": a.allowed_tools,
            "is_active": True,
        })

    for a in ROLE_SPECIFIC_AGENTS:
        catalog.append({
            "name": a.name,
            "display_name": a.display_name,
            "description": a.description,
            "category": "role_specific",
            "supported_roles": a.supported_roles,
            "allowed_tools": a.allowed_tools,
            "is_active": True,
        })

    return catalog


@router.get("/runs")
async def get_agent_runs(
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List recent agent execution runs with steps, latency, and status."""
    stmt = (
        select(AgentRun)
        .where(AgentRun.user_id == current_user.id)
        .options(selectinload(AgentRun.steps), selectinload(AgentRun.approvals))
        .order_by(AgentRun.created_at.desc())
        .limit(limit)
    )
    res = await db.execute(stmt)
    runs = res.scalars().all()

    output: List[Dict[str, Any]] = []
    for r in runs:
        output.append({
            "id": str(r.id),
            "user_query": r.user_query,
            "detected_intent": r.detected_intent,
            "status": r.status,
            "final_response": r.final_response,
            "latency_ms": r.latency_ms,
            "created_at": r.created_at.isoformat(),
            "steps": [
                {
                    "step_order": s.step_order,
                    "agent_name": s.agent_name,
                    "tool_name": s.tool_name,
                    "status": s.status,
                    "input_summary": s.input_summary,
                    "output_summary": s.output_summary,
                }
                for s in r.steps
            ],
            "approvals": [
                {
                    "id": str(ap.id),
                    "action_summary": ap.action_summary,
                    "tool_name": ap.tool_name,
                    "status": ap.status,
                }
                for ap in r.approvals
            ],
        })
    return output
