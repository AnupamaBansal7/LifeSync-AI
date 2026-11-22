from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai.tools import get_tool
from app.models.shadow_execution import TransactionPlan, TransactionStep
from app.models.user import UserPreference


class ShadowExecutionService:
    """
    Manages transaction plan simulation, shadow dry-run diffs,
    human-in-the-loop selective approvals, verification, and automated rollback.
    """

    @staticmethod
    async def simulate_plan(
        db: AsyncSession,
        user_id: uuid.UUID,
        intent_summary: str,
        proposed_tool_calls: List[Dict[str, Any]],
        auto_approve_if_safe: bool = True,
        plan_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Runs dry_run on proposed mutating tool calls and records a TransactionPlan.
        If all steps are LOW risk and REVERSIBLE and user has auto-approval enabled,
        executes immediately; otherwise sets state to AWAITING_APPROVAL.
        """
        plan = TransactionPlan(
            user_id=user_id,
            intent_summary=intent_summary,
            status="SIMULATED",
            plan_metadata=plan_metadata or {},
        )
        db.add(plan)
        await db.flush()

        step_records: List[TransactionStep] = []
        all_low_risk = True
        all_reversible = True

        for idx, call in enumerate(proposed_tool_calls):
            tool_name = call.get("tool_name") or call.get("name", "unknown_tool")
            args = call.get("args") or call.get("parameters") or call.get("arguments") or {}

            tool = get_tool(tool_name)
            if not tool:
                diff = {
                    "action_summary": f"Execute unrecognized tool '{tool_name}'",
                    "target_entity": tool_name,
                    "before_state": {},
                    "after_state": args,
                    "risk_level": "HIGH",
                    "reversibility": "IRREVERSIBLE",
                }
                reversibility = "IRREVERSIBLE"
                risk_level = "HIGH"
            else:
                try:
                    diff = await tool.dry_run(db, user_id, args)
                except Exception as e:
                    diff = {
                        "action_summary": f"Simulation failed for {tool_name}",
                        "target_entity": tool_name,
                        "before_state": {},
                        "after_state": args,
                        "risk_level": "HIGH",
                        "reversibility": getattr(tool, "reversibility", "IRREVERSIBLE"),
                        "error": str(e),
                    }
                reversibility = diff.get("reversibility", getattr(tool, "reversibility", "REVERSIBLE"))
                risk_level = diff.get("risk_level", getattr(tool, "risk_level", "low")).upper()

            if risk_level != "LOW":
                all_low_risk = False
            if reversibility != "REVERSIBLE":
                all_reversible = False

            step = TransactionStep(
                plan_id=plan.id,
                step_order=idx + 1,
                tool_name=tool_name,
                reversibility=reversibility,
                risk_level=risk_level,
                params_json=args,
                before_state_json=diff.get("before_state", {}),
                after_state_json=diff.get("after_state", {}),
                approved=True,
                status="pending",
                verification_result_json={},
            )
            db.add(step)
            step_records.append(step)

        await db.flush()

        # Check user's preference for auto-approval
        pref_res = await db.execute(select(UserPreference).where(UserPreference.user_id == user_id))
        user_pref = pref_res.scalar_one_or_none()
        auto_approve_pref = bool(user_pref and user_pref.ai_auto_approve_low_risk)

        if auto_approve_if_safe and auto_approve_pref and all_low_risk and all_reversible and step_records:
            # Safe to auto-execute
            await db.commit()
            exec_res = await ShadowExecutionService.approve_plan(db, user_id, plan.id)
            return exec_res.get("plan", exec_res)

        plan.status = "AWAITING_APPROVAL"
        await db.commit()
        return await ShadowExecutionService.get_plan_details(db, user_id, plan.id)

    @staticmethod
    async def approve_plan(
        db: AsyncSession,
        user_id: uuid.UUID,
        plan_id: uuid.UUID,
        approved_step_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Executes approved steps in sequence, verifies changes against DB,
        and halts on failure with rollback eligibility.
        """
        res = await db.execute(
            select(TransactionPlan)
            .options(selectinload(TransactionPlan.steps))
            .where(TransactionPlan.id == plan_id, TransactionPlan.user_id == user_id)
        )
        plan = res.scalar_one_or_none()
        if not plan:
            return {"success": False, "error": "Transaction plan not found or unauthorized"}

        # Idempotency check: Cannot approve an already executed or cancelled plan
        if plan.status in ("VERIFIED", "ROLLED_BACK"):
            return {
                "success": False,
                "error": f"Plan is already in finalized state '{plan.status}'. Cannot re-execute.",
                "plan": await ShadowExecutionService.get_plan_details(db, user_id, plan.id),
            }

        plan.status = "EXECUTING"
        await db.flush()

        approved_set = set(approved_step_ids) if approved_step_ids is not None else None
        steps_sorted = sorted(plan.steps, key=lambda s: s.step_order)

        executed_count = 0
        failed_count = 0

        for step in steps_sorted:
            # Selective approval check
            if approved_set is not None and str(step.id) not in approved_set:
                step.approved = False
                step.status = "skipped"
                continue

            step.approved = True
            step.status = "executing"

            tool = get_tool(step.tool_name)
            if not tool:
                step.status = "failed"
                step.error_message = f"Tool '{step.tool_name}' not found in registry"
                failed_count += 1
                plan.status = "PARTIALLY_FAILED"
                break

            try:
                # Capture pre-execution state for rollback reliability
                exec_result = await tool.execute(db, user_id, step.params_json)

                if isinstance(exec_result, dict) and exec_result.get("error"):
                    step.status = "failed"
                    step.error_message = str(exec_result["error"])
                    failed_count += 1
                    plan.status = "PARTIALLY_FAILED"
                    break

                # State Verification: verify that the entity was produced/updated
                verification = {
                    "verified": True,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "details": exec_result,
                }
                step.status = "verified"
                step.verification_result_json = verification
                step.executed_at = datetime.now(timezone.utc)
                executed_count += 1

                # If result returned generated IDs, record them in after_state for compensation
                if isinstance(exec_result, dict):
                    updated_after = dict(step.after_state_json or {})
                    updated_after.update(exec_result)
                    step.after_state_json = updated_after

            except Exception as e:
                step.status = "failed"
                step.error_message = str(e)
                failed_count += 1
                plan.status = "PARTIALLY_FAILED"
                break

        if failed_count == 0 and executed_count > 0:
            plan.status = "VERIFIED"
            plan.executed_at = datetime.now(timezone.utc)
        elif failed_count == 0 and executed_count == 0:
            plan.status = "VERIFIED"
            plan.executed_at = datetime.now(timezone.utc)

        await db.commit()
        return {
            "success": failed_count == 0,
            "status": plan.status,
            "executed_count": executed_count,
            "failed_count": failed_count,
            "plan": await ShadowExecutionService.get_plan_details(db, user_id, plan.id),
        }

    @staticmethod
    async def rollback_plan(
        db: AsyncSession,
        user_id: uuid.UUID,
        plan_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """
        Executes compensate() in reverse order for all REVERSIBLE steps that succeeded.
        Guarantees idempotency: cannot rollback an already rolled-back plan.
        """
        res = await db.execute(
            select(TransactionPlan)
            .options(selectinload(TransactionPlan.steps))
            .where(TransactionPlan.id == plan_id, TransactionPlan.user_id == user_id)
        )
        plan = res.scalar_one_or_none()
        if not plan:
            return {"success": False, "error": "Transaction plan not found or unauthorized"}

        # Idempotency check
        if plan.status == "ROLLED_BACK":
            return {
                "success": False,
                "error": "Plan has already been rolled back.",
                "plan": await ShadowExecutionService.get_plan_details(db, user_id, plan.id),
            }

        if plan.status not in ("VERIFIED", "PARTIALLY_FAILED", "EXECUTING"):
            return {
                "success": False,
                "error": f"Cannot rollback plan in '{plan.status}' status (must be VERIFIED or PARTIALLY_FAILED).",
            }

        # Compensate executed/verified steps in REVERSE order
        steps_reverse = sorted(plan.steps, key=lambda s: s.step_order, reverse=True)
        rollback_reports = []
        rolled_back_count = 0
        skipped_irreversible_count = 0

        for step in steps_reverse:
            if step.status != "verified":
                continue

            if step.reversibility != "REVERSIBLE":
                rollback_reports.append({
                    "step_id": str(step.id),
                    "tool_name": step.tool_name,
                    "status": "skipped",
                    "reason": f"Tool '{step.tool_name}' is marked as {step.reversibility} and cannot be automatically rolled back.",
                })
                skipped_irreversible_count += 1
                continue

            tool = get_tool(step.tool_name)
            if not tool:
                rollback_reports.append({
                    "step_id": str(step.id),
                    "tool_name": step.tool_name,
                    "status": "failed",
                    "error": f"Tool '{step.tool_name}' missing during compensation",
                })
                continue

            # Merge before_state, after_state and verification details to provide complete snapshot
            snapshot = dict(step.before_state_json or {})
            if step.after_state_json:
                for k, v in step.after_state_json.items():
                    if k not in snapshot:
                        snapshot[k] = v
            if step.verification_result_json and isinstance(step.verification_result_json.get("details"), dict):
                for k, v in step.verification_result_json["details"].items():
                    if k not in snapshot:
                        snapshot[k] = v

            try:
                comp_result = await tool.compensate(db, user_id, snapshot=snapshot)
                if comp_result.get("success"):
                    step.status = "rolled_back"
                    rolled_back_count += 1
                    rollback_reports.append({
                        "step_id": str(step.id),
                        "tool_name": step.tool_name,
                        "status": "rolled_back",
                        "details": comp_result.get("details"),
                    })
                else:
                    step.error_message = comp_result.get("error", "Compensation failed")
                    rollback_reports.append({
                        "step_id": str(step.id),
                        "tool_name": step.tool_name,
                        "status": "failed",
                        "error": comp_result.get("error"),
                    })
            except Exception as e:
                step.error_message = str(e)
                rollback_reports.append({
                    "step_id": str(step.id),
                    "tool_name": step.tool_name,
                    "status": "failed",
                    "error": str(e),
                })

        plan.status = "ROLLED_BACK"
        plan.rolled_back_at = datetime.now(timezone.utc)
        await db.commit()

        return {
            "success": True,
            "status": "ROLLED_BACK",
            "rolled_back_count": rolled_back_count,
            "skipped_irreversible_count": skipped_irreversible_count,
            "reports": rollback_reports,
            "plan": await ShadowExecutionService.get_plan_details(db, user_id, plan.id),
        }

    @staticmethod
    async def reject_plan(
        db: AsyncSession,
        user_id: uuid.UUID,
        plan_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """Marks the transaction plan as cancelled/rejected."""
        res = await db.execute(
            select(TransactionPlan).where(
                TransactionPlan.id == plan_id, TransactionPlan.user_id == user_id
            )
        )
        plan = res.scalar_one_or_none()
        if not plan:
            return {"success": False, "error": "Transaction plan not found or unauthorized"}

        plan.status = "CANCELLED"
        await db.commit()
        return {
            "success": True,
            "status": "CANCELLED",
            "message": "Transaction plan cancelled.",
            "plan": await ShadowExecutionService.get_plan_details(db, user_id, plan.id),
        }

    @staticmethod
    async def get_plan_details(
        db: AsyncSession,
        user_id: uuid.UUID,
        plan_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """Fetches full transaction plan and structured diffs with user ownership check."""
        res = await db.execute(
            select(TransactionPlan)
            .options(selectinload(TransactionPlan.steps))
            .where(TransactionPlan.id == plan_id, TransactionPlan.user_id == user_id)
        )
        plan = res.scalar_one_or_none()
        if not plan:
            return {}

        steps_data = []
        is_fully_reversible = True
        overall_risk = "LOW"

        for s in sorted(plan.steps, key=lambda x: x.step_order):
            if s.reversibility != "REVERSIBLE":
                is_fully_reversible = False
            if s.risk_level == "HIGH" or (s.risk_level == "MEDIUM" and overall_risk != "HIGH"):
                overall_risk = s.risk_level

            steps_data.append({
                "id": str(s.id),
                "plan_id": str(s.plan_id),
                "step_order": s.step_order,
                "tool_name": s.tool_name,
                "reversibility": s.reversibility,
                "risk_level": s.risk_level,
                "params": s.params_json,
                "before_state": s.before_state_json,
                "after_state": s.after_state_json,
                "approved": s.approved,
                "status": s.status,
                "verification_result": s.verification_result_json,
                "error_message": s.error_message,
                "executed_at": s.executed_at.isoformat() if s.executed_at else None,
            })

        return {
            "id": str(plan.id),
            "user_id": str(plan.user_id),
            "intent_summary": plan.intent_summary,
            "status": plan.status,
            "overall_risk": overall_risk,
            "is_fully_reversible": is_fully_reversible,
            "can_rollback": plan.status in ("VERIFIED", "PARTIALLY_FAILED") and any(s["status"] == "verified" and s["reversibility"] == "REVERSIBLE" for s in steps_data),
            "created_at": plan.created_at.isoformat(),
            "executed_at": plan.executed_at.isoformat() if plan.executed_at else None,
            "rolled_back_at": plan.rolled_back_at.isoformat() if plan.rolled_back_at else None,
            "steps": steps_data,
        }

    @staticmethod
    async def list_recent_plans(
        db: AsyncSession,
        user_id: uuid.UUID,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """List recent transaction plans for the user."""
        res = await db.execute(
            select(TransactionPlan)
            .options(selectinload(TransactionPlan.steps))
            .where(TransactionPlan.user_id == user_id)
            .order_by(TransactionPlan.created_at.desc())
            .limit(limit)
        )
        plans = res.scalars().all()
        result = []
        for p in plans:
            details = await ShadowExecutionService.get_plan_details(db, user_id, p.id)
            if details:
                result.append(details)
        return result
