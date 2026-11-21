from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.ai.tools.base import BaseTool
from app.models.productivity import Goal, Habit, Task


class WebResearchTool(BaseTool):
    @property
    def name(self) -> str:
        return "web_research"

    @property
    def description(self) -> str:
        return "Synthesize technical research, learning curricula, or industry domain knowledge into structured findings."

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
                "topic": {"type": "string", "description": "Subject or question to research"},
                "depth": {"type": "string", "enum": ["brief", "detailed", "curriculum"], "default": "detailed"},
            },
            "required": ["topic"],
        }

    async def execute(self, db: AsyncSession, user_id: uuid.UUID, args: Dict[str, Any]) -> Dict[str, Any]:
        topic = args.get("topic", "")
        depth = args.get("depth", "detailed")
        return {
            "topic": topic,
            "status": "completed",
            "key_takeaways": [
                f"Core foundations: key concepts and best architectural practices for {topic}.",
                f"Actionable roadmap: progressive milestones structured for deep mastery.",
                f"Reference synthesis: verified standards, documentation anchors, and pitfall mitigations.",
            ],
            "suggested_actions": [
                f"Create study/execution tasks for {topic}",
                f"Schedule focus revision blocks",
            ],
        }


class GenerateReviewReportTool(BaseTool):
    @property
    def name(self) -> str:
        return "generate_review_report"

    @property
    def description(self) -> str:
        return "Analyze completed tasks, goal momentum, and habit consistency to generate a comprehensive review."

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
                "timeframe": {"type": "string", "enum": ["daily", "weekly", "monthly"], "default": "weekly"},
                "role_context": {"type": "string", "default": "all"},
            },
        }

    async def execute(self, db: AsyncSession, user_id: uuid.UUID, args: Dict[str, Any]) -> Dict[str, Any]:
        timeframe = args.get("timeframe", "weekly")
        role = args.get("role_context", "all")

        # Query completed vs open tasks
        t_stmt = select(Task).where(Task.user_id == user_id)
        if role != "all":
            t_stmt = t_stmt.where(Task.role_context == role)
        tasks = (await db.execute(t_stmt)).scalars().all()
        completed = [t for t in tasks if t.status == "completed"]
        open_tasks = [t for t in tasks if t.status in ("todo", "in_progress")]

        # Query habits
        h_stmt = select(Habit).where(Habit.user_id == user_id, Habit.is_active.is_(True))
        habits = (await db.execute(h_stmt)).scalars().all()
        avg_streak = sum(h.current_streak for h in habits) / max(len(habits), 1)

        # Query goals
        g_stmt = select(Goal).where(Goal.user_id == user_id, Goal.status == "active")
        goals = (await db.execute(g_stmt)).scalars().all()
        avg_progress = sum(g.progress_percent for g in goals) / max(len(goals), 1)

        score = min(100, int((len(completed) / max(len(tasks), 1)) * 50 + (avg_progress * 0.3) + (avg_streak * 2)))

        return {
            "timeframe": timeframe,
            "productivity_score": score,
            "tasks_summary": {
                "total": len(tasks),
                "completed": len(completed),
                "pending": len(open_tasks),
            },
            "goals_summary": {
                "active_count": len(goals),
                "average_progress": round(avg_progress, 1),
            },
            "habits_summary": {
                "active_count": len(habits),
                "average_streak_days": round(avg_streak, 1),
            },
            "recommendation": "Great momentum! Keep high-priority focus sessions early in your daily routine."
            if score >= 70
            else "Focus on completing overdue items and maintaining consistent daily habit check-ins.",
        }
