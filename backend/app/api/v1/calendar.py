import uuid
from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.calendar import CalendarEvent, DailyPlan
from app.models.user import User
from app.schemas.productivity import CalendarEventCreate, CalendarEventOut, DailyPlanOut

router = APIRouter(prefix="/calendar", tags=["Calendar & Daily Plans"])


@router.get("/events", response_model=List[CalendarEventOut])
async def list_events(
    role_context: Optional[str] = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(CalendarEvent).where(CalendarEvent.user_id == current_user.id)
    if role_context and role_context != "all":
        stmt = stmt.where(CalendarEvent.role_context == role_context)
    res = await db.execute(stmt.order_by(CalendarEvent.start_time.asc()))
    return res.scalars().all()


@router.post("/events", response_model=CalendarEventOut, status_code=status.HTTP_201_CREATED)
async def create_event(
    payload: CalendarEventCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if payload.end_time <= payload.start_time:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="end_time must be after start_time")
    ev = CalendarEvent(user_id=current_user.id, **payload.model_dump())
    db.add(ev)
    await db.commit()
    await db.refresh(ev)
    return ev


@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(CalendarEvent).where(CalendarEvent.id == event_id, CalendarEvent.user_id == current_user.id)
    )
    ev = res.scalar_one_or_none()
    if not ev:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    await db.delete(ev)
    await db.commit()


@router.get("/daily-plans", response_model=List[DailyPlanOut])
async def list_daily_plans(
    plan_date: Optional[date] = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(DailyPlan).where(DailyPlan.user_id == current_user.id)
    if plan_date:
        stmt = stmt.where(DailyPlan.plan_date == plan_date)
    res = await db.execute(stmt.order_by(DailyPlan.created_at.desc()).limit(10))
    return res.scalars().all()