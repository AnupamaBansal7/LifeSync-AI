from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.ai_system import ActionApproval, AgentRun, Memory
from app.models.automation import Notification
from app.models.calendar import CalendarEvent, DailyPlan
from app.models.productivity import Goal, Habit, HabitLog, Task
from app.models.user import User

router = APIRouter(prefix="/dashboard", tags=["Personalized Dashboard"])


@router.get("/summary")
async def get_role_aware_dashboard(
    role_context: Optional[str] = Query(default="personal"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    today = date.today()
    active_role = role_context or "personal"

    # Tasks query
    tasks_query = select(Task).where(Task.user_id == current_user.id)
    if active_role != "all":
        tasks_query = tasks_query.where(Task.role_context.in_([active_role, "personal"]))
    tasks_res = await db.execute(tasks_query.order_by(Task.priority.desc(), Task.due_date.asc()))
    all_tasks = tasks_res.scalars().all()

    completed_tasks = [t for t in all_tasks if t.status == "completed"]
    pending_tasks = [t for t in all_tasks if t.status in ("todo", "in_progress")]
    overdue_tasks = [t for t in pending_tasks if t.due_date and t.due_date < now]
    today_priorities = [t for t in pending_tasks if t.priority in ("urgent", "high")][:5]
    if not today_priorities:
        today_priorities = pending_tasks[:5]

    # Calendar Events
    ev_stmt = select(CalendarEvent).where(
        CalendarEvent.user_id == current_user.id,
        CalendarEvent.end_time >= now - timedelta(hours=2),
    )
    if active_role != "all":
        ev_stmt = ev_stmt.where(CalendarEvent.role_context.in_([active_role, "personal"]))
    ev_res = await db.execute(ev_stmt.order_by(CalendarEvent.start_time.asc()).limit(8))
    upcoming_events = ev_res.scalars().all()

    # Goals
    g_stmt = select(Goal).where(Goal.user_id == current_user.id).options(selectinload(Goal.milestones))
    if active_role != "all":
        g_stmt = g_stmt.where(Goal.role_context.in_([active_role, "personal"]))
    g_res = await db.execute(g_stmt.order_by(Goal.progress_percent.asc()).limit(6))
    goals = g_res.scalars().all()

    # Habits & Today's completion
    h_stmt = select(Habit).where(Habit.user_id == current_user.id, Habit.is_active.is_(True))
    if active_role != "all":
        h_stmt = h_stmt.where(Habit.role_context.in_([active_role, "personal"]))
    h_res = await db.execute(h_stmt.order_by(Habit.current_streak.desc()).limit(8))
    habits = h_res.scalars().all()

    habit_ids = [h.id for h in habits]
    today_logs_res = await db.execute(
        select(HabitLog.habit_id).where(
            HabitLog.habit_id.in_(habit_ids),
            HabitLog.log_date == today,
            HabitLog.completed.is_(True),
        )
    )
    completed_habit_ids = set(today_logs_res.scalars().all())

    habits_with_status = []
    for h in habits:
        habits_with_status.append({
            "id": str(h.id),
            "title": h.title,
            "frequency": h.frequency,
            "current_streak": h.current_streak,
            "longest_streak": h.longest_streak,
            "completed_today": h.id in completed_habit_ids,
            "role_context": h.role_context,
        })

    # Latest Daily Plan
    plan_res = await db.execute(
        select(DailyPlan).where(DailyPlan.user_id == current_user.id).order_by(DailyPlan.plan_date.desc()).limit(1)
    )
    latest_plan = plan_res.scalar_one_or_none()

    # Recent Notifications & Approvals
    notifs_res = await db.execute(
        select(Notification)
        .where(Notification.user_id == current_user.id, Notification.is_read.is_(False))
        .order_by(Notification.created_at.desc())
        .limit(5)
    )
    unread_notifications = notifs_res.scalars().all()

    approvals_res = await db.execute(
        select(ActionApproval)
        .where(ActionApproval.user_id == current_user.id, ActionApproval.status == "pending")
        .order_by(ActionApproval.created_at.desc())
        .limit(5)
    )
    pending_approvals = approvals_res.scalars().all()

    # Calculate real Daily Productivity Score (0 to 100)
    score = 50.0
    if all_tasks:
        task_ratio = len(completed_tasks) / len(all_tasks)
        score += task_ratio * 30.0
    if habits:
        habit_ratio = len(completed_habit_ids) / len(habits)
        score += habit_ratio * 20.0
    score -= min(len(overdue_tasks) * 5.0, 20.0)
    final_score = int(max(10, min(100, round(score))))

    # Role-specific tailored highlights
    role_highlights: Dict[str, Any] = {}
    if active_role == "student":
        role_highlights = {
            "title": "Academic Focus Mode",
            "study_sessions_due": sum(1 for e in upcoming_events if e.event_type in ("exam", "time_block")),
            "assignments_pending": sum(1 for t in pending_tasks if "assignment" in (t.category or "").lower() or "study" in t.title.lower()),
            "exam_alerts": [e.title for e in upcoming_events if e.event_type == "exam"],
            "focus_recommendation": "Block 90 minutes for revision of your highest priority exam topic before noon.",
        }
    elif active_role == "professional":
        role_highlights = {
            "title": "Professional Delivery Mode",
            "meetings_scheduled": sum(1 for e in upcoming_events if e.event_type == "meeting"),
            "sprint_tasks": len(pending_tasks),
            "focus_recommendation": "Protect afternoon time slots from ad-hoc syncs to maintain unbroken flow state.",
        }
    elif active_role == "entrepreneur":
        role_highlights = {
            "title": "Founder Strategic Mode",
            "active_okrs": len(goals),
            "critical_priorities": len(today_priorities),
            "focus_recommendation": "Review weekly cashflow and client roadmap milestones before delegating operational tasks.",
        }
    elif active_role == "homemaker":
        role_highlights = {
            "title": "Household & Routine Mode",
            "pending_routines": len(pending_tasks),
            "daily_wellness_habits": len(habits),
            "focus_recommendation": "Complete the morning family logistics check before moving into personal reading time.",
        }
    else:
        role_highlights = {
            "title": "Personal Life Operating System",
            "habits_to_check": len(habits) - len(completed_habit_ids),
            "active_goals": len(goals),
            "focus_recommendation": "Keep momentum with early morning habit completion and clear 1 major milestone today.",
        }

    # Timezone-aware greeting
    try:
        from zoneinfo import ZoneInfo
        user_tz_str = (
            current_user.preferences.timezone
            if current_user.preferences and current_user.preferences.timezone
            else "UTC"
        )
        user_tz = ZoneInfo(user_tz_str)
        user_now = datetime.now(user_tz)
    except Exception:
        user_now = datetime.now(timezone.utc)
        user_tz_str = "UTC"

    hour = user_now.hour
    if 5 <= hour < 12:
        greeting = "Good morning"
    elif 12 <= hour < 17:
        greeting = "Good afternoon"
    elif 17 <= hour < 22:
        greeting = "Good evening"
    else:
        greeting = "Good night"

    user_display_name = current_user.full_name if current_user.full_name and current_user.full_name.strip() else current_user.email.split('@')[0].capitalize()

    # Real Email Intelligence Summary
    from app.services.integrations_service import IntegrationsService
    email_intelligence = await IntegrationsService.get_email_intelligence_summary(db, current_user.id)

    # Real Agent Activity
    runs_res = await db.execute(
        select(AgentRun)
        .where(AgentRun.user_id == current_user.id)
        .order_by(AgentRun.created_at.desc())
        .limit(6)
    )
    recent_runs = runs_res.scalars().all()
    intent_to_agent = {
        "task_management": "TaskManagementAgent",
        "create_task": "TaskManagementAgent",
        "update_task": "TaskManagementAgent",
        "calendar_scheduling": "CalendarAgent",
        "schedule_event": "CalendarAgent",
        "email_triage": "EmailAgent",
        "draft_email": "EmailAgent",
        "send_email": "EmailAgent",
        "personal_wellness": "WellnessAgent",
        "habit_tracking": "HabitAgent",
        "goal_setting": "GoalAgent",
    }
    agent_activity = [
        {
            "id": str(r.id),
            "agent_name": intent_to_agent.get(r.detected_intent, f"{r.detected_intent.replace('_', ' ').title().replace(' ', '')}Agent"),
            "status": "Waiting for Approval" if r.status == "awaiting_approval" else r.status.capitalize(),
            "assignment": (r.user_query[:65] + "...") if len(r.user_query or "") > 65 else (r.user_query or "Agent operation"),
            "started_at": r.created_at.isoformat() if r.created_at else now.isoformat(),
            "completed_at": r.updated_at.isoformat() if (r.status in ("completed", "failed") and r.updated_at) else None,
            "result_summary": r.final_response or r.error_message or "Operating normally",
        }
        for r in recent_runs
    ]
    if not agent_activity:
        agent_activity = [
            {"id": "ag-1", "agent_name": "PersonalAssistantAgent", "status": "Idle", "assignment": "Standing by for user instructions", "started_at": now.isoformat(), "result_summary": "Ready"},
            {"id": "ag-2", "agent_name": "EmailAgent", "status": "Idle", "assignment": "Monitoring inbox for deadlines and priority updates", "started_at": now.isoformat(), "result_summary": "Ready"},
            {"id": "ag-3", "agent_name": "TaskManagementAgent", "status": "Idle", "assignment": "Tracking active task deadlines and backlog velocity", "started_at": now.isoformat(), "result_summary": "Ready"},
            {"id": "ag-4", "agent_name": "CalendarAgent", "status": "Idle", "assignment": "Analyzing daily focus blocks and schedule conflicts", "started_at": now.isoformat(), "result_summary": "Ready"},
        ]

    # Proactive Insights (Grounded in real user metrics)
    proactive_insights = []
    if overdue_tasks:
        proactive_insights.append({
            "type": "deadline",
            "urgency": "urgent",
            "title": f"{len(overdue_tasks)} task{'s are' if len(overdue_tasks) > 1 else ' is'} past deadline",
            "description": f"Prioritize '{overdue_tasks[0].title}' to keep your delivery schedule on track.",
            "action_text": "Reschedule Task",
            "tab": "tasks",
        })
    if len(today_priorities) >= 4:
        proactive_insights.append({
            "type": "workload",
            "urgency": "high",
            "title": "High task workload scheduled today",
            "description": f"You have {len(today_priorities)} high-priority tasks. Ask Sync to reprioritize or schedule focus blocks.",
            "action_text": "Optimize Schedule",
            "tab": "calendar",
        })
    if email_intelligence.get("unread_count", 0) > 0:
        proactive_insights.append({
            "type": "email",
            "urgency": "medium",
            "title": f"{email_intelligence.get('unread_count')} unread email{'s' if email_intelligence.get('unread_count') > 1 else ''} in inbox",
            "description": "Messages regarding placement drives and project reviews need attention.",
            "action_text": "Open Email Hub",
            "tab": "email",
        })
    if habits and len(completed_habit_ids) < len(habits):
        missed_count = len(habits) - len(completed_habit_ids)
        proactive_insights.append({
            "type": "habit",
            "urgency": "medium",
            "title": f"{missed_count} habit{'s' if missed_count > 1 else ''} left for today",
            "description": "Log your habits before evening to maintain your consistency streak.",
            "action_text": "View Habits",
            "tab": "habits",
        })

    return {
        "greeting": f"{greeting}, {user_display_name}",
        "user_name": user_display_name,
        "current_time_iso": user_now.isoformat(),
        "user_timezone": user_tz_str,
        "active_role": active_role,
        "productivity_score": final_score,
        "metrics": {
            "total_tasks": len(all_tasks),
            "completed_tasks": len(completed_tasks),
            "pending_tasks": len(pending_tasks),
            "overdue_tasks": len(overdue_tasks),
            "active_goals": len(goals),
            "active_habits": len(habits),
            "completed_habits_today": len(completed_habit_ids),
            "upcoming_events_count": len(upcoming_events),
            "pending_approvals_count": len(pending_approvals),
            "unread_notifications_count": len(unread_notifications),
            "unread_emails_count": email_intelligence.get("unread_count", 0),
        },
        "today_priorities": [
            {
                "id": str(t.id),
                "title": t.title,
                "priority": t.priority,
                "status": t.status,
                "due_date": t.due_date.isoformat() if t.due_date else None,
                "estimated_minutes": t.estimated_minutes,
                "role_context": t.role_context,
            }
            for t in today_priorities
        ],
        "upcoming_events": [
            {
                "id": str(e.id),
                "title": e.title,
                "event_type": e.event_type,
                "start_time": e.start_time.isoformat(),
                "end_time": e.end_time.isoformat(),
                "is_locked": e.is_locked,
                "role_context": e.role_context,
            }
            for e in upcoming_events
        ],
        "habits": habits_with_status,
        "goals": [
            {
                "id": str(g.id),
                "title": g.title,
                "progress_percent": g.progress_percent,
                "horizon": g.horizon,
                "milestones_count": len(g.milestones),
                "completed_milestones": sum(1 for m in g.milestones if m.is_completed),
            }
            for g in goals
        ],
        "daily_plan": {
            "summary": latest_plan.summary if latest_plan else "No daily plan drafted yet. Ask Sync to plan your day.",
            "blocks": latest_plan.schedule_blocks if latest_plan else [],
        },
        "role_highlights": role_highlights,
        "email_intelligence": email_intelligence,
        "agent_activity": agent_activity,
        "proactive_insights": proactive_insights,
        "recent_notifications": [
            {"id": str(n.id), "title": n.title, "message": n.message, "category": n.category, "created_at": n.created_at.isoformat()}
            for n in unread_notifications
        ],
    }
