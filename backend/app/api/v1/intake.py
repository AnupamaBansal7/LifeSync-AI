import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.services.agentic_intake_service import AgenticIntakeService

router = APIRouter(prefix="/intake", tags=["Conversational Agentic Intake"])


class IntakeStartRequest(BaseModel):
    prompt: str = Field(..., min_length=2, max_length=2000, description="High-level goal or planning objective")
    role_context: str = "personal"


class IntakeRespondRequest(BaseModel):
    selected_options: List[str] = Field(default=[], description="Selected option IDs or values")
    custom_text: Optional[str] = Field(default=None, description="Optional custom typed or spoken input")
    skip_and_generate: bool = Field(default=False, description="Whether to immediately compile the blueprint plan")
    role_context: str = "personal"


@router.post("/start", status_code=status.HTTP_200_OK)
async def start_intake_session(
    payload: IntakeStartRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Starts a new conversational zero-form intake session, returning a structured ClarificationCard."""
    result = await AgenticIntakeService.start_or_continue_intake(
        db=db,
        user_id=current_user.id,
        prompt=payload.prompt,
        role_context=payload.role_context,
    )
    return result


@router.post("/{session_id}/respond", status_code=status.HTTP_200_OK)
async def respond_to_intake_session(
    session_id: uuid.UUID,
    payload: IntakeRespondRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Advances an active intake session with user selections, returning either the next ClarificationCard or the compiled TransactionPlan."""
    try:
        result = await AgenticIntakeService.respond_to_intake(
            db=db,
            user_id=current_user.id,
            session_id=session_id,
            selected_options=payload.selected_options,
            custom_text=payload.custom_text,
            skip_and_generate=payload.skip_and_generate,
            role_context=payload.role_context,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{session_id}/cancel", status_code=status.HTTP_200_OK)
async def cancel_intake_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cancels an active intake session."""
    try:
        result = await AgenticIntakeService.cancel_intake(
            db=db,
            user_id=current_user.id,
            session_id=session_id,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
