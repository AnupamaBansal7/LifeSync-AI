from datetime import date
from typing import Any, Dict
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.ai.tools.base import BaseTool
from app.models.productivity import Habit, HabitLog


class CreateHabitTool(BaseTool):
    @property
    def name(self) -> str:
        return "create_habit"

    @property
    def description(self) -> str:
        return "Create a new recurring habit with target weekly frequency and reminder time."

    @property
    def requires_approval(self) -> bool:
        return True

    async def execute(self, db: AsyncSession, user_id: uuid.UUID, args: Dict[str, Any]) -> Dict[str, Any]:
        habit = Habit(
            user_id=user_id,
            title=args.get("title", "Daily Habit"),
            description=args.get("description"),
            role_context=args.get("role_context", "personal"),
            frequency=args.get("frequency", "daily"),
            target_days_per_week=int(args.get("target_days_per_week", 7)),
            reminder_time=args.get("reminder_time"),
            is_active=True,
        )
        db.add(habit)
        await db.commit()
        await db.refresh(habit)
        return {"created_habit_id": str(habit.id), "title": habit.title}


class LogHabitTool(BaseTool):
    @property
    def name(self) -> str:
        return "log_habit"

    @property
    def description(self) -> str:
        return "Log completion of a habit for today or a specific date, updating streaks."

    @property
    def requires_approval(self) -> bool:
        return False

    async def execute(self, db: AsyncSession, user_id: uuid.UUID, args: Dict[str, Any]) -> Dict[str, Any]:
        habit_id_str = args.get("habit_id")
        title_q = args.get("title_query")

        habit = None
        if habit_id_str:
            try:
                habit_id = uuid.UUID(habit_id_str)
                res = await db.execute(select(Habit).where(Habit.id == habit_id, Habit.user_id == user_id))
                habit = res.scalar_one_or_none()
            except ValueError:
                pass

        if not habit and title_q:
            res = await db.execute(select(Habit).where(Habit.user_id == user_id, Habit.is_active.is_(True)))
            for h in res.scalars().all():
                if title_q.lower() in h.title.lower():
                    habit = h
                    break

        if not habit:
            # Pick first active habit if user simply said "log my habit"
            res = await db.execute(select(Habit).where(Habit.user_id == user_id, Habit.is_active.is_(True)).limit(1))
            habit = res.scalar_one_or_none()

        if not habit:
            return {"error": "Habit not found to log"}

        today = date.today()
        log_res = await db.execute(select(HabitLog).where(HabitLog.habit_id == habit.id, HabitLog.log_date == today))
        existing_log = log_res.scalar_one_or_none()

        if not existing_log:
            db.add(HabitLog(habit_id=habit.id, user_id=user_id, log_date=today, completed=True))
            habit.current_streak += 1
            if habit.current_streak > habit.longest_streak:
                habit.longest_streak = habit.current_streak
            await db.commit()

        return {"habit_id": str(habit.id), "title": habit.title, "streak": habit.current_streak}


class ListHabitsTool(BaseTool):
    @property
    def name(self) -> str:
        return "list_habits"

    @property
    def description(self) -> str:
        return "List user's active habits and streak progress."

    @property
    def requires_approval(self) -> bool:
        return False

    @property
    def risk_level(self) -> str:
        return "low"

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "role_context": {"type": "string"},
            },
        }

    async def execute(self, db: AsyncSession, user_id: uuid.UUID, args: Dict[str, Any]) -> Dict[str, Any]:
        stmt = select(Habit).where(Habit.user_id == user_id, Habit.is_active.is_(True))
        role = args.get("role_context")
        if role and role != "all":
            stmt = stmt.where(Habit.role_context == role)

        res = await db.execute(stmt)
        habits = res.scalars().all()
        return {
            "habits_count": len(habits),
            "habits": [
                {
                    "id": str(h.id),
                    "title": h.title,
                    "current_streak": h.current_streak,
                    "longest_streak": h.longest_streak,
                    "frequency": h.frequency,
                }
                for h in habits
            ],
        }
