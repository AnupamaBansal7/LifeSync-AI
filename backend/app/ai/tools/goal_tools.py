from datetime import date
from typing import Any, Dict
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.ai.tools.base import BaseTool
from app.models.productivity import Goal, Milestone


class CreateGoalTool(BaseTool):
    @property
    def name(self) -> str:
        return "create_goal"

    @property
    def description(self) -> str:
        return "Create a new short-term or long-term goal with optional milestones."

    @property
    def requires_approval(self) -> bool:
        return True

    @property
    def risk_level(self) -> str:
        return "low"

    async def execute(self, db: AsyncSession, user_id: uuid.UUID, args: Dict[str, Any]) -> Dict[str, Any]:
        target_d = None
        if args.get("target_date"):
            try:
                target_d = date.fromisoformat(args["target_date"])
            except ValueError:
                target_d = None

        goal = Goal(
            user_id=user_id,
            title=args.get("title", "New Goal"),
            description=args.get("description"),
            horizon=args.get("horizon", "short_term"),
            role_context=args.get("role_context", "personal"),
            category=args.get("category"),
            target_date=target_d,
            progress_percent=0.0,
            status="active",
        )
        db.add(goal)
        await db.flush()

        milestones_list = args.get("milestones", [])
        for idx, m_title in enumerate(milestones_list):
            db.add(
                Milestone(
                    goal_id=goal.id,
                    title=m_title if isinstance(m_title, str) else m_title.get("title", f"Milestone #{idx+1}"),
                    order_index=idx,
                )
            )

        await db.commit()
        await db.refresh(goal)
        return {"created_goal_id": str(goal.id), "title": goal.title, "horizon": goal.horizon}


class ListGoalsTool(BaseTool):
    @property
    def name(self) -> str:
        return "list_goals"

    @property
    def description(self) -> str:
        return "List active goals and their progress percentage."

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
                "horizon": {"type": "string", "enum": ["all", "short_term", "long_term"], "default": "all"},
            },
        }

    async def execute(self, db: AsyncSession, user_id: uuid.UUID, args: Dict[str, Any]) -> Dict[str, Any]:
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        stmt = select(Goal).where(Goal.user_id == user_id, Goal.status == "active").options(selectinload(Goal.milestones))
        horizon = args.get("horizon", "all")
        if horizon != "all":
            stmt = stmt.where(Goal.horizon == horizon)
        role = args.get("role_context")
        if role and role != "all":
            stmt = stmt.where(Goal.role_context == role)

        res = await db.execute(stmt)
        goals = res.scalars().all()
        return {
            "goals_count": len(goals),
            "goals": [
                {
                    "id": str(g.id),
                    "title": g.title,
                    "horizon": g.horizon,
                    "progress_percent": g.progress_percent,
                    "milestones_count": len(g.milestones),
                }
                for g in goals
            ],
        }

