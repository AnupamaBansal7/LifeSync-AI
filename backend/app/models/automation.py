import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, UUIDTimestampMixin


class Notification(Base, UUIDTimestampMixin):
    __tablename__ = "notifications"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(40), default="reminder", nullable=False)  # reminder, deadline, agent_approval, insight
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, index=True, nullable=False)
    action_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)


class AutomationRule(Base, UUIDTimestampMixin):
    __tablename__ = "automation_rules"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    trigger_type: Mapped[str] = mapped_column(String(50), nullable=False)  # schedule, task_overdue, habit_missed
    trigger_config: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)   # daily_review, reschedule_suggest, notify
    action_config: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_triggered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)