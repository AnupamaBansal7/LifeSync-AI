import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, UUIDTimestampMixin


class TransactionPlan(Base, UUIDTimestampMixin):
    __tablename__ = "transaction_plans"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    intent_summary: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default="SIMULATED", index=True, nullable=False
    )  # SIMULATED, AWAITING_APPROVAL, EXECUTING, VERIFIED, PARTIALLY_FAILED, ROLLED_BACK, CANCELLED
    plan_metadata: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    executed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    rolled_back_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    steps: Mapped[List["TransactionStep"]] = relationship(
        back_populates="plan", cascade="all, delete-orphan", order_by="TransactionStep.step_order"
    )


class TransactionStep(Base, UUIDTimestampMixin):
    __tablename__ = "transaction_steps"

    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("transaction_plans.id", ondelete="CASCADE"), index=True, nullable=False
    )
    step_order: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    tool_name: Mapped[str] = mapped_column(String(80), nullable=False)
    reversibility: Mapped[str] = mapped_column(
        String(32), default="REVERSIBLE", nullable=False
    )  # REVERSIBLE, DELAYED_UNDO, IRREVERSIBLE
    risk_level: Mapped[str] = mapped_column(
        String(20), default="LOW", nullable=False
    )  # LOW, MEDIUM, HIGH
    params_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    before_state_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    after_state_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    approved: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default="pending", index=True, nullable=False
    )  # pending, executing, verified, failed, rolled_back, skipped
    verification_result_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    executed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    plan: Mapped["TransactionPlan"] = relationship(back_populates="steps")
