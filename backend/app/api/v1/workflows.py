import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.workflow import WorkflowExecution, WorkflowStepExecution
from app.services.workflow_engine import WorkflowEngineService


router = APIRouter(prefix="/workflows", tags=["Workflow Execution Engine"])


class WorkflowStepCreate(BaseModel):
    step_id: str
    name: str
    agent_name: str = "WorkflowAgent"
    tool_name: str
    input_payload: Dict[str, Any] = Field(default_factory=dict)
    depends_on: List[str] = Field(default_factory=list)
    max_retries: int = 2


class WorkflowCreateRequest(BaseModel):
    name: str
    steps: List[WorkflowStepCreate]
    idempotency_key: Optional[str] = None
    context_state: Dict[str, Any] = Field(default_factory=dict)
    timeout_seconds: int = 300
    auto_start: bool = True


class WorkflowStepOut(BaseModel):
    id: uuid.UUID
    step_id: str
    step_order: int
    name: str
    agent_name: str
    tool_name: str
    input_payload: Dict[str, Any]
    output_payload: Dict[str, Any]
    depends_on: List[str]
    status: str
    requires_approval: bool
    approval_id: Optional[uuid.UUID]
    retry_count: int
    error: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    model_config = {"from_attributes": True}


class WorkflowExecutionOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    idempotency_key: Optional[str]
    status: str
    plan_graph: Dict[str, Any]
    current_step_index: int
    error_message: Optional[str]
    retry_count: int
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    steps: List[WorkflowStepOut] = []

    model_config = {"from_attributes": True}


@router.post("", response_model=WorkflowExecutionOut, status_code=status.HTTP_201_CREATED)
async def create_workflow(
    payload: WorkflowCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create and optionally start a resilient multi-step DAG workflow."""
    steps_dicts = [s.model_dump() for s in payload.steps]
    wf = await WorkflowEngineService.create_workflow(
        db=db,
        user_id=current_user.id,
        name=payload.name,
        steps_plan=steps_dicts,
        idempotency_key=payload.idempotency_key,
        context_state=payload.context_state,
        timeout_seconds=payload.timeout_seconds,
    )

    if payload.auto_start and wf.status == "pending":
        wf = await WorkflowEngineService.execute_workflow(db, wf.id)

    # Reload with steps
    res = await db.execute(
        select(WorkflowExecution)
        .options(selectinload(WorkflowExecution.steps))
        .where(WorkflowExecution.id == wf.id)
    )
    return res.scalar_one()


@router.get("", response_model=List[WorkflowExecutionOut])
async def list_workflows(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List recent workflow executions with step states."""
    res = await db.execute(
        select(WorkflowExecution)
        .options(selectinload(WorkflowExecution.steps))
        .where(WorkflowExecution.user_id == current_user.id)
        .order_by(WorkflowExecution.created_at.desc())
        .limit(25)
    )
    return res.scalars().all()


@router.get("/{workflow_id}", response_model=WorkflowExecutionOut)
async def get_workflow(
    workflow_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get single workflow DAG execution status and step outputs."""
    res = await db.execute(
        select(WorkflowExecution)
        .options(selectinload(WorkflowExecution.steps))
        .where(WorkflowExecution.id == workflow_id, WorkflowExecution.user_id == current_user.id)
    )
    wf = res.scalar_one_or_none()
    if not wf:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")
    return wf


@router.post("/{workflow_id}/resume", response_model=WorkflowExecutionOut)
async def resume_workflow(
    workflow_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Resume execution of an awaiting-approval or paused workflow."""
    wf = await WorkflowEngineService.resume_workflow(db, workflow_id)
    res = await db.execute(
        select(WorkflowExecution)
        .options(selectinload(WorkflowExecution.steps))
        .where(WorkflowExecution.id == wf.id)
    )
    return res.scalar_one()


@router.post("/{workflow_id}/cancel", response_model=WorkflowExecutionOut)
async def cancel_workflow(
    workflow_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Safely cancel an active workflow."""
    wf = await WorkflowEngineService.cancel_workflow(db, workflow_id)
    res = await db.execute(
        select(WorkflowExecution)
        .options(selectinload(WorkflowExecution.steps))
        .where(WorkflowExecution.id == wf.id)
    )
    return res.scalar_one()
