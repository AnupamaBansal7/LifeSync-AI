import uuid
from datetime import date, datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    goal_id: Optional[uuid.UUID] = None
    parent_task_id: Optional[uuid.UUID] = None
    depends_on_id: Optional[uuid.UUID] = None
    role_context: str = "personal"
    category: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    priority: str = Field(default="medium", pattern="^(low|medium|high|urgent)$")
    status: str = Field(default="todo", pattern="^(todo|in_progress|blocked|completed|cancelled)$")
    due_date: Optional[datetime] = None
    estimated_minutes: int = Field(default=30, ge=5, le=1440)
    recurrence_rule: Optional[str] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    goal_id: Optional[uuid.UUID] = None
    depends_on_id: Optional[uuid.UUID] = None
    role_context: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    priority: Optional[str] = Field(default=None, pattern="^(low|medium|high|urgent)$")
    status: Optional[str] = Field(default=None, pattern="^(todo|in_progress|blocked|completed|cancelled)$")
    due_date: Optional[datetime] = None
    estimated_minutes: Optional[int] = Field(default=None, ge=5, le=1440)
    recurrence_rule: Optional[str] = None


class TaskOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    goal_id: Optional[uuid.UUID]
    parent_task_id: Optional[uuid.UUID]
    depends_on_id: Optional[uuid.UUID]
    title: str
    description: Optional[str]
    role_context: str
    category: Optional[str]
    tags: List[str]
    priority: str
    status: str
    due_date: Optional[datetime]
    estimated_minutes: int
    recurrence_rule: Optional[str]
    completed_at: Optional[datetime]
    created_by_agent: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MilestoneCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    target_date: Optional[date] = None
    order_index: int = 0


class MilestoneUpdate(BaseModel):
    title: Optional[str] = None
    target_date: Optional[date] = None
    is_completed: Optional[bool] = None
    order_index: Optional[int] = None


class MilestoneOut(BaseModel):
    id: uuid.UUID
    goal_id: uuid.UUID
    title: str
    target_date: Optional[date]
    is_completed: bool
    order_index: int

    model_config = {"from_attributes": True}


class GoalCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    horizon: str = Field(default="short_term", pattern="^(short_term|long_term)$")
    role_context: str = "personal"
    category: Optional[str] = None
    target_date: Optional[date] = None
    milestones: List[MilestoneCreate] = Field(default_factory=list)


class GoalUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    horizon: Optional[str] = Field(default=None, pattern="^(short_term|long_term)$")
    role_context: Optional[str] = None
    category: Optional[str] = None
    target_date: Optional[date] = None
    progress_percent: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    status: Optional[str] = Field(default=None, pattern="^(active|paused|completed|archived)$")


class GoalOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    description: Optional[str]
    horizon: str
    role_context: str
    category: Optional[str]
    target_date: Optional[date]
    progress_percent: float
    status: str
    milestones: List[MilestoneOut] = []
    created_at: datetime

    model_config = {"from_attributes": True}


class HabitCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = None
    role_context: str = "personal"
    frequency: str = Field(default="daily", pattern="^(daily|weekly|custom)$")
    target_days_per_week: int = Field(default=7, ge=1, le=7)
    reminder_time: Optional[str] = None


class HabitLogRequest(BaseModel):
    log_date: date = Field(default_factory=date.today)
    completed: bool = True
    notes: Optional[str] = None


class HabitOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    description: Optional[str]
    role_context: str
    frequency: str
    target_days_per_week: int
    reminder_time: Optional[str]
    current_streak: int
    longest_streak: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class CalendarEventCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    task_id: Optional[uuid.UUID] = None
    role_context: str = "personal"
    event_type: str = Field(default="time_block", pattern="^(meeting|time_block|exam|deadline|personal)$")
    start_time: datetime
    end_time: datetime
    is_all_day: bool = False
    is_locked: bool = False


class CalendarEventOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    task_id: Optional[uuid.UUID]
    title: str
    description: Optional[str]
    role_context: str
    event_type: str
    start_time: datetime
    end_time: datetime
    is_all_day: bool
    is_locked: bool

    model_config = {"from_attributes": True}


class DailyPlanOut(BaseModel):
    id: uuid.UUID
    plan_date: date
    summary: Optional[str]
    schedule_blocks: List[Dict[str, Any]]
    ai_insights: Dict[str, Any]
    status: str

    model_config = {"from_attributes": True}