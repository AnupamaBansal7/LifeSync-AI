import uuid
from datetime import date, datetime
from typing import Optional
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, UUIDTimestampMixin


class CalendarEvent(Base, UUIDTimestampMixin):
    __tablename__ = "calendar_events"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    task_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="SET NULL"), index=True, nullable=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    role_context: Mapped[str] = mapped_column(String(50), default="personal", index=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(32), default="time_block", nullable=False)  # meeting, time_block, exam, deadline, personal
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    is_all_day: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # Prevents auto-rescheduler from moving fixed meetings


class DailyPlan(Base, UUIDTimestampMixin):
    __tablename__ = "daily_plans"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    plan_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    schedule_blocks: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    ai_insights: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="draft", nullable=False)  # draft, active, completed