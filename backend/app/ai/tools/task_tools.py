from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
import uuid
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.ai.tools.base import BaseTool
from app.models.productivity import Task, TaskHistory


class CreateTaskTool(BaseTool):
    @property
    def name(self) -> str:
        return "create_task"

    @property
    def description(self) -> str:
        return "Create a new task with title, role context, priority, estimated duration, and due date."

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
                "title": {"type": "string", "description": "Title of the task"},
                "description": {"type": "string", "description": "Optional notes or details"},
                "role_context": {"type": "string", "default": "personal"},
                "priority": {"type": "string", "enum": ["low", "medium", "high", "urgent"], "default": "medium"},
                "estimated_minutes": {"type": "integer", "default": 30},
                "due_date": {"type": "string", "description": "ISO 8601 datetime or null"},
                "category": {"type": "string"},
                "tags": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["title"],
        }

    async def execute(self, db: AsyncSession, user_id: uuid.UUID, args: Dict[str, Any]) -> Dict[str, Any]:
        due_dt = None
        if args.get("due_date"):
            try:
                due_dt = datetime.fromisoformat(args["due_date"])
            except ValueError:
                due_dt = datetime.now(timezone.utc) + timedelta(days=1)

        task = Task(
            user_id=user_id,
            title=args.get("title", "Untitled Task").strip(),
            description=args.get("description"),
            role_context=args.get("role_context", "personal"),
            priority=args.get("priority", "medium"),
            estimated_minutes=int(args.get("estimated_minutes", 30)),
            due_date=due_dt,
            category=args.get("category"),
            tags=args.get("tags", []),
            created_by_agent="TaskArchitectAgent",
        )
        db.add(task)
        await db.flush()

        db.add(
            TaskHistory(
                task_id=task.id,
                user_id=user_id,
                action="created_by_agent",
                changes={"title": task.title, "priority": task.priority},
                actor="agent:TaskArchitectAgent",
            )
        )
        await db.commit()
        await db.refresh(task)
        return {
            "created_task_id": str(task.id),
            "title": task.title,
            "priority": task.priority,
            "status": task.status,
            "due_date": task.due_date.isoformat() if task.due_date else None,
        }


class BatchCreateTasksTool(BaseTool):
    @property
    def name(self) -> str:
        return "batch_create_tasks"

    @property
    def description(self) -> str:
        return "Create multiple tasks simultaneously from a single plan or to-do list."

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
                "tasks": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "priority": {"type": "string", "default": "medium"},
                            "estimated_minutes": {"type": "integer", "default": 30},
                            "due_date": {"type": "string"},
                            "role_context": {"type": "string", "default": "personal"},
                        },
                        "required": ["title"],
                    },
                }
            },
            "required": ["tasks"],
        }

    async def execute(self, db: AsyncSession, user_id: uuid.UUID, args: Dict[str, Any]) -> Dict[str, Any]:
        task_items = args.get("tasks", [])
        created_records = []
        for item in task_items:
            title = item.get("title", "").strip()
            if not title:
                continue
            due_dt = None
            if item.get("due_date"):
                try:
                    due_dt = datetime.fromisoformat(item["due_date"])
                except ValueError:
                    due_dt = datetime.now(timezone.utc) + timedelta(days=1)

            t = Task(
                user_id=user_id,
                title=title,
                role_context=item.get("role_context", "personal"),
                priority=item.get("priority", "medium"),
                estimated_minutes=int(item.get("estimated_minutes", 30)),
                due_date=due_dt,
                created_by_agent="TaskArchitectAgent",
            )
            db.add(t)
            await db.flush()
            created_records.append({"id": str(t.id), "title": t.title, "priority": t.priority})

        await db.commit()
        return {"created_count": len(created_records), "tasks": created_records}


class UpdateTaskStatusTool(BaseTool):
    @property
    def name(self) -> str:
        return "update_task_status"

    @property
    def description(self) -> str:
        return "Update task status (todo, in_progress, completed, blocked). Can find task by task_id or title query."

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
                "task_id": {"type": "string", "description": "UUID of the task"},
                "title_query": {"type": "string", "description": "Title keywords if task_id not known"},
                "status": {"type": "string", "enum": ["todo", "in_progress", "completed", "blocked"], "default": "completed"},
                "due_date": {"type": "string", "description": "ISO 8601 datetime to reschedule task to"},
            },
        }


    async def execute(self, db: AsyncSession, user_id: uuid.UUID, args: Dict[str, Any]) -> Dict[str, Any]:
        task_id_str = args.get("task_id")
        title_q = args.get("title_query")
        new_status = args.get("status", "completed")

        task = None
        if task_id_str:
            try:
                task_id = uuid.UUID(task_id_str)
                res = await db.execute(select(Task).where(Task.id == task_id, Task.user_id == user_id))
                task = res.scalar_one_or_none()
            except ValueError:
                pass

        if not task and title_q:
            clean_q = title_q.strip().lower()
            res = await db.execute(select(Task).where(Task.user_id == user_id))
            all_tasks = res.scalars().all()
            for t in all_tasks:
                if clean_q in t.title.lower() or t.title.lower() in clean_q:
                    task = t
                    break

        if not task:
            return {"error": f"Task not found matching '{task_id_str or title_q}'"}

        old_status = task.status
        changes: Dict[str, Any] = {}
        if "status" in args:
            task.status = new_status
            if new_status == "completed":
                task.completed_at = datetime.now(timezone.utc)
            changes["status"] = {"old": old_status, "new": new_status}

        if args.get("due_date"):
            old_due = task.due_date.isoformat() if task.due_date else None
            try:
                task.due_date = datetime.fromisoformat(args["due_date"])
                changes["due_date"] = {"old": old_due, "new": task.due_date.isoformat()}
            except ValueError:
                pass

        db.add(
            TaskHistory(
                task_id=task.id,
                user_id=user_id,
                action="update",
                changes=changes,
                actor="agent",
            )
        )
        await db.commit()
        return {
            "task_id": str(task.id),
            "title": task.title,
            "new_status": task.status,
            "due_date": task.due_date.isoformat() if task.due_date else None,
            "previous_status": old_status,
        }



class DeleteTaskTool(BaseTool):
    @property
    def name(self) -> str:
        return "delete_task"

    @property
    def description(self) -> str:
        return "Delete a task permanently. Higher-risk action requiring user confirmation."

    @property
    def requires_approval(self) -> bool:
        return True

    @property
    def risk_level(self) -> str:
        return "high"

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "UUID of the task to delete"},
                "title_query": {"type": "string", "description": "Title query of the task"},
            },
        }

    async def execute(self, db: AsyncSession, user_id: uuid.UUID, args: Dict[str, Any]) -> Dict[str, Any]:
        task_id_str = args.get("task_id")
        title_q = args.get("title_query")

        task = None
        if task_id_str:
            try:
                task_id = uuid.UUID(task_id_str)
                res = await db.execute(select(Task).where(Task.id == task_id, Task.user_id == user_id))
                task = res.scalar_one_or_none()
            except ValueError:
                pass

        if not task and title_q:
            res = await db.execute(select(Task).where(Task.user_id == user_id))
            for t in res.scalars().all():
                if title_q.lower() in t.title.lower():
                    task = t
                    break

        if not task:
            return {"error": "Task to delete not found"}

        title = task.title
        tid = str(task.id)
        await db.delete(task)
        await db.commit()
        return {"deleted": True, "task_id": tid, "title": title}


class ListTasksTool(BaseTool):
    @property
    def name(self) -> str:
        return "list_tasks"

    @property
    def description(self) -> str:
        return "Retrieve user tasks filtered by status (todo, in_progress, completed, overdue) and role."

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
                "status": {"type": "string", "enum": ["all", "todo", "in_progress", "completed", "overdue"], "default": "todo"},
                "role_context": {"type": "string"},
                "limit": {"type": "integer", "default": 10},
            },
        }

    async def execute(self, db: AsyncSession, user_id: uuid.UUID, args: Dict[str, Any]) -> Dict[str, Any]:
        status_filter = args.get("status", "todo")
        role_context = args.get("role_context")
        limit = args.get("limit", 10)

        stmt = select(Task).where(Task.user_id == user_id)
        if role_context and role_context != "all":
            stmt = stmt.where(Task.role_context == role_context)

        now = datetime.now(timezone.utc)
        if status_filter == "overdue":
            stmt = stmt.where(Task.status.in_(["todo", "in_progress"]), Task.due_date < now)
        elif status_filter != "all":
            stmt = stmt.where(Task.status == status_filter)

        res = await db.execute(stmt.order_by(Task.due_date.asc().nulls_last()).limit(limit))
        tasks = res.scalars().all()
        return {
            "total_count": len(tasks),
            "tasks": [
                {
                    "id": str(t.id),
                    "title": t.title,
                    "status": t.status,
                    "priority": t.priority,
                    "role_context": t.role_context,
                    "due_date": t.due_date.isoformat() if t.due_date else None,
                    "estimated_minutes": t.estimated_minutes,
                }
                for t in tasks
            ],
        }
