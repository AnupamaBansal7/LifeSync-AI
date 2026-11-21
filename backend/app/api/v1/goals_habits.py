import uuid
from datetime import timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.productivity import Goal, Habit, HabitLog, Milestone
from app.models.user import User
from app.schemas.productivity import (
    GoalCreate,
    GoalOut,
    GoalUpdate,
    HabitCreate,
    HabitLogRequest,
    HabitOut,
    MilestoneCreate,
    MilestoneOut,
    MilestoneUpdate,
)

router = APIRouter(tags=["Goals & Habits"])


def _recompute_goal_progress(goal: Goal) -> None:
    if not goal.milestones:
        return
    done = sum(1 for m in goal.milestones if m.is_completed)
    goal.progress_percent = round((done / len(goal.milestones)) * 100.0, 1)
    if goal.progress_percent >= 100.0:
        goal.status = "completed"


# --- GOALS ---
@router.get("/goals", response_model=List[GoalOut])
async def list_goals(
    role_context: Optional[str] = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Goal)
        .where(Goal.user_id == current_user.id)
        .options(selectinload(Goal.milestones))
        .order_by(Goal.created_at.desc())
    )
    if role_context and role_context != "all":
        stmt = stmt.where(Goal.role_context == role_context)
    res = await db.execute(stmt)
    return res.scalars().all()


@router.post("/goals", response_model=GoalOut, status_code=status.HTTP_201_CREATED)
async def create_goal(
    payload: GoalCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    goal = Goal(
        user_id=current_user.id,
        title=payload.title,
        description=payload.description,
        horizon=payload.horizon,
        role_context=payload.role_context,
        category=payload.category,
        target_date=payload.target_date,
    )
    db.add(goal)
    await db.flush()

    for idx, ms in enumerate(payload.milestones):
        db.add(
            Milestone(
                goal_id=goal.id,
                title=ms.title,
                target_date=ms.target_date,
                order_index=ms.order_index or idx,
            )
        )

    await db.commit()
    res = await db.execute(select(Goal).where(Goal.id == goal.id).options(selectinload(Goal.milestones)))
    return res.scalar_one()


@router.patch("/goals/{goal_id}", response_model=GoalOut)
async def update_goal(
    goal_id: uuid.UUID,
    payload: GoalUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(Goal).where(Goal.id == goal_id, Goal.user_id == current_user.id).options(selectinload(Goal.milestones))
    )
    goal = res.scalar_one_or_none()
    if not goal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")

    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(goal, k, v)
    await db.commit()
    await db.refresh(goal)
    return goal


@router.post("/goals/{goal_id}/milestones", response_model=MilestoneOut, status_code=status.HTTP_201_CREATED)
async def add_milestone(
    goal_id: uuid.UUID,
    payload: MilestoneCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(Goal).where(Goal.id == goal_id, Goal.user_id == current_user.id).options(selectinload(Goal.milestones))
    )
    goal = res.scalar_one_or_none()
    if not goal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")

    ms = Milestone(goal_id=goal.id, **payload.model_dump())
    db.add(ms)
    await db.flush()
    goal.milestones.append(ms)
    _recompute_goal_progress(goal)
    await db.commit()
    await db.refresh(ms)
    return ms


@router.patch("/milestones/{milestone_id}", response_model=MilestoneOut)
async def update_milestone(
    milestone_id: uuid.UUID,
    payload: MilestoneUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(select(Milestone).where(Milestone.id == milestone_id))
    ms = res.scalar_one_or_none()
    if not ms:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Milestone not found")

    goal_res = await db.execute(
        select(Goal).where(Goal.id == ms.goal_id, Goal.user_id == current_user.id).options(selectinload(Goal.milestones))
    )
    goal = goal_res.scalar_one_or_none()
    if not goal:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(ms, k, v)
    _recompute_goal_progress(goal)
    await db.commit()
    await db.refresh(ms)
    return ms


# --- HABITS ---
@router.get("/habits", response_model=List[HabitOut])
async def list_habits(
    role_context: Optional[str] = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Habit).where(Habit.user_id == current_user.id, Habit.is_active.is_(True))
    if role_context and role_context != "all":
        stmt = stmt.where(Habit.role_context == role_context)
    res = await db.execute(stmt.order_by(Habit.created_at.desc()))
    return res.scalars().all()


@router.post("/habits", response_model=HabitOut, status_code=status.HTTP_201_CREATED)
async def create_habit(
    payload: HabitCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    habit = Habit(user_id=current_user.id, **payload.model_dump())
    db.add(habit)
    await db.commit()
    await db.refresh(habit)
    return habit


@router.post("/habits/{habit_id}/log", response_model=HabitOut)
async def log_habit_checkin(
    habit_id: uuid.UUID,
    payload: HabitLogRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(select(Habit).where(Habit.id == habit_id, Habit.user_id == current_user.id))
    habit = res.scalar_one_or_none()
    if not habit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Habit not found")

    log_res = await db.execute(
        select(HabitLog).where(HabitLog.habit_id == habit.id, HabitLog.log_date == payload.log_date)
    )
    existing_log = log_res.scalar_one_or_none()
    if existing_log:
        existing_log.completed = payload.completed
        existing_log.notes = payload.notes
    else:
        db.add(
            HabitLog(
                habit_id=habit.id,
                user_id=current_user.id,
                log_date=payload.log_date,
                completed=payload.completed,
                notes=payload.notes,
            )
        )

    await db.flush()
    all_logs_res = await db.execute(
        select(HabitLog.log_date)
        .where(HabitLog.habit_id == habit.id, HabitLog.completed.is_(True))
        .order_by(HabitLog.log_date.desc())
    )
    dates = list(all_logs_res.scalars().all())
    streak = 0
    if dates:
        cursor = dates[0]
        date_set = set(dates)
        while cursor in date_set:
            streak += 1
            cursor = cursor - timedelta(days=1)

    habit.current_streak = streak
    habit.longest_streak = max(habit.longest_streak, streak)
    await db.commit()
    await db.refresh(habit)
    return habit