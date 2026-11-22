import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, UUIDTimestampMixin


class IntakeSession(Base, UUIDTimestampMixin):
    __tablename__ = "intake_sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    initial_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    domain: Mapped[str] = mapped_column(String(40), default="GENERAL", nullable=False)  # GOAL_PLANNING, PROJECT_BREAKDOWN, TASK_CAPTURE, HABIT_DESIGN, GENERAL
    status: Mapped[str] = mapped_column(String(32), default="GATHERING_INFO", nullable=False, index=True)  # GATHERING_INFO, READY_TO_SIMULATE, COMPLETED, CANCELLED
    collected_context_json: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    current_step: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    max_steps: Mapped[int] = mapped_column(Integer, default=4, nullable=False)
    resulting_plan_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("transaction_plans.id", ondelete="SET NULL"), nullable=True
    )

    user = relationship("User", backref="intake_sessions")
    resulting_plan = relationship("TransactionPlan", backref="intake_session")
