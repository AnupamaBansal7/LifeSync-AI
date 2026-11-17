import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, EmailStr, Field


class RoleOut(BaseModel):
    id: uuid.UUID
    slug: str
    name: str
    description: Optional[str] = None
    default_modules: List[str] = []

    model_config = {"from_attributes": True}


class UserRoleAssignmentInput(BaseModel):
    role_slug: str
    is_primary: bool = False
    context_metadata: Dict[str, Any] = Field(default_factory=dict)


class UserRoleOut(BaseModel):
    id: uuid.UUID
    role: RoleOut
    is_primary: bool
    context_metadata: Dict[str, Any]

    model_config = {"from_attributes": True}


class UserProfileOut(BaseModel):
    headline: Optional[str] = None
    bio: Optional[str] = None
    organization: Optional[str] = None
    focus_areas: List[str] = []
    work_hours_start: str
    work_hours_end: str

    model_config = {"from_attributes": True}


class UserProfileUpdate(BaseModel):
    headline: Optional[str] = Field(default=None, max_length=200)
    bio: Optional[str] = None
    organization: Optional[str] = Field(default=None, max_length=150)
    focus_areas: Optional[List[str]] = None
    work_hours_start: Optional[str] = Field(default=None, pattern=r"^\d{2}:\d{2}$")
    work_hours_end: Optional[str] = Field(default=None, pattern=r"^\d{2}:\d{2}$")


class UserPreferenceOut(BaseModel):
    timezone: str
    language: str
    theme: str
    reduced_motion: bool
    ai_auto_approve_low_risk: bool
    training_data_opt_in: bool
    notification_settings: Dict[str, Any]

    model_config = {"from_attributes": True}


class UserPreferenceUpdate(BaseModel):
    timezone: Optional[str] = None
    language: Optional[str] = None
    theme: Optional[str] = Field(default=None, pattern="^(dark|light|system)$")
    reduced_motion: Optional[bool] = None
    ai_auto_approve_low_risk: Optional[bool] = None
    training_data_opt_in: Optional[bool] = None
    notification_settings: Optional[Dict[str, Any]] = None


class UserModuleOut(BaseModel):
    id: uuid.UUID
    module_key: str
    is_enabled: bool
    config: Dict[str, Any]

    model_config = {"from_attributes": True}


class UserModuleToggleRequest(BaseModel):
    is_enabled: bool
    config: Optional[Dict[str, Any]] = None


class OnboardingCompleteRequest(BaseModel):
    roles: List[UserRoleAssignmentInput] = Field(min_length=1)
    headline: Optional[str] = Field(default=None, max_length=200)
    organization: Optional[str] = Field(default=None, max_length=150)
    focus_areas: List[str] = Field(default_factory=list)
    work_hours_start: str = Field(default="09:00", pattern=r"^\d{2}:\d{2}$")
    work_hours_end: str = Field(default="18:00", pattern=r"^\d{2}:\d{2}$")
    timezone: str = "UTC"
    enabled_modules: List[str] = Field(
        default_factory=lambda: ["tasks", "goals", "habits", "calendar", "memory", "analytics"]
    )
    initial_goals: List[str] = Field(default_factory=list)
    training_data_opt_in: bool = False


class UserMeResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str
    is_active: bool
    is_onboarded: bool
    created_at: datetime
    profile: Optional[UserProfileOut] = None
    preferences: Optional[UserPreferenceOut] = None
    roles: List[UserRoleOut] = []
    modules: List[UserModuleOut] = []

    model_config = {"from_attributes": True}