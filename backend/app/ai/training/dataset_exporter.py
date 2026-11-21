import json
from typing import Any, Dict, List, Optional
import uuid
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.ai_system import TrainingDatasetRecord


async def record_training_pair(
    db: AsyncSession,
    user_id: uuid.UUID,
    agent_name: str,
    system_prompt: str,
    user_input: str,
    expected_output: str,
    dataset_version: str = "v1.0",
    feedback_score: Optional[int] = None,
    is_approved: bool = True,
) -> TrainingDatasetRecord:
    """Record an interaction pair for future offline fine-tuning, strictly subject to user consent."""
    rec = TrainingDatasetRecord(
        user_id=user_id,
        dataset_version=dataset_version,
        agent_name=agent_name,
        system_prompt=system_prompt,
        user_input=user_input,
        expected_output=expected_output,
        user_feedback_score=feedback_score,
        is_approved_for_training=is_approved,
    )
    db.add(rec)
    await db.commit()
    await db.refresh(rec)
    return rec


async def export_approved_training_data(
    db: AsyncSession,
    user_id: Optional[uuid.UUID] = None,
    dataset_version: Optional[str] = None,
    limit: int = 500,
) -> str:
    """Export approved training pairs in standard OpenAI/ShareGPT JSONL format for fine-tuning."""
    stmt = select(TrainingDatasetRecord).where(TrainingDatasetRecord.is_approved_for_training.is_(True))
    if user_id:
        stmt = stmt.where(TrainingDatasetRecord.user_id == user_id)
    if dataset_version:
        stmt = stmt.where(TrainingDatasetRecord.dataset_version == dataset_version)

    stmt = stmt.order_by(TrainingDatasetRecord.created_at.desc()).limit(limit)
    res = await db.execute(stmt)
    records = res.scalars().all()

    jsonl_lines: List[str] = []
    for r in records:
        entry = {
            "messages": [
                {"role": "system", "content": r.system_prompt},
                {"role": "user", "content": r.user_input},
                {"role": "assistant", "content": r.expected_output},
            ],
            "metadata": {
                "agent": r.agent_name,
                "version": r.dataset_version,
                "score": r.user_feedback_score,
            },
        }
        jsonl_lines.append(json.dumps(entry))

    return "\n".join(jsonl_lines)


async def get_dataset_statistics(db: AsyncSession, user_id: uuid.UUID) -> Dict[str, Any]:
    """Retrieve fine-tuning dataset metrics for transparency."""
    total = (
        await db.execute(
            select(func.count(TrainingDatasetRecord.id)).where(TrainingDatasetRecord.user_id == user_id)
        )
    ).scalar() or 0

    approved = (
        await db.execute(
            select(func.count(TrainingDatasetRecord.id)).where(
                TrainingDatasetRecord.user_id == user_id,
                TrainingDatasetRecord.is_approved_for_training.is_(True),
            )
        )
    ).scalar() or 0

    return {"total_collected": total, "approved_for_fine_tuning": approved}
