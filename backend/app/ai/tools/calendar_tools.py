from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
import uuid
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.ai.tools.base import BaseTool, Reversibility
from app.models.calendar import CalendarEvent, DailyPlan


class CreateCalendarBlockTool(BaseTool):
    @property
    def name(self) -> str:
        return "create_calendar_block"

    @property
    def description(self) -> str:
        return "Schedule a calendar event or time-block. Checks for conflicts against locked commitments."

    @property
    def requires_approval(self) -> bool:
        return False

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
                "title": {"type": "string", "description": "Title of calendar event or focus block"},
                "start_time": {"type": "string", "description": "ISO 8601 start datetime"},
                "end_time": {"type": "string", "description": "ISO 8601 end datetime"},
                "duration_minutes": {"type": "integer", "default": 60},
                "role_context": {"type": "string", "default": "personal"},
                "event_type": {"type": "string", "enum": ["time_block", "meeting", "exam", "deadline", "personal"], "default": "time_block"},
                "is_locked": {"type": "boolean", "default": False},
            },
            "required": ["title"],
        }

    async def dry_run(self, db: AsyncSession, user_id: uuid.UUID, args: Dict[str, Any]) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        start_str = args.get("start_time")
        end_str = args.get("end_time")
        dur = int(args.get("duration_minutes", 60))

        if start_str:
            try:
                start_dt = datetime.fromisoformat(start_str)
            except ValueError:
                start_dt = now.replace(hour=9, minute=0, second=0, microsecond=0)
        else:
            start_dt = now.replace(hour=9, minute=0, second=0, microsecond=0)

        if end_str:
            try:
                end_dt = datetime.fromisoformat(end_str)
            except ValueError:
                end_dt = start_dt + timedelta(minutes=dur)
        else:
            end_dt = start_dt + timedelta(minutes=dur)

        # Conflict check (read-only)
        stmt = select(CalendarEvent).where(
            CalendarEvent.user_id == user_id,
            CalendarEvent.start_time < end_dt,
            CalendarEvent.end_time > start_dt,
        )
        res = await db.execute(stmt)
        conflicts = [c.title for c in res.scalars().all()]

        return {
            "action_summary": f"Schedule calendar event: '{args.get('title', 'Focus Session')}'",
            "target_entity": "CalendarEvent",
            "before_state": {},
            "after_state": {
                "title": args.get("title", "Focus Session").strip(),
                "start_time": start_dt.isoformat(),
                "end_time": end_dt.isoformat(),
                "event_type": args.get("event_type", "time_block"),
                "role_context": args.get("role_context", "personal"),
                "conflicts_detected": conflicts,
            },
            "risk_level": "LOW",
            "reversibility": self.reversibility.value,
        }

    async def compensate(self, db: AsyncSession, user_id: uuid.UUID, snapshot: Dict[str, Any]) -> Dict[str, Any]:
        event_id_str = snapshot.get("created_event_id") or snapshot.get("event_id") or snapshot.get("id")
        if not event_id_str:
            title = snapshot.get("title")
            if title:
                res = await db.execute(select(CalendarEvent).where(CalendarEvent.title == title, CalendarEvent.user_id == user_id))
                ev = res.scalar_one_or_none()
                if ev:
                    event_id_str = str(ev.id)

        if event_id_str:
            try:
                ev_id = uuid.UUID(event_id_str)
                await db.execute(delete(CalendarEvent).where(CalendarEvent.id == ev_id, CalendarEvent.user_id == user_id))
                await db.commit()
                return {
                    "success": True,
                    "restored_entity_id": str(ev_id),
                    "details": f"Deleted calendar event '{ev_id}' to revert creation.",
                    "error": None,
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "restored_entity_id": event_id_str,
                    "details": "Failed to rollback calendar event.",
                }

        return {
            "success": False,
            "error": "Calendar event ID not found in snapshot for compensation.",
            "restored_entity_id": None,
            "details": "Snapshot missing entity ID.",
        }

    async def execute(self, db: AsyncSession, user_id: uuid.UUID, args: Dict[str, Any]) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        start_str = args.get("start_time")
        end_str = args.get("end_time")

        if start_str:
            try:
                start_dt = datetime.fromisoformat(start_str)
            except ValueError:
                start_dt = now.replace(hour=9, minute=0, second=0, microsecond=0)
        else:
            start_dt = now.replace(hour=9, minute=0, second=0, microsecond=0)

        dur = int(args.get("duration_minutes", 60))
        if end_str:
            try:
                end_dt = datetime.fromisoformat(end_str)
            except ValueError:
                end_dt = start_dt + timedelta(minutes=dur)
        else:
            end_dt = start_dt + timedelta(minutes=dur)

        # Conflict check
        stmt = select(CalendarEvent).where(
            CalendarEvent.user_id == user_id,
            CalendarEvent.start_time < end_dt,
            CalendarEvent.end_time > start_dt,
        )
        res = await db.execute(stmt)
        conflicts = res.scalars().all()
        conflict_notes = []
        for c in conflicts:
            conflict_notes.append(f"Conflicts with: {c.title} ({c.start_time.strftime('%H:%M')}-{c.end_time.strftime('%H:%M')})")

        ev = CalendarEvent(
            user_id=user_id,
            title=args.get("title", "Focus Session").strip(),
            description=args.get("description"),
            role_context=args.get("role_context", "personal"),
            event_type=args.get("event_type", "time_block"),
            start_time=start_dt,
            end_time=end_dt,
            is_locked=bool(args.get("is_locked", False)),
        )
        db.add(ev)
        await db.commit()
        await db.refresh(ev)
        return {
            "created_event_id": str(ev.id),
            "title": ev.title,
            "start_time": ev.start_time.isoformat(),
            "end_time": ev.end_time.isoformat(),
            "is_locked": ev.is_locked,
            "conflicts": conflict_notes,
        }


class ListCalendarEventsTool(BaseTool):
    @property
    def name(self) -> str:
        return "list_calendar_events"

    @property
    def description(self) -> str:
        return "Retrieve scheduled events and time-blocks for a given time range."

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
                "days_ahead": {"type": "integer", "default": 7},
                "role_context": {"type": "string"},
            },
        }

    async def execute(self, db: AsyncSession, user_id: uuid.UUID, args: Dict[str, Any]) -> Dict[str, Any]:
        days_ahead = int(args.get("days_ahead", 7))
        role_context = args.get("role_context")
        now = datetime.now(timezone.utc)
        future = now + timedelta(days=days_ahead)

        stmt = select(CalendarEvent).where(
            CalendarEvent.user_id == user_id,
            CalendarEvent.start_time >= now - timedelta(hours=1),
            CalendarEvent.start_time <= future,
        )
        if role_context and role_context != "all":
            stmt = stmt.where(CalendarEvent.role_context == role_context)

        res = await db.execute(stmt.order_by(CalendarEvent.start_time.asc()))
        events = res.scalars().all()
        return {
            "total_count": len(events),
            "events": [
                {
                    "id": str(e.id),
                    "title": e.title,
                    "event_type": e.event_type,
                    "start_time": e.start_time.isoformat(),
                    "end_time": e.end_time.isoformat(),
                    "is_locked": e.is_locked,
                    "role_context": e.role_context,
                }
                for e in events
            ],
        }


class DeleteCalendarEventTool(BaseTool):
    @property
    def name(self) -> str:
        return "delete_calendar_event"

    @property
    def description(self) -> str:
        return "Delete a scheduled calendar event. Higher-risk action requiring user confirmation."

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
                "event_id": {"type": "string"},
                "title_query": {"type": "string"},
            },
        }

    async def execute(self, db: AsyncSession, user_id: uuid.UUID, args: Dict[str, Any]) -> Dict[str, Any]:
        ev_id = args.get("event_id")
        title_q = args.get("title_query")
        ev = None
        if ev_id:
            try:
                res = await db.execute(select(CalendarEvent).where(CalendarEvent.id == uuid.UUID(ev_id), CalendarEvent.user_id == user_id))
                ev = res.scalar_one_or_none()
            except ValueError:
                pass

        if not ev and title_q:
            res = await db.execute(select(CalendarEvent).where(CalendarEvent.user_id == user_id))
            for item in res.scalars().all():
                if title_q.lower() in item.title.lower():
                    ev = item
                    break

        if not ev:
            return {"error": "Calendar event to delete not found"}

        title = ev.title
        eid = str(ev.id)
        await db.delete(ev)
        await db.commit()
        return {"deleted": True, "event_id": eid, "title": title}


class SaveDailyPlanTool(BaseTool):
    @property
    def name(self) -> str:
        return "save_daily_plan"

    @property
    def description(self) -> str:
        return "Save an AI synthesized daily execution timetable with time blocks and productivity insights."

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
                "summary": {"type": "string"},
                "schedule_blocks": {"type": "array", "items": {"type": "object"}},
                "ai_insights": {"type": "object"},
            },
        }

    async def execute(self, db: AsyncSession, user_id: uuid.UUID, args: Dict[str, Any]) -> Dict[str, Any]:
        plan = DailyPlan(
            user_id=user_id,
            plan_date=date.today(),
            summary=args.get("summary", "AI Generated Daily Execution Plan"),
            schedule_blocks=args.get("schedule_blocks", []),
            ai_insights=args.get("ai_insights", {}),
            status="active",
        )
        db.add(plan)
        await db.commit()
        await db.refresh(plan)
        return {
            "daily_plan_id": str(plan.id),
            "plan_date": str(plan.plan_date),
            "summary": plan.summary,
            "blocks_count": len(plan.schedule_blocks),
        }
