import uuid
from datetime import date, datetime
from typing import List, Optional
from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, UUIDTimestampMixin


class Task(Base, UUIDTimestampMixin):
    __tablename__ = "tasks"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    goal_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("goals.id", ondelete="SET NULL"), index=True, nullable=True
    )
    parent_task_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), index=True, nullable=True
    )
    depends_on_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    role_context: Mapped[str] = mapped_column(String(50), default="personal", index=True, nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(80), index=True, nullable=True)
    tags: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)

    priority: Mapped[str] = mapped_column(String(20), default="medium", index=True, nullable=False)  # low, medium, high, urgent
    status: Mapped[str] = mapped_column(String(24), default="todo", index=True, nullable=False)      # todo, in_progress, blocked, completed, cancelled
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True, nullable=True)
    estimated_minutes: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    recurrence_rule: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by_agent: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)

    subtasks: Mapped[List["Task"]] = relationship(
        "Task",
        back_populates="parent_task",
        foreign_keys=[parent_task_id],
        cascade="all, delete-orphan",
    )
    parent_task: Mapped[Optional["Task"]] = relationship(
        "Task",
        back_populates="subtasks",
        remote_side="Task.id",
        foreign_keys=[parent_task_id],
    )
    history: Mapped[List["TaskHistory"]] = relationship(
        back_populates="task", cascade="all, delete-orphan"
    )


class TaskHistory(Base, UUIDTimestampMixin):
    __tablename__ = "task_history"

    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    changes: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    actor: Mapped[str] = mapped_column(String(80), default="user", nullable=False)

    task: Mapped["Task"] = relationship(back_populates="history")


class Goal(Base, UUIDTimestampMixin):
    __tablename__ = "goals"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    horizon: Mapped[str] = mapped_column(String(24), default="short_term", nullable=False)  # short_term, long_term
    role_context: Mapped[str] = mapped_column(String(50), default="personal", index=True, nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    target_date: Mapped[Optional[date]] = mapped_column(Date, index=True, nullable=True)
    progress_percent: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="active", index=True, nullable=False)  # active, paused, completed, archived

    milestones: Mapped[List["Milestone"]] = relationship(
        back_populates="goal", cascade="all, delete-orphan", order_by="Milestone.order_index"
    )


class Milestone(Base, UUIDTimestampMixin):
    __tablename__ = "milestones"

    goal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("goals.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    target_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    goal: Mapped["Goal"] = relationship(back_populates="milestones")


class Habit(Base, UUIDTimestampMixin):
    __tablename__ = "habits"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    role_context: Mapped[str] = mapped_column(String(50), default="personal", nullable=False)
    frequency: Mapped[str] = mapped_column(String(24), default="daily", nullable=False)  # daily, weekly, custom
    target_days_per_week: Mapped[int] = mapped_column(Integer, default=7, nullable=False)
    reminder_time: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    current_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    longest_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    logs: Mapped[List["HabitLog"]] = relationship(
        back_populates="habit", cascade="all, delete-orphan"
    )


class HabitLog(Base, UUIDTimestampMixin):
    __tablename__ = "habit_logs"
    __table_args__ = (UniqueConstraint("habit_id", "log_date", name="uq_habit_log_date"),)

    habit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("habits.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    log_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    habit: Mapped["Habit"] = relationship(back_populates="logs")