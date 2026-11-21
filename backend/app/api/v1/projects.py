from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.ai_system import KnowledgeDocument, Memory
from app.models.productivity import Goal, Project, Task
from app.models.user import User


router = APIRouter(prefix="/projects", tags=["Project Workspaces & Knowledge Brain"])


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: Optional[str] = None
    role_context: str = Field(default="professional")
    target_date: Optional[date] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    role_context: Optional[str] = None
    status: Optional[str] = None
    target_date: Optional[date] = None


class ProjectNoteCreate(BaseModel):
    title: str
    content: str
    tags: List[str] = Field(default_factory=list)


class ProjectDecisionCreate(BaseModel):
    decision: str
    rationale: str
    options_considered: List[str] = Field(default_factory=list)
    impact: str = "medium"


class ProjectOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    description: Optional[str]
    role_context: str
    status: str
    target_date: Optional[date]
    notes: List[Dict[str, Any]] = []
    decisions: List[Dict[str, Any]] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectDetailOut(ProjectOut):
    tasks_count: int = 0
    goals_count: int = 0
    documents_count: int = 0


@router.get("", response_model=List[ProjectDetailOut])
async def list_projects(
    role: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all project workspaces for the authenticated user."""
    stmt = select(Project).where(Project.user_id == current_user.id)
    if role:
        stmt = stmt.where(Project.role_context == role)
    res = await db.execute(stmt.order_by(Project.created_at.desc()))
    projects = res.scalars().all()

    detailed = []
    for p in projects:
        # Count linked items
        res_t = await db.execute(select(Task).where(Task.project_id == p.id))
        t_count = len(res_t.scalars().all())

        res_g = await db.execute(select(Goal).where(Goal.project_id == p.id))
        g_count = len(res_g.scalars().all())

        res_d = await db.execute(select(KnowledgeDocument).where(KnowledgeDocument.project_id == p.id))
        d_count = len(res_d.scalars().all())

        detail = ProjectDetailOut.model_validate(p)
        detail.tasks_count = t_count
        detail.goals_count = g_count
        detail.documents_count = d_count
        detailed.append(detail)

    return detailed


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new dedicated project workspace."""
    project = Project(
        user_id=current_user.id,
        name=payload.name,
        description=payload.description,
        role_context=payload.role_context,
        target_date=payload.target_date,
        status="active",
        notes=[],
        decisions=[],
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectDetailOut)
async def get_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get project details with linked tasks, decisions, notes, and documents."""
    res = await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == current_user.id)
    )
    project = res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    res_t = await db.execute(select(Task).where(Task.project_id == project.id))
    t_count = len(res_t.scalars().all())

    res_g = await db.execute(select(Goal).where(Goal.project_id == project.id))
    g_count = len(res_g.scalars().all())

    res_d = await db.execute(select(KnowledgeDocument).where(KnowledgeDocument.project_id == project.id))
    d_count = len(res_d.scalars().all())

    detail = ProjectDetailOut.model_validate(project)
    detail.tasks_count = t_count
    detail.goals_count = g_count
    detail.documents_count = d_count
    return detail


@router.patch("/{project_id}", response_model=ProjectOut)
async def update_project(
    project_id: uuid.UUID,
    payload: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update project status or metadata."""
    res = await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == current_user.id)
    )
    project = res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    changes = payload.model_dump(exclude_unset=True)
    for field, val in changes.items():
        setattr(project, field, val)

    await db.commit()
    await db.refresh(project)
    return project


@router.post("/{project_id}/notes", response_model=ProjectOut)
async def add_project_note(
    project_id: uuid.UUID,
    payload: ProjectNoteCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a structured markdown note to the project workspace."""
    res = await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == current_user.id)
    )
    project = res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    note_entry = {
        "id": uuid.uuid4().hex[:12],
        "title": payload.title,
        "content": payload.content,
        "tags": payload.tags,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    project.notes = list(project.notes) + [note_entry]

    await db.commit()
    await db.refresh(project)
    return project


@router.post("/{project_id}/decisions", response_model=ProjectOut)
async def log_project_decision(
    project_id: uuid.UUID,
    payload: ProjectDecisionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Record an architectural or strategic decision for future AI context."""
    res = await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == current_user.id)
    )
    project = res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    decision_entry = {
        "id": uuid.uuid4().hex[:12],
        "decision": payload.decision,
        "rationale": payload.rationale,
        "options_considered": payload.options_considered,
        "impact": payload.impact,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    project.decisions = list(project.decisions) + [decision_entry]

    await db.commit()
    await db.refresh(project)
    return project
