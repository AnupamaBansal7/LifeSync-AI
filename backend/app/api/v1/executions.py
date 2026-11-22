import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.services.shadow_execution_service import ShadowExecutionService

router = APIRouter(prefix="/executions", tags=["Shadow Execution & Rollback"])


class ApprovePlanRequest(BaseModel):
    approved_step_ids: Optional[List[str]] = Field(
        default=None,
        description="Optional list of specific step IDs to execute. If omitted, all steps are executed.",
    )


class SimulatePlanRequest(BaseModel):
    intent_summary: str
    proposed_tool_calls: List[Dict[str, Any]]
    auto_approve: bool = False
    plan_metadata: Optional[Dict[str, Any]] = None


@router.get("/plans", response_model=List[Dict[str, Any]])
async def list_transaction_plans(
    limit: int = Query(default=10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List recent shadow execution transaction plans for the current user."""
    return await ShadowExecutionService.list_recent_plans(
        db=db, user_id=current_user.id, limit=limit
    )


@router.post("/simulate", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def simulate_transaction_plan(
    payload: SimulatePlanRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Simulates proposed mutating tool calls, generating before/after diffs,
    risk analysis, and reversibility ratings without committing state changes.
    """
    return await ShadowExecutionService.simulate_plan(
        db=db,
        user_id=current_user.id,
        intent_summary=payload.intent_summary,
        proposed_tool_calls=payload.proposed_tool_calls,
        auto_approve_if_safe=payload.auto_approve,
        plan_metadata=payload.plan_metadata,
    )


@router.get("/plans/{plan_id}", response_model=Dict[str, Any])
async def get_transaction_plan(
    plan_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetch full transaction plan details, step diffs, and verification logs."""
    plan = await ShadowExecutionService.get_plan_details(
        db=db, user_id=current_user.id, plan_id=plan_id
    )
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction plan not found or unauthorized",
        )
    return plan


@router.post("/plans/{plan_id}/approve", response_model=Dict[str, Any])
async def approve_transaction_plan(
    plan_id: uuid.UUID,
    payload: Optional[ApprovePlanRequest] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Selectively or wholly approves proposed steps, executes them in sequence,
    and returns verified database state diffs.
    """
    # Check plan existence and ownership first
    existing = await ShadowExecutionService.get_plan_details(
        db=db, user_id=current_user.id, plan_id=plan_id
    )
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction plan not found or unauthorized",
        )

    approved_ids = payload.approved_step_ids if payload else None
    result = await ShadowExecutionService.approve_plan(
        db=db,
        user_id=current_user.id,
        plan_id=plan_id,
        approved_step_ids=approved_ids,
    )
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Execution failed"),
        )
    return result


@router.post("/plans/{plan_id}/reject", response_model=Dict[str, Any])
async def reject_transaction_plan(
    plan_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Rejects/cancels a transaction plan."""
    existing = await ShadowExecutionService.get_plan_details(
        db=db, user_id=current_user.id, plan_id=plan_id
    )
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction plan not found or unauthorized",
        )

    result = await ShadowExecutionService.reject_plan(
        db=db, user_id=current_user.id, plan_id=plan_id
    )
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Reject failed"),
        )
    return result


@router.post("/plans/{plan_id}/rollback", response_model=Dict[str, Any])
async def rollback_transaction_plan(
    plan_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Automated rollback: Executes compensating actions in reverse order
    for all reversible steps that succeeded.
    """
    existing = await ShadowExecutionService.get_plan_details(
        db=db, user_id=current_user.id, plan_id=plan_id
    )
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction plan not found or unauthorized",
        )

    result = await ShadowExecutionService.rollback_plan(
        db=db, user_id=current_user.id, plan_id=plan_id
    )
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Rollback failed"),
        )
    return result
