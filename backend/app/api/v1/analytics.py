import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.ai_system import ActionApproval, AgentRun, Memory
from app.models.automation import Notification
from app.models.calendar import CalendarEvent
from app.models.productivity import Goal, Habit, Task
from app.models.user import User

router = APIRouter(prefix="/analytics", tags=["Analytics & Notifications"])


@router.get("/overview")
async def get_dashboard_overview(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tasks_res = await db.execute(select(Task).where(Task.user_id == current_user.id))
    tasks = list(tasks_res.scalars().all())
    completed_tasks = sum(1 for t in tasks if t.status == "completed")
    pending_tasks = sum(1 for t in tasks if t.status in ("todo", "in_progress"))

    role_breakdown = {}
    for t in tasks:
        role_breakdown[t.role_context] = role_breakdown.get(t.role_context, 0) + 1

    goals_res = await db.execute(select(Goal).where(Goal.user_id == current_user.id))
    goals = list(goals_res.scalars().all())
    avg_goal_progress = round(sum(g.progress_percent for g in goals) / len(goals), 1) if goals else 0.0

    habits_res = await db.execute(select(Habit).where(Habit.user_id == current_user.id, Habit.is_active.is_(True)))
    habits = list(habits_res.scalars().all())
    top_streak = max((h.current_streak for h in habits), default=0)

    mem_count = (
        await db.execute(select(func.count(Memory.id)).where(Memory.user_id == current_user.id))
    ).scalar() or 0
    runs_count = (
        await db.execute(select(func.count(AgentRun.id)).where(AgentRun.user_id == current_user.id))
    ).scalar() or 0
    pending_approvals = (
        await db.execute(
            select(func.count(ActionApproval.id)).where(
                ActionApproval.user_id == current_user.id, ActionApproval.status == "pending"
            )
        )
    ).scalar() or 0
    events_count = (
        await db.execute(select(func.count(CalendarEvent.id)).where(CalendarEvent.user_id == current_user.id))
    ).scalar() or 0

    completion_rate = round((completed_tasks / len(tasks)) * 100.0, 1) if tasks else 0.0

    return {
        "tasks": {
            "total": len(tasks),
            "completed": completed_tasks,
            "pending": pending_tasks,
            "completion_rate": completion_rate,
            "by_role": role_breakdown,
        },
        "goals": {
            "total": len(goals),
            "average_progress": avg_goal_progress,
        },
        "habits": {
            "active_count": len(habits),
            "top_streak": top_streak,
        },
        "ai": {
            "memories_stored": mem_count,
            "agent_runs": runs_count,
            "pending_approvals": pending_approvals,
        },
        "calendar": {
            "scheduled_events": events_count,
        },
    }


@router.get("/notifications")
async def list_notifications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(Notification)
        .where(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(20)
    )
    return res.scalars().all()


@router.patch("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(Notification).where(Notification.id == notification_id, Notification.user_id == current_user.id)
    )
    notif = res.scalar_one_or_none()
    if not notif:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    notif.is_read = True
    await db.commit()
    return {"status": "read"}