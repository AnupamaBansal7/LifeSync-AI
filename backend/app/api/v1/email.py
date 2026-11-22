import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.services.integrations_service import IntegrationsService


router = APIRouter(prefix="/email", tags=["Email Workspace & Intelligence"])


class SendEmailPayload(BaseModel):
    to: str
    subject: str
    body: str
    cc: Optional[str] = None


class ReplyEmailPayload(BaseModel):
    message_id: str
    body: str
    reply_all: bool = False


class ForwardEmailPayload(BaseModel):
    message_id: str
    to: str
    comment: Optional[str] = None


class ExtractTasksPayload(BaseModel):
    message_id: str
    custom_title: Optional[str] = None


@router.get("/messages")
async def get_email_messages(
    folder: str = Query(default="inbox", description="inbox, unread, important, sent, drafts, archived"),
    q: str = Query(default="", description="Search sender, subject, or keyword"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=15, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve paginated emails filtered by folder or search keyword."""
    return await IntegrationsService.fetch_unified_emails(
        db=db,
        user_id=current_user.id,
        folder=folder,
        query=q,
        page=page,
        page_size=page_size,
    )


@router.get("/messages/{message_id}")
async def get_email_message_details(
    message_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve full email content, headers, attachments, and extracted actions."""
    return await IntegrationsService.get_email_details(
        db=db,
        user_id=current_user.id,
        message_id=message_id,
    )


@router.post("/send")
async def send_email(
    payload: SendEmailPayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send an outbound email through connected Gmail or Microsoft Outlook."""
    if not payload.to or not payload.subject:
        raise HTTPException(status_code=400, detail="Recipient and subject are required.")

    result = await IntegrationsService.send_email(
        db=db,
        user_id=current_user.id,
        recipient=payload.to,
        subject=payload.subject,
        body=payload.body,
    )
    return result


@router.post("/reply")
async def reply_to_email(
    payload: ReplyEmailPayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a contextual reply to an email thread."""
    details = await IntegrationsService.get_email_details(db, current_user.id, payload.message_id)
    email_data = details.get("email", {})
    recipient = email_data.get("sender", "")
    subject = email_data.get("subject", "Reply")
    if not subject.lower().startswith("re:"):
        subject = f"Re: {subject}"

    result = await IntegrationsService.send_email(
        db=db,
        user_id=current_user.id,
        recipient=recipient,
        subject=subject,
        body=payload.body,
    )
    return {"success": True, "reply_to": recipient, "result": result}


@router.post("/forward")
async def forward_email(
    payload: ForwardEmailPayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Forward an email to another recipient."""
    details = await IntegrationsService.get_email_details(db, current_user.id, payload.message_id)
    email_data = details.get("email", {})
    subject = email_data.get("subject", "Forwarded Message")
    if not subject.lower().startswith("fwd:"):
        subject = f"Fwd: {subject}"

    forward_body = f"{payload.comment or ''}\n\n---------- Forwarded message ---------\nFrom: {email_data.get('sender')}\nSubject: {email_data.get('subject')}\nDate: {email_data.get('date')}\n\n{email_data.get('body', '')}"

    result = await IntegrationsService.send_email(
        db=db,
        user_id=current_user.id,
        recipient=payload.to,
        subject=subject,
        body=forward_body,
    )
    return {"success": True, "forwarded_to": payload.to, "result": result}


@router.post("/extract-tasks")
async def extract_tasks_from_email(
    payload: ExtractTasksPayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Email-to-Task Automation: Extract deadlines, create tasks, and prevent duplicates."""
    return await IntegrationsService.extract_tasks_from_email_content(
        db=db,
        user_id=current_user.id,
        message_id=payload.message_id,
        custom_title=payload.custom_title,
    )


@router.get("/intelligence-summary")
async def get_email_intelligence(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve email intelligence widget data for the Command Center."""
    return await IntegrationsService.get_email_intelligence_summary(
        db=db,
        user_id=current_user.id,
    )
