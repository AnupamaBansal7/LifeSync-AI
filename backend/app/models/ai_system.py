import uuid
from typing import List, Optional
from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.config import settings
from app.models.base import Base, UUIDTimestampMixin


class Conversation(Base, UUIDTimestampMixin):
    __tablename__ = "conversations"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), default="New Session", nullable=False)
    active_role: Mapped[str] = mapped_column(String(50), default="personal", nullable=False)

    messages: Mapped[List["Message"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at"
    )


class Message(Base, UUIDTimestampMixin):
    __tablename__ = "messages"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    sender: Mapped[str] = mapped_column(String(20), nullable=False)  # user, assistant, system
    content: Mapped[str] = mapped_column(Text, nullable=False)
    agent_run_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_runs.id", ondelete="SET NULL"), nullable=True
    )
    structured_payload: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")


class Memory(Base, UUIDTimestampMixin):
    __tablename__ = "memories"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    category: Mapped[str] = mapped_column(String(50), default="preference", index=True, nullable=False)  # preference, goal, responsibility, decision, academic, work
    role_context: Mapped[str] = mapped_column(String(50), default="personal", index=True, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    importance_score: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    source: Mapped[str] = mapped_column(String(80), default="conversation", nullable=False)
    consent_for_training: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    embedding: Mapped[Optional[list]] = mapped_column(Vector(settings.EMBEDDING_DIMENSIONS), nullable=True)


class KnowledgeDocument(Base, UUIDTimestampMixin):
    __tablename__ = "knowledge_documents"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    role_context: Mapped[str] = mapped_column(String(50), default="personal", nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    embedding: Mapped[Optional[list]] = mapped_column(Vector(settings.EMBEDDING_DIMENSIONS), nullable=True)


class AgentRun(Base, UUIDTimestampMixin):
    __tablename__ = "agent_runs"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    conversation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True
    )
    user_query: Mapped[str] = mapped_column(Text, nullable=False)
    detected_intent: Mapped[str] = mapped_column(String(100), default="general", nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="running", index=True, nullable=False)  # running, awaiting_approval, completed, failed
    final_response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    steps: Mapped[List["AgentExecutionStep"]] = relationship(
        back_populates="agent_run", cascade="all, delete-orphan", order_by="AgentExecutionStep.step_order"
    )
    approvals: Mapped[List["ActionApproval"]] = relationship(
        back_populates="agent_run", cascade="all, delete-orphan"
    )


class AgentExecutionStep(Base, UUIDTimestampMixin):
    __tablename__ = "agent_execution_steps"

    agent_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_runs.id", ondelete="CASCADE"), index=True, nullable=False
    )
    step_order: Mapped[int] = mapped_column(Integer, nullable=False)
    agent_name: Mapped[str] = mapped_column(String(80), nullable=False)
    tool_name: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    input_summary: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    output_summary: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="completed", nullable=False)

    agent_run: Mapped["AgentRun"] = relationship(back_populates="steps")


class ActionApproval(Base, UUIDTimestampMixin):
    __tablename__ = "action_approvals"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    agent_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_runs.id", ondelete="CASCADE"), index=True, nullable=False
    )
    agent_name: Mapped[str] = mapped_column(String(80), nullable=False)
    tool_name: Mapped[str] = mapped_column(String(80), nullable=False)
    action_summary: Mapped[str] = mapped_column(String(255), nullable=False)
    tool_arguments: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="pending", index=True, nullable=False)  # pending, approved, rejected, executed, failed
    execution_result: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    agent_run: Mapped["AgentRun"] = relationship(back_populates="approvals")


class ModelConfiguration(Base, UUIDTimestampMixin):
    __tablename__ = "model_configurations"

    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=True
    )
    agent_name: Mapped[str] = mapped_column(String(80), default="default", nullable=False)
    provider_type: Mapped[str] = mapped_column(String(50), default="openai_compatible", nullable=False)  # openai_compatible, ollama_local, custom_finetuned
    model_name: Mapped[str] = mapped_column(String(120), nullable=False)
    temperature: Mapped[float] = mapped_column(Float, default=0.3, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class TrainingDatasetRecord(Base, UUIDTimestampMixin):
    __tablename__ = "training_dataset_records"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    dataset_version: Mapped[str] = mapped_column(String(32), default="v1.0", index=True, nullable=False)
    agent_name: Mapped[str] = mapped_column(String(80), nullable=False)
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    user_input: Mapped[str] = mapped_column(Text, nullable=False)
    expected_output: Mapped[str] = mapped_column(Text, nullable=False)
    user_feedback_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1 to 5
    is_approved_for_training: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)