import uuid
from typing import List, Optional
from sqlalchemy import Boolean, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, UUIDTimestampMixin


class User(Base, UUIDTimestampMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_onboarded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    profile: Mapped[Optional["UserProfile"]] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    preferences: Mapped[Optional["UserPreference"]] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    roles: Mapped[List["UserRole"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    modules: Mapped[List["UserModule"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Role(Base, UUIDTimestampMixin):
    __tablename__ = "roles"

    slug: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    default_modules: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)


class UserRole(Base, UUIDTimestampMixin):
    __tablename__ = "user_roles"
    __table_args__ = (UniqueConstraint("user_id", "role_id", name="uq_user_role"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), index=True, nullable=False
    )
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    context_metadata: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    user: Mapped["User"] = relationship(back_populates="roles")
    role: Mapped["Role"] = relationship()


class UserProfile(Base, UUIDTimestampMixin):
    __tablename__ = "user_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    headline: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    organization: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    focus_areas: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    work_hours_start: Mapped[str] = mapped_column(String(10), default="09:00", nullable=False)
    work_hours_end: Mapped[str] = mapped_column(String(10), default="18:00", nullable=False)

    user: Mapped["User"] = relationship(back_populates="profile")


class UserPreference(Base, UUIDTimestampMixin):
    __tablename__ = "user_preferences"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    timezone: Mapped[str] = mapped_column(String(64), default="UTC", nullable=False)
    language: Mapped[str] = mapped_column(String(16), default="en", nullable=False)
    theme: Mapped[str] = mapped_column(String(20), default="dark", nullable=False)
    reduced_motion: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ai_auto_approve_low_risk: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    training_data_opt_in: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notification_settings: Mapped[dict] = mapped_column(
        JSONB,
        default=lambda: {"daily_briefing": True, "deadline_alerts": True, "habit_nudges": True},
        nullable=False,
    )

    user: Mapped["User"] = relationship(back_populates="preferences")


class UserModule(Base, UUIDTimestampMixin):
    __tablename__ = "user_modules"
    __table_args__ = (UniqueConstraint("user_id", "module_key", name="uq_user_module"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    module_key: Mapped[str] = mapped_column(String(50), nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    config: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    user: Mapped["User"] = relationship(back_populates="modules")