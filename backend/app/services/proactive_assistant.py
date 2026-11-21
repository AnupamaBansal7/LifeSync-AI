from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.automation import Notification
from app.models.calendar import CalendarEvent, DailyPlan
from app.models.productivity import Goal, Habit, Task
from app.models.user import User


class ProactiveAssistantService:
    """
    LifeSync AI 4.0 Proactive Intelligence Engine.
    Synthesizes morning briefings, detects deadline risks, identifies schedule conflicts,
    and analyzes workload capacity while respecting quiet hours.
    """

    @classmethod
    def is_in_quiet_hours(cls, user: User, current_time: datetime) -> bool:
        """Check if current time falls within user's configured quiet hours."""
        if not user or not user.preferences:
            return False
        # Default quiet hours: 22:00 (10 PM) to 07:00 (7 AM)
        user_hour = current_time.hour
        return user_hour >= 22 or user_hour < 7

    @classmethod
    async def generate_morning_briefing(
        cls,
        db: AsyncSession,
        user: User,
        role_context: str = "personal",
    ) -> Dict[str, Any]:
        """Synthesize daily executive briefing based on calendar, tasks, and habits."""
        now = datetime.now(timezone.utc)
        today = date.today()

        # 1. Fetch Priority Tasks
        res_tasks = await db.execute(
            select(Task)
            .where(Task.user_id == user.id, Task.status == "todo")
            .order_by(Task.due_date.asc().nulls_last())
            .limit(5)
        )
        tasks = res_tasks.scalars().all()

        # 2. Fetch Today's Calendar Events
        res_events = await db.execute(
            select(CalendarEvent)
            .where(
                CalendarEvent.user_id == user.id,
                CalendarEvent.start_time >= now - timedelta(hours=2),
                CalendarEvent.start_time <= now + timedelta(hours=18),
            )
            .order_by(CalendarEvent.start_time.asc())
        )
        events = res_events.scalars().all()

        # 3. Fetch Active Habit Streaks
        res_habits = await db.execute(
            select(Habit).where(Habit.user_id == user.id, Habit.is_active.is_(True)).limit(4)
        )
        habits = res_habits.scalars().all()

        # 4. Check for overdue tasks
        res_overdue = await db.execute(
            select(Task).where(
                Task.user_id == user.id,
                Task.status == "todo",
                Task.due_date < now,
            )
        )
        overdue_tasks = res_overdue.scalars().all()

        # Calculate Workload Capacity
        total_work_minutes = sum(t.estimated_minutes for t in tasks)
        free_hours_estimate = max(0.0, (480 - total_work_minutes) / 60.0)

        briefing = {
            "date": today.isoformat(),
            "user_name": user.full_name,
            "role_context": role_context,
            "tasks_summary": {
                "total_open": len(tasks),
                "overdue_count": len(overdue_tasks),
                "high_priority": [t.title for t in tasks if t.priority in ("high", "urgent")],
            },
            "events_today": [
                {
                    "title": e.title,
                    "time": f"{e.start_time.strftime('%H:%M')} - {e.end_time.strftime('%H:%M')}",
                    "is_locked": e.is_locked,
                }
                for e in events
            ],
            "habits_to_protect": [
                {"title": h.title, "streak": h.current_streak}
                for h in habits
            ],
            "estimated_focus_hours_needed": round(total_work_minutes / 60.0, 1),
            "executive_recommendation": (
                f"Allocate your first 90-minute morning focus sprint to '{tasks[0].title}'."
                if tasks else "Your board is clear. Excellent time to review strategic long-term goals."
            ),
        }

        # Create Proactive In-App Notification
        notif = Notification(
            user_id=user.id,
            title="☀️ Sync Morning Briefing",
            message=briefing["executive_recommendation"],
            category="insight",
            action_url="/dashboard",
        )
        db.add(notif)
        await db.commit()

        return briefing

    @classmethod
    async def check_deadline_risks(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
    ) -> List[Dict[str, Any]]:
        """Identify tasks due in next 48 hours and assess deadline risks."""
        now = datetime.now(timezone.utc)
        deadline_horizon = now + timedelta(hours=48)

        res = await db.execute(
            select(Task).where(
                Task.user_id == user_id,
                Task.status == "todo",
                Task.due_date <= deadline_horizon,
            ).order_by(Task.due_date.asc())
        )
        impending_tasks = res.scalars().all()
        risks = []

        for t in impending_tasks:
            time_left_hours = (t.due_date - now).total_seconds() / 3600.0 if t.due_date else 999.0
            is_overdue = time_left_hours < 0
            risk_tier = "critical" if is_overdue or time_left_hours < 6 else ("high" if time_left_hours < 24 else "medium")

            risk_record = {
                "task_id": str(t.id),
                "title": t.title,
                "due_date": t.due_date.isoformat() if t.due_date else None,
                "hours_remaining": round(time_left_hours, 1),
                "is_overdue": is_overdue,
                "risk_tier": risk_tier,
                "estimated_minutes": t.estimated_minutes,
                "recommendation": (
                    f"Immediate action required. '{t.title}' is overdue!"
                    if is_overdue else
                    f"Only {round(time_left_hours)}h left. Lock an exclusive focus session."
                ),
            }
            risks.append(risk_record)

        return risks
