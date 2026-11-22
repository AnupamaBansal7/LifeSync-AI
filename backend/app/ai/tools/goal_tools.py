from datetime import date
from typing import Any, Dict, List
import uuid
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.ai.tools.base import BaseTool, Reversibility
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

    @property
    def reversibility(self) -> Reversibility:
        return Reversibility.REVERSIBLE

    @property
    def is_mutating(self) -> bool:
        return True

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Title of the goal"},
                "description": {"type": "string", "description": "Detailed description or motivation"},
                "horizon": {"type": "string", "enum": ["short_term", "long_term"], "default": "short_term"},
                "role_context": {"type": "string", "default": "personal"},
                "category": {"type": "string", "description": "Category such as Career, Health, Education"},
                "target_date": {"type": "string", "description": "ISO 8601 target date (YYYY-MM-DD)"},
                "milestones": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of key milestone titles",
                },
            },
            "required": ["title"],
        }

    async def dry_run(self, db: AsyncSession, user_id: uuid.UUID, args: Dict[str, Any]) -> Dict[str, Any]:
        title = args.get("title", "New Goal").strip()
        horizon = args.get("horizon", "short_term")
        milestones = args.get("milestones", [])
        return {
            "action_summary": f"Create goal: '{title}' ({horizon.replace('_', ' ').capitalize()})",
            "target_entity": "Goal",
            "before_state": {},
            "after_state": {
                "title": title,
                "description": args.get("description"),
                "horizon": horizon,
                "role_context": args.get("role_context", "personal"),
                "category": args.get("category"),
                "target_date": args.get("target_date"),
                "milestones": milestones,
            },
            "risk_level": "LOW",
            "reversibility": self.reversibility.value,
        }

    async def compensate(self, db: AsyncSession, user_id: uuid.UUID, snapshot: Dict[str, Any]) -> Dict[str, Any]:
        after = snapshot.get("after_state", {}) if isinstance(snapshot.get("after_state"), dict) else {}
        goal_id_str = (
            snapshot.get("created_goal_id")
            or snapshot.get("goal_id")
            or snapshot.get("id")
            or after.get("goal_id")
            or after.get("created_goal_id")
            or after.get("id")
        )
        if not goal_id_str:
            title = snapshot.get("title") or after.get("title")
            if title:
                res = await db.execute(select(Goal).where(Goal.title == title, Goal.user_id == user_id))
                g = res.scalar_one_or_none()
                if g:
                    goal_id_str = str(g.id)

        if goal_id_str:
            try:
                g_id = uuid.UUID(goal_id_str)
                await db.execute(delete(Milestone).where(Milestone.goal_id == g_id))
                await db.execute(delete(Goal).where(Goal.id == g_id, Goal.user_id == user_id))
                await db.commit()
                return {
                    "success": True,
                    "restored_entity_id": str(g_id),
                    "details": f"Deleted goal '{g_id}' and associated milestones to revert creation.",
                    "error": None,
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "restored_entity_id": goal_id_str,
                    "details": "Failed to rollback goal.",
                }

        return {
            "success": False,
            "error": "Goal ID not found in snapshot for compensation.",
            "restored_entity_id": None,
            "details": "Snapshot missing entity ID.",
        }

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

