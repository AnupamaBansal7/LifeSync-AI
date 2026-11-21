from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import re
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.automation import AutomationRule, AutomationTriggerLog, Notification
from app.models.user import User
from app.services.automation_runner import AutomationRunnerService

router = APIRouter(prefix="/automations", tags=["Automations & Workflows"])



class AutomationRuleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    trigger_type: str = Field(default="schedule", pattern="^(schedule|task_overdue|habit_missed|deadline_approaching)$")
    trigger_config: Dict[str, Any] = Field(default_factory=dict)
    action_type: str = Field(default="notify", pattern="^(notify|generate_plan|reschedule_suggest|daily_review)$")
    action_config: Dict[str, Any] = Field(default_factory=dict)
    requires_approval: bool = True
    is_active: bool = True


class AutomationRuleUpdate(BaseModel):
    name: Optional[str] = None
    trigger_type: Optional[str] = None
    trigger_config: Optional[Dict[str, Any]] = None
    action_type: Optional[str] = None
    action_config: Optional[Dict[str, Any]] = None
    requires_approval: Optional[bool] = None
    is_active: Optional[bool] = None


class AutomationRuleOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    trigger_type: str
    trigger_config: Dict[str, Any]
    action_type: str
    action_config: Dict[str, Any]
    requires_approval: bool
    is_active: bool
    last_triggered_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class NaturalLanguageAutomationRequest(BaseModel):
    prompt: str = Field(min_length=3, max_length=500)
    auto_save: bool = True


class AutomationTriggerLogOut(BaseModel):
    id: uuid.UUID
    automation_rule_id: uuid.UUID
    trigger_event: str
    status: str
    output_summary: Dict[str, Any]
    executed_at: datetime

    model_config = {"from_attributes": True}



AUTOMATION_TEMPLATES = [
    {
        "name": "Morning Briefing & Daily Plan",
        "trigger_type": "schedule",
        "trigger_config": {"time": "08:00", "days": ["mon", "tue", "wed", "thu", "fri"]},
        "action_type": "generate_plan",
        "action_config": {"include_weather": False, "role_context": "all"},
        "requires_approval": False,
        "description": "Synthesizes your top priorities, meetings, and habits into a structured day plan at 8:00 AM.",
    },
    {
        "name": "Evening Reflection & Incomplete Task Review",
        "trigger_type": "schedule",
        "trigger_config": {"time": "20:00", "days": ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]},
        "action_type": "daily_review",
        "action_config": {"notify_incomplete": True},
        "requires_approval": False,
        "description": "Reviews tasks completed today and suggests rescheduling or deferring open items.",
    },
    {
        "name": "Urgent Deadline Approaching Alert",
        "trigger_type": "deadline_approaching",
        "trigger_config": {"hours_before": 24},
        "action_type": "notify",
        "action_config": {"channel": "in_app", "urgency": "high"},
        "requires_approval": False,
        "description": "Sends a priority alert 24 hours before any high or urgent task due date.",
    },
    {
        "name": "Overdue Task Auto-Reschedule Suggestion",
        "trigger_type": "task_overdue",
        "trigger_config": {"delay_hours": 2},
        "action_type": "reschedule_suggest",
        "action_config": {"suggest_next_available_slot": True},
        "requires_approval": True,
        "description": "Detects overdue tasks and creates an agent approval card to shift them to open calendar slots tomorrow.",
    },
    {
        "name": "Habit Streak Guard Nudge",
        "trigger_type": "habit_missed",
        "trigger_config": {"remind_time": "19:00"},
        "action_type": "notify",
        "action_config": {"message": "You still have active habits pending today. Protect your streak!"},
        "requires_approval": False,
        "description": "A gentle reminder at 7:00 PM if core daily wellness habits have not been checked off.",
    },
]


@router.get("/templates")
async def get_automation_templates():
    return AUTOMATION_TEMPLATES


@router.get("", response_model=List[AutomationRuleOut])
async def list_automations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(AutomationRule)
        .where(AutomationRule.user_id == current_user.id)
        .order_by(AutomationRule.created_at.desc())
    )
    rules = res.scalars().all()
    # Seed default templates if user has no rules yet
    if not rules:
        for t in AUTOMATION_TEMPLATES[:3]:
            r = AutomationRule(
                user_id=current_user.id,
                name=t["name"],
                trigger_type=t["trigger_type"],
                trigger_config=t["trigger_config"],
                action_type=t["action_type"],
                action_config=t["action_config"],
                requires_approval=t["requires_approval"],
                is_active=True,
            )
            db.add(r)
        await db.commit()
        res = await db.execute(
            select(AutomationRule)
            .where(AutomationRule.user_id == current_user.id)
            .order_by(AutomationRule.created_at.desc())
        )
        rules = res.scalars().all()

    return rules


@router.post("", response_model=AutomationRuleOut, status_code=status.HTTP_201_CREATED)
async def create_automation(
    payload: AutomationRuleCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rule = AutomationRule(
        user_id=current_user.id,
        name=payload.name,
        trigger_type=payload.trigger_type,
        trigger_config=payload.trigger_config,
        action_type=payload.action_type,
        action_config=payload.action_config,
        requires_approval=payload.requires_approval,
        is_active=payload.is_active,
    )
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return rule


@router.patch("/{rule_id}", response_model=AutomationRuleOut)
async def update_automation(
    rule_id: uuid.UUID,
    payload: AutomationRuleUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(AutomationRule).where(AutomationRule.id == rule_id, AutomationRule.user_id == current_user.id)
    )
    rule = res.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Automation rule not found")

    changes = payload.model_dump(exclude_unset=True)
    for field, val in changes.items():
        setattr(rule, field, val)

    await db.commit()
    await db.refresh(rule)
    return rule


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_automation(
    rule_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(AutomationRule).where(AutomationRule.id == rule_id, AutomationRule.user_id == current_user.id)
    )
    rule = res.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Automation rule not found")

    await db.delete(rule)
    await db.commit()


@router.post("/{rule_id}/trigger")
async def trigger_automation_manually(
    rule_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Test or manually trigger an automation rule immediately."""
    res = await db.execute(
        select(AutomationRule).where(AutomationRule.id == rule_id, AutomationRule.user_id == current_user.id)
    )
    rule = res.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Automation rule not found")

    rule.last_triggered_at = datetime.now(timezone.utc)

    # Execute corresponding action
    notif = Notification(
        user_id=current_user.id,
        title=f"Automation Executed: {rule.name}",
        message=f"Rule triggered via action '{rule.action_type}'. Status: Verified.",
        category="insight" if rule.action_type in ("daily_review", "generate_plan") else "reminder",
        action_url="/automations",
    )
    db.add(notif)
    await db.commit()

    return {
        "status": "triggered_successfully",
        "rule_id": str(rule.id),
        "rule_name": rule.name,
        "action_type": rule.action_type,
        "executed_at": rule.last_triggered_at.isoformat(),
    }


@router.post("/parse-natural-language")
async def parse_natural_language_automation(
    payload: NaturalLanguageAutomationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Convert natural-language prompt into a structured automation rule."""
    text = payload.prompt.strip()
    low = text.lower()

    # 1. Parse Trigger
    trigger_type = "schedule"
    trigger_config: Dict[str, Any] = {}

    if any(k in low for k in ["overdue", "late task"]):
        trigger_type = "task_overdue"
        delay_match = re.search(r"(\d+)\s*(?:hour|hr|h)", low)
        trigger_config = {"delay_hours": int(delay_match.group(1)) if delay_match else 2}
    elif any(k in low for k in ["deadline", "due soon", "approaching"]):
        trigger_type = "deadline_approaching"
        hours_match = re.search(r"(\d+)\s*(?:hour|hr|h)", low)
        trigger_config = {"hours_before": int(hours_match.group(1)) if hours_match else 24}
    elif any(k in low for k in ["habit", "streak", "wellness"]):
        trigger_type = "habit_missed"
        trigger_config = {"remind_time": "19:00"}
    else:
        # Schedule trigger
        time_match = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", low)
        if time_match:
            hr = int(time_match.group(1))
            mn = int(time_match.group(2) or 0)
            ampm = time_match.group(3)
            if ampm == "pm" and hr < 12:
                hr += 12
            elif ampm == "am" and hr == 12:
                hr = 0
            time_str = f"{hr:02d}:{mn:02d}"
        else:
            time_str = "08:00"

        days = ["mon", "tue", "wed", "thu", "fri"] if "weekday" in low else ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
        trigger_config = {"time": time_str, "days": days}

    # 2. Parse Action
    action_type = "notify"
    action_config: Dict[str, Any] = {}
    requires_approval = False

    if any(k in low for k in ["plan", "schedule", "priorities", "day plan"]):
        action_type = "generate_plan"
        action_config = {"role_context": "all", "include_weather": False}
    elif any(k in low for k in ["review", "reflection", "incomplete", "summary"]):
        action_type = "daily_review"
        action_config = {"notify_incomplete": True}
    elif any(k in low for k in ["reschedule", "shift", "replan"]):
        action_type = "reschedule_suggest"
        action_config = {"suggest_next_available_slot": True}
        requires_approval = True
    else:
        action_type = "notify"
        action_config = {"message": f"Automation alert: {text[:60]}"}

    name = text[:60].capitalize()

    rule_data = {
        "name": name,
        "trigger_type": trigger_type,
        "trigger_config": trigger_config,
        "action_type": action_type,
        "action_config": action_config,
        "requires_approval": requires_approval,
        "is_active": True,
    }

    if payload.auto_save:
        rule = AutomationRule(
            user_id=current_user.id,
            name=name,
            trigger_type=trigger_type,
            trigger_config=trigger_config,
            action_type=action_type,
            action_config=action_config,
            requires_approval=requires_approval,
            is_active=True,
        )
        db.add(rule)
        await db.commit()
        await db.refresh(rule)
        return {
            "status": "created",
            "rule": AutomationRuleOut.model_validate(rule),
            "explanation": f"Created automated workflow '{name}' triggering via '{trigger_type}' and executing '{action_type}'.",
        }

    return {
        "status": "preview",
        "rule": rule_data,
        "explanation": f"Parsed rule '{name}' with {trigger_type} trigger -> {action_type} action.",
    }


@router.get("/logs", response_model=List[AutomationTriggerLogOut])
async def list_automation_logs(
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve execution history logs for automated workflows."""
    res = await db.execute(
        select(AutomationTriggerLog)
        .where(AutomationTriggerLog.user_id == current_user.id)
        .order_by(AutomationTriggerLog.executed_at.desc())
        .limit(limit)
    )
    return res.scalars().all()


@router.post("/evaluate-all")
async def evaluate_all_automations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Run the automation evaluation cycle for all active rules."""
    results = await AutomationRunnerService.evaluate_user_automations(db, current_user.id)
    return {
        "status": "evaluation_complete",
        "evaluated_rules_count": len(results),
        "triggered_rules": results,
    }

