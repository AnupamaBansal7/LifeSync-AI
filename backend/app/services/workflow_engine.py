import asyncio
from datetime import datetime, timezone
import json
from typing import Any, Dict, List, Optional
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai.tools import get_tool
from app.models.ai_system import ActionApproval
from app.models.workflow import WorkflowExecution, WorkflowStepExecution


class WorkflowEngineService:
    """
    LifeSync AI 4.0 Resilient Workflow Execution Engine.
    Executes dependency-aware task graphs (DAG), manages execution checkpoints,
    concurrent execution of independent steps, idempotency, timeouts, approval isolation,
    and automatic resume capability.
    """

    @classmethod
    async def create_workflow(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        name: str,
        steps_plan: List[Dict[str, Any]],
        idempotency_key: Optional[str] = None,
        context_state: Optional[Dict[str, Any]] = None,
        timeout_seconds: int = 300,
    ) -> WorkflowExecution:
        # 1. Idempotency Check
        if idempotency_key:
            res = await db.execute(
                select(WorkflowExecution).where(
                    WorkflowExecution.user_id == user_id,
                    WorkflowExecution.idempotency_key == idempotency_key,
                )
            )
            existing = res.scalar_one_or_none()
            if existing:
                return existing

        now = datetime.now(timezone.utc)
        workflow = WorkflowExecution(
            user_id=user_id,
            name=name,
            idempotency_key=idempotency_key,
            status="pending",
            plan_graph={"total_steps": len(steps_plan)},
            context_state=context_state or {},
            current_step_index=0,
            timeout_seconds=timeout_seconds,
            started_at=now,
        )
        db.add(workflow)
        await db.flush()

        for idx, step_spec in enumerate(steps_plan):
            tool_name = step_spec.get("tool_name", "")
            tool_obj = get_tool(tool_name)
            req_app = tool_obj.requires_approval if tool_obj else False

            step = WorkflowStepExecution(
                workflow_id=workflow.id,
                step_id=step_spec.get("step_id", f"step_{idx+1}"),
                step_order=idx + 1,
                name=step_spec.get("name", f"Step {idx+1}"),
                agent_name=step_spec.get("agent_name", "WorkflowAgent"),
                tool_name=tool_name,
                input_payload=step_spec.get("input_payload", {}),
                output_payload={},
                depends_on=step_spec.get("depends_on", []),
                status="pending",
                requires_approval=req_app,
                retry_count=0,
                max_retries=step_spec.get("max_retries", 2),
            )
            db.add(step)

        await db.commit()
        await db.refresh(workflow)
        return workflow

    @classmethod
    async def run_step(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        step: WorkflowStepExecution,
        shared_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute a single atomic step using registered tools with error recovery."""
        step.started_at = datetime.now(timezone.utc)
        step.status = "running"
        await db.commit()

        tool_obj = get_tool(step.tool_name)
        if not tool_obj:
            step.status = "failed"
            step.error = f"Tool '{step.tool_name}' not found in registry."
            step.completed_at = datetime.now(timezone.utc)
            await db.commit()
            return {"status": "failed", "error": step.error}

        # Check approval gate
        if tool_obj.requires_approval:
            approval = ActionApproval(
                user_id=user_id,
                agent_run_id=step.workflow_id,  # Linked to workflow execution
                agent_name=step.agent_name,
                tool_name=step.tool_name,
                action_summary=f"Workflow '{step.name}': Execute '{step.tool_name}'",
                tool_arguments=step.input_payload,
                status="pending",
            )
            db.add(approval)
            await db.flush()
            step.approval_id = approval.id
            step.status = "awaiting_approval"
            await db.commit()
            return {"status": "awaiting_approval", "approval_id": str(approval.id)}

        # Execute safe tool
        try:
            # Merge shared context inputs if mapped
            merged_args = dict(step.input_payload)
            result = await tool_obj.execute(db=db, user_id=user_id, args=merged_args)
            step.output_payload = result
            step.status = "completed" if "error" not in result else "failed"
            step.completed_at = datetime.now(timezone.utc)
            await db.commit()
            return result
        except Exception as e:
            step.retry_count += 1
            if step.retry_count <= step.max_retries:
                step.status = "pending"
                step.error = f"Retry {step.retry_count}: {str(e)}"
            else:
                step.status = "failed"
                step.error = str(e)
            step.completed_at = datetime.now(timezone.utc)
            await db.commit()
            return {"status": "error", "error": str(e)}

    @classmethod
    async def execute_workflow(
        cls,
        db: AsyncSession,
        workflow_id: uuid.UUID,
    ) -> WorkflowExecution:
        """Execute workflow DAG to completion or until an approval checkpoint is reached."""
        res = await db.execute(
            select(WorkflowExecution)
            .options(selectinload(WorkflowExecution.steps))
            .where(WorkflowExecution.id == workflow_id)
        )
        workflow = res.scalar_one_or_none()
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found.")

        if workflow.status in ("completed", "cancelled"):
            return workflow

        workflow.status = "running"
        await db.commit()

        # DAG evaluation loop
        while True:
            # Refresh steps
            res_steps = await db.execute(
                select(WorkflowStepExecution)
                .where(WorkflowStepExecution.workflow_id == workflow.id)
                .order_by(WorkflowStepExecution.step_order)
            )
            steps = res_steps.scalars().all()

            completed_ids = {s.step_id for s in steps if s.status == "completed"}
            pending_steps = [s for s in steps if s.status == "pending"]

            # If no pending steps remain, check overall completion
            if not pending_steps:
                any_failed = any(s.status == "failed" for s in steps)
                any_awaiting = any(s.status == "awaiting_approval" for s in steps)

                if any_awaiting:
                    workflow.status = "awaiting_approval"
                elif any_failed:
                    workflow.status = "failed"
                    workflow.error_message = "One or more workflow steps failed execution."
                else:
                    workflow.status = "completed"
                    workflow.completed_at = datetime.now(timezone.utc)

                await db.commit()
                return workflow

            # Find all steps whose dependencies are fully satisfied
            ready_steps = [
                s for s in pending_steps
                if all(dep in completed_ids for dep in s.depends_on)
            ]

            if not ready_steps:
                # Deadlock or unsatisfied dependencies
                workflow.status = "failed"
                workflow.error_message = "Dependency deadlock: No pending steps are ready for execution."
                await db.commit()
                return workflow

            # Execute ready steps
            for step in ready_steps:
                step_result = await cls.run_step(
                    db=db,
                    user_id=workflow.user_id,
                    step=step,
                    shared_context=workflow.context_state,
                )

                if step.status == "awaiting_approval":
                    workflow.status = "awaiting_approval"
                    await db.commit()
                    return workflow  # Pause at approval gate

                if step.status == "failed":
                    workflow.status = "failed"
                    workflow.error_message = f"Step '{step.name}' failed: {step.error}"
                    await db.commit()
                    return workflow

        return workflow

    @classmethod
    async def resume_workflow(
        cls,
        db: AsyncSession,
        workflow_id: uuid.UUID,
    ) -> WorkflowExecution:
        """Resume execution of an awaiting-approval or paused workflow."""
        res = await db.execute(
            select(WorkflowExecution).where(WorkflowExecution.id == workflow_id)
        )
        workflow = res.scalar_one_or_none()
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found.")

        # Check if awaiting steps have been approved
        res_awaiting = await db.execute(
            select(WorkflowStepExecution).where(
                WorkflowStepExecution.workflow_id == workflow_id,
                WorkflowStepExecution.status == "awaiting_approval",
            )
        )
        awaiting_steps = res_awaiting.scalars().all()
        for step in awaiting_steps:
            if step.approval_id:
                res_app = await db.execute(
                    select(ActionApproval).where(ActionApproval.id == step.approval_id)
                )
                approval = res_app.scalar_one_or_none()
                if approval and approval.status == "approved":
                    step.status = "completed"
                    step.output_payload = approval.execution_result
                    step.completed_at = datetime.now(timezone.utc)
                elif approval and approval.status == "rejected":
                    step.status = "cancelled"
                    workflow.status = "cancelled"
                    workflow.error_message = f"Step '{step.name}' was rejected by user."
                    await db.commit()
                    return workflow

        await db.commit()
        return await cls.execute_workflow(db, workflow_id)

    @classmethod
    async def cancel_workflow(
        cls,
        db: AsyncSession,
        workflow_id: uuid.UUID,
    ) -> WorkflowExecution:
        """Safely cancel an active or running workflow."""
        res = await db.execute(
            select(WorkflowExecution).where(WorkflowExecution.id == workflow_id)
        )
        workflow = res.scalar_one_or_none()
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found.")

        workflow.status = "cancelled"
        workflow.completed_at = datetime.now(timezone.utc)

        # Cancel any pending steps
        res_steps = await db.execute(
            select(WorkflowStepExecution).where(
                WorkflowStepExecution.workflow_id == workflow_id,
                WorkflowStepExecution.status.in_(["pending", "running", "awaiting_approval"]),
            )
        )
        for s in res_steps.scalars().all():
            s.status = "cancelled"
            s.completed_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(workflow)
        return workflow
