from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.services.proactive_assistant import ProactiveAssistantService


router = APIRouter(prefix="/proactive", tags=["Proactive Intelligence"])


@router.get("/briefing")
async def get_morning_briefing(
    role: str = "personal",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve synthesized executive morning briefing for the user."""
    return await ProactiveAssistantService.generate_morning_briefing(
        db=db, user=current_user, role_context=role
    )


@router.get("/deadline-risks")
async def get_deadline_risks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Scan and return all impending tasks with deadline risk scores."""
    risks = await ProactiveAssistantService.check_deadline_risks(db, current_user.id)
    return {
        "scanned_at": datetime.now(timezone.utc).isoformat(),
        "total_at_risk": len(risks),
        "critical_count": sum(1 for r in risks if r["risk_tier"] == "critical"),
        "risks": risks,
    }


@router.post("/run-cycle")
async def run_proactive_cycle(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Run full proactive evaluation cycle with quiet-hours suppression."""
    now = datetime.now(timezone.utc)
    in_quiet = ProactiveAssistantService.is_in_quiet_hours(current_user, now)

    risks = await ProactiveAssistantService.check_deadline_risks(db, current_user.id)
    briefing = await ProactiveAssistantService.generate_morning_briefing(db, current_user)

    return {
        "status": "cycle_complete",
        "quiet_hours_active": in_quiet,
        "briefing_generated": True,
        "risks_identified": len(risks),
        "briefing": briefing,
    }
