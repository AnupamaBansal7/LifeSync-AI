from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai.agents import COMMON_AGENTS, ROLE_SPECIFIC_AGENTS
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.ai_system import ActionApproval, AgentRun
from app.models.calendar import CalendarEvent
from app.models.productivity import Task
from app.models.user import User
from app.schemas.ai import AgentGreetingResponse

router = APIRouter(prefix="/agents", tags=["AI Agents Ecosystem"])


@router.get("/greeting", response_model=AgentGreetingResponse)
async def get_proactive_greeting(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generates a personalized, proactive greeting with live user tasks and next calendar commitment."""
    now = datetime.now(timezone.utc)
    end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=999999)

    user_name = (
        current_user.full_name.split()[0]
        if current_user.full_name and current_user.full_name.strip()
        else current_user.email.split("@")[0].capitalize()
    )

    # 1. Count tasks due today or open
    stmt_tasks = select(func.count(Task.id)).where(
        Task.user_id == current_user.id,
        Task.status.in_(["todo", "in_progress"]),
        Task.due_date <= end_of_day + timedelta(days=1),
    )
    res_tasks = await db.execute(stmt_tasks)
    pending_tasks_count = res_tasks.scalar() or 0

    # 2. Find next upcoming calendar event
    stmt_event = (
        select(CalendarEvent)
        .where(
            CalendarEvent.user_id == current_user.id,
            CalendarEvent.end_time >= now,
        )
        .order_by(CalendarEvent.start_time.asc())
        .limit(1)
    )
    res_event = await db.execute(stmt_event)
    next_event_obj = res_event.scalar_one_or_none()

    next_event_str: Optional[str] = None
    if next_event_obj:
        start_local = next_event_obj.start_time.strftime("%I:%M %p")
        next_event_str = f"'{next_event_obj.title}' at {start_local}"

    # 3. Formulate natural spoken greeting text
    if pending_tasks_count > 0 and next_event_str:
        greeting_text = (
            f"Hello {user_name}! You have {pending_tasks_count} tasks due today, and {next_event_str}. "
            f"What would you like my help with, and how can I assist you?"
        )
    elif pending_tasks_count > 0:
        greeting_text = (
            f"Hello {user_name}! You have {pending_tasks_count} tasks due today. "
            f"What would you like my help with, and how can I assist you?"
        )
    elif next_event_str:
        greeting_text = (
            f"Hello {user_name}! You have {next_event_str} coming up. "
            f"What would you like my help with, and how can I assist you?"
        )
    else:
        greeting_text = (
            f"Hello {user_name}! All your tasks are completed for today. "
            f"What would you like my help with, and how can I assist you?"
        )

    quick_suggestions = [
        "Plan my day",
        "Add a new task",
        "Review today's deadlines",
    ]

    return AgentGreetingResponse(
        greeting_text=greeting_text,
        user_name=user_name,
        pending_tasks_count=pending_tasks_count,
        next_event=next_event_str,
        quick_suggestions=quick_suggestions,
    )


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
