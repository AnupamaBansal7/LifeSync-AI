import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, UUIDTimestampMixin


class WorkflowExecution(Base, UUIDTimestampMixin):
    __tablename__ = "workflow_executions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(128), index=True, nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), default="pending", index=True, nullable=False
    )  # pending, running, awaiting_approval, completed, failed, cancelled, retrying
    plan_graph: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    context_state: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    current_step_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_retries: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=300, nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    steps: Mapped[List["WorkflowStepExecution"]] = relationship(
        back_populates="workflow", cascade="all, delete-orphan", order_by="WorkflowStepExecution.step_order"
    )


class WorkflowStepExecution(Base, UUIDTimestampMixin):
    __tablename__ = "workflow_step_executions"

    workflow_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workflow_executions.id", ondelete="CASCADE"), index=True, nullable=False
    )
    step_id: Mapped[str] = mapped_column(String(80), nullable=False)
    step_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    agent_name: Mapped[str] = mapped_column(String(80), nullable=False)
    tool_name: Mapped[str] = mapped_column(String(80), nullable=False)
    input_payload: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    output_payload: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    depends_on: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)  # list of prerequisite step_ids
    status: Mapped[str] = mapped_column(
        String(32), default="pending", index=True, nullable=False
    )  # pending, running, awaiting_approval, completed, failed, skipped, cancelled
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    approval_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("action_approvals.id", ondelete="SET NULL"), nullable=True
    )
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_retries: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    workflow: Mapped["WorkflowExecution"] = relationship(back_populates="steps")
