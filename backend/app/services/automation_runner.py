from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.automation import AutomationRule, AutomationTriggerLog, Notification
from app.models.calendar import DailyPlan
from app.models.productivity import Task
from app.models.user import User


class AutomationRunnerService:
    """Evaluates and executes active automation rules, logging trigger events."""

    @classmethod
    async def evaluate_user_automations(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
    ) -> List[Dict[str, Any]]:
        """Evaluate all active automation rules for a given user."""
        res = await db.execute(
            select(AutomationRule).where(
                AutomationRule.user_id == user_id,
                AutomationRule.is_active.is_(True),
            )
        )
        rules = res.scalars().all()
        results = []

        now = datetime.now(timezone.utc)

        for rule in rules:
            triggered = False
            output: Dict[str, Any] = {}

            # Evaluate Trigger
            if rule.trigger_type == "schedule":
                # Check if it was already triggered within the last 6 hours
                if not rule.last_triggered_at or (now - rule.last_triggered_at).total_seconds() > 21600:
                    triggered = True
            elif rule.trigger_type == "task_overdue":
                res_overdue = await db.execute(
                    select(Task).where(
                        Task.user_id == user_id,
                        Task.status == "todo",
                        Task.due_date < now,
                    ).limit(5)
                )
                overdue_tasks = res_overdue.scalars().all()
                if overdue_tasks:
                    triggered = True
                    output["overdue_count"] = len(overdue_tasks)
                    output["tasks"] = [t.title for t in overdue_tasks]
            elif rule.trigger_type in ("habit_missed", "deadline_approaching"):
                triggered = True

            if triggered:
                # Execute Action
                action_status = "success"
                if rule.action_type == "generate_plan":
                    notif = Notification(
                        user_id=user_id,
                        title=f"Automated Plan Generated: {rule.name}",
                        message=f"Sync has synthesized your daily priorities and calendar focus blocks.",
                        category="insight",
                        action_url="/calendar",
                    )
                    db.add(notif)
                    output["notification_sent"] = True
                elif rule.action_type == "daily_review":
                    notif = Notification(
                        user_id=user_id,
                        title=f"Evening Reflection: {rule.name}",
                        message="Your daily productivity score and pending task status have been updated.",
                        category="insight",
                        action_url="/tasks",
                    )
                    db.add(notif)
                    output["review_generated"] = True
                elif rule.action_type == "reschedule_suggest":
                    notif = Notification(
                        user_id=user_id,
                        title=f"Reschedule Suggestion: {rule.name}",
                        message="Detected overdue tasks. Click to approve shifting them to tomorrow's slots.",
                        category="reminder",
                        action_url="/calendar",
                    )
                    db.add(notif)
                    output["reschedule_suggested"] = True
                else:
                    notif = Notification(
                        user_id=user_id,
                        title=rule.name,
                        message=rule.action_config.get("message", "Automation notification triggered."),
                        category="reminder",
                        action_url="/dashboard",
                    )
                    db.add(notif)
                    output["notified"] = True

                rule.last_triggered_at = now

                # Record Trigger Log
                log = AutomationTriggerLog(
                    automation_rule_id=rule.id,
                    user_id=user_id,
                    trigger_event=rule.trigger_type,
                    status=action_status,
                    output_summary=output,
                    executed_at=now,
                )
                db.add(log)
                results.append({
                    "rule_id": str(rule.id),
                    "rule_name": rule.name,
                    "trigger_type": rule.trigger_type,
                    "action_type": rule.action_type,
                    "status": action_status,
                    "output": output,
                })

        if results:
            await db.commit()

        return results
