from datetime import date, datetime, timedelta, timezone
import logging
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.automation import Notification
from app.models.productivity import Habit, HabitLog, Task
from app.models.user import User

logger = logging.getLogger(__name__)


async def check_approaching_deadlines(ctx: dict | None = None) -> int:
    """Scan for tasks due within the next 24 hours and issue high-priority notifications."""
    now = datetime.now(timezone.utc)
    target_window = now + timedelta(hours=24)
    notifications_created = 0

    async with AsyncSessionLocal() as db:
        res = await db.execute(
            select(Task).where(
                Task.status.in_(["todo", "in_progress"]),
                Task.due_date >= now,
                Task.due_date <= target_window,
            )
        )
        tasks = res.scalars().all()

        for t in tasks:
            notif = Notification(
                user_id=t.user_id,
                title=f"Upcoming Deadline: {t.title}",
                message=f"Task is due soon ({t.due_date.strftime('%b %d at %H:%M')}). Priority: {t.priority.upper()}.",
                category="deadline",
                action_url="/tasks",
            )
            db.add(notif)
            notifications_created += 1

        if notifications_created > 0:
            await db.commit()

    logger.info("Checked approaching deadlines. Notifications created: %d", notifications_created)
    return notifications_created


async def check_habit_streaks(ctx: dict | None = None) -> int:
    """Nudge users whose active habits have not been checked off today."""
    today = date.today()
    nudges_created = 0

    async with AsyncSessionLocal() as db:
        users_res = await db.execute(select(User).where(User.is_active.is_(True), User.is_onboarded.is_(True)))
        users = users_res.scalars().all()

        for u in users:
            habits_res = await db.execute(select(Habit).where(Habit.user_id == u.id, Habit.is_active.is_(True)))
            habits = habits_res.scalars().all()
            if not habits:
                continue

            h_ids = [h.id for h in habits]
            logged_res = await db.execute(
                select(HabitLog.habit_id).where(
                    HabitLog.habit_id.in_(h_ids),
                    HabitLog.log_date == today,
                    HabitLog.completed.is_(True),
                )
            )
            logged_ids = set(logged_res.scalars().all())
            pending = [h for h in habits if h.id not in logged_ids]

            if pending:
                db.add(
                    Notification(
                        user_id=u.id,
                        title="Habit Streak Protection",
                        message=f"You have {len(pending)} pending habits today. Don't break your streak on '{pending[0].title}'!",
                        category="reminder",
                        action_url="/habits",
                    )
                )
                nudges_created += 1

        if nudges_created > 0:
            await db.commit()

    logger.info("Checked habit streaks. Nudges created: %d", nudges_created)
    return nudges_created
