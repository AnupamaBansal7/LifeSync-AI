import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.productivity import Task, TaskHistory
from app.models.user import User
from app.schemas.productivity import TaskCreate, TaskOut, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("", response_model=List[TaskOut])
async def list_tasks(
    role_context: Optional[str] = Query(default=None),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    priority: Optional[str] = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Task).where(Task.user_id == current_user.id)
    if role_context and role_context != "all":
        stmt = stmt.where(Task.role_context == role_context)
    if status_filter:
        stmt = stmt.where(Task.status == status_filter)
    if priority:
        stmt = stmt.where(Task.priority == priority)
    stmt = stmt.order_by(Task.created_at.desc())
    res = await db.execute(stmt)
    return res.scalars().all()


@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
async def create_task(
    payload: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = Task(user_id=current_user.id, **payload.model_dump())
    db.add(task)
    await db.flush()
    db.add(
        TaskHistory(
            task_id=task.id,
            user_id=current_user.id,
            action="created",
            changes={"title": task.title, "status": task.status},
            actor="user",
        )
    )
    await db.commit()
    await db.refresh(task)
    return task


@router.patch("/{task_id}", response_model=TaskOut)
async def update_task(
    task_id: uuid.UUID,
    payload: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(select(Task).where(Task.id == task_id, Task.user_id == current_user.id))
    task = res.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    changes = payload.model_dump(exclude_unset=True)
    for key, val in changes.items():
        setattr(task, key, val)

    if changes.get("status") == "completed" and task.completed_at is None:
        task.completed_at = datetime.now(timezone.utc)
    elif "status" in changes and changes["status"] != "completed":
        task.completed_at = None

    db.add(
        TaskHistory(
            task_id=task.id,
            user_id=current_user.id,
            action="updated",
            changes={k: str(v) for k, v in changes.items()},
            actor="user",
        )
    )
    await db.commit()
    await db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(select(Task).where(Task.id == task_id, Task.user_id == current_user.id))
    task = res.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    await db.delete(task)
    await db.commit()