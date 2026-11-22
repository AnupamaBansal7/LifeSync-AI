import asyncio
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.ai.tools import ALL_TOOLS, get_tool
from app.ai.tools.base import Reversibility
from app.ai.tools.calendar_tools import CreateCalendarBlockTool, ListCalendarEventsTool
from app.ai.tools.habit_tools import CreateHabitTool, ListHabitsTool
from app.ai.tools.task_tools import CreateTaskTool, ListTasksTool, UpdateTaskStatusTool
from app.api.v1.router import api_router
from app.models.calendar import CalendarEvent
from app.models.productivity import Habit, Task
from app.models.shadow_execution import TransactionPlan, TransactionStep
from app.models.user import UserPreference
from app.services.shadow_execution_service import ShadowExecutionService


# ============================================================================
# 1. TOOL REVERSIBILITY & DRY-RUN CONTRACT
# ============================================================================

def test_tool_reversibility_contract():
    """Verify tool base class reversibility defaults and mutating tool properties."""
    create_task = CreateTaskTool()
    assert create_task.is_mutating is True
    assert create_task.reversibility == Reversibility.REVERSIBLE

    update_task = UpdateTaskStatusTool()
    assert update_task.is_mutating is True
    assert update_task.reversibility == Reversibility.REVERSIBLE

    create_cal = CreateCalendarBlockTool()
    assert create_cal.is_mutating is True
    assert create_cal.reversibility == Reversibility.REVERSIBLE

    create_habit = CreateHabitTool()
    assert create_habit.is_mutating is True
    assert create_habit.reversibility == Reversibility.REVERSIBLE

    # Read-only tools must have is_mutating=False
    list_tasks = ListTasksTool()
    assert list_tasks.is_mutating is False
    assert list_tasks.reversibility == Reversibility.REVERSIBLE

    list_cal = ListCalendarEventsTool()
    assert list_cal.is_mutating is False

    list_habits = ListHabitsTool()
    assert list_habits.is_mutating is False


# ============================================================================
# 2. DRY-RUN SIMULATION (NO STATE MUTATIONS)
# ============================================================================

def test_create_task_dry_run_diff_without_mutation():
    """Verify CreateTaskTool dry_run generates correct before/after diffs without DB mutations."""
    async def _run():
        tool = CreateTaskTool()
        mock_db = AsyncMock()
        user_id = uuid.uuid4()
        params = {
            "title": "Build Shadow Engine",
            "priority": "high",
            "role_context": "engineering",
            "estimated_minutes": 60,
        }

        diff = await tool.dry_run(mock_db, user_id, params)

        assert diff["reversibility"] == "REVERSIBLE"
        assert diff["risk_level"] == "LOW"
        assert diff["target_entity"] == "Task"
        assert diff["before_state"] == {}
        assert diff["after_state"]["title"] == "Build Shadow Engine"
        assert diff["after_state"]["priority"] == "high"
        assert diff["after_state"]["status"] == "todo"

        # Crucial: DB must NOT have had any writes or commits
        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()

    asyncio.run(_run())


def test_update_task_status_dry_run_captures_before_state():
    """Verify UpdateTaskStatusTool dry_run queries current state and builds precise diff."""
    async def _run():
        tool = UpdateTaskStatusTool()
        mock_db = AsyncMock()
        user_id = uuid.uuid4()
        task_id = uuid.uuid4()

        fake_task = Task(
            id=task_id,
            user_id=user_id,
            title="Deploy Feature",
            status="todo",
        )

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [fake_task]
        mock_db.execute.return_value = mock_result

        diff = await tool.dry_run(mock_db, user_id, {"title_query": "Deploy Feature", "status": "completed"})

        assert diff["reversibility"] == "REVERSIBLE"
        assert diff["risk_level"] == "LOW"
        assert diff["before_state"]["status"] == "todo"
        assert diff["after_state"]["status"] == "completed"

        # DB not mutated during dry-run
        mock_db.commit.assert_not_called()

    asyncio.run(_run())


def test_create_calendar_block_dry_run():
    """Verify CreateCalendarBlockTool dry_run simulates calendar reservation."""
    async def _run():
        tool = CreateCalendarBlockTool()
        mock_db = AsyncMock()
        user_id = uuid.uuid4()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        diff = await tool.dry_run(
            mock_db,
            user_id,
            {
                "title": "Deep Work Sprint",
                "start_time": "2026-11-23T10:00:00",
                "duration_minutes": 90,
                "role_context": "engineering",
            },
        )

        assert diff["reversibility"] == "REVERSIBLE"
        assert diff["risk_level"] == "LOW"
        assert diff["target_entity"] == "CalendarEvent"
        assert diff["after_state"]["title"] == "Deep Work Sprint"
        assert "start_time" in diff["after_state"]
        mock_db.add.assert_not_called()

    asyncio.run(_run())


def test_create_habit_dry_run():
    """Verify CreateHabitTool dry_run simulates habit creation."""
    async def _run():
        tool = CreateHabitTool()
        mock_db = AsyncMock()
        user_id = uuid.uuid4()

        diff = await tool.dry_run(
            mock_db,
            user_id,
            {"title": "Morning Meditation", "target_frequency": "daily", "role_context": "personal"},
        )

        assert diff["reversibility"] == "REVERSIBLE"
        assert diff["risk_level"] == "LOW"
        assert diff["target_entity"] == "Habit"
        assert diff["after_state"]["title"] == "Morning Meditation"
        mock_db.add.assert_not_called()

    asyncio.run(_run())


# ============================================================================
# 3. TOOL COMPENSATION (ROLLBACK IMPLEMENTATION)
# ============================================================================

def test_create_task_compensation():
    """Verify CreateTaskTool compensate deletes the task created during execution."""
    async def _run():
        tool = CreateTaskTool()
        mock_db = AsyncMock()
        user_id = uuid.uuid4()
        task_id = uuid.uuid4()

        res = await tool.compensate(mock_db, user_id, snapshot={"created_task_id": str(task_id)})

        assert res["success"] is True
        assert res["restored_entity_id"] == str(task_id)
        mock_db.execute.assert_called()
        mock_db.commit.assert_called_once()

    asyncio.run(_run())


def test_update_task_status_compensation():
    """Verify UpdateTaskStatusTool compensate restores previous status."""
    async def _run():
        tool = UpdateTaskStatusTool()
        mock_db = AsyncMock()
        user_id = uuid.uuid4()
        task_id = uuid.uuid4()

        fake_task = Task(id=task_id, user_id=user_id, title="Deploy Feature", status="completed")
        mock_res = MagicMock()
        mock_res.scalar_one_or_none.return_value = fake_task
        mock_db.execute.return_value = mock_res

        res = await tool.compensate(
            mock_db,
            user_id,
            snapshot={"task_id": str(task_id), "status": "todo"},
        )

        assert res["success"] is True
        assert fake_task.status == "todo"
        mock_db.commit.assert_called_once()

    asyncio.run(_run())


def test_create_calendar_block_compensation():
    """Verify CreateCalendarBlockTool compensate deletes the calendar block."""
    async def _run():
        tool = CreateCalendarBlockTool()
        mock_db = AsyncMock()
        user_id = uuid.uuid4()
        event_id = uuid.uuid4()

        res = await tool.compensate(mock_db, user_id, snapshot={"created_event_id": str(event_id)})

        assert res["success"] is True
        assert res["restored_entity_id"] == str(event_id)
        mock_db.execute.assert_called()
        mock_db.commit.assert_called_once()

    asyncio.run(_run())


def test_create_habit_compensation():
    """Verify CreateHabitTool compensate deletes the habit created during execution."""
    async def _run():
        tool = CreateHabitTool()
        mock_db = AsyncMock()
        user_id = uuid.uuid4()
        habit_id = uuid.uuid4()

        res = await tool.compensate(mock_db, user_id, snapshot={"created_habit_id": str(habit_id)})

        assert res["success"] is True
        assert res["restored_entity_id"] == str(habit_id)
        mock_db.execute.assert_called()
        mock_db.commit.assert_called_once()

    asyncio.run(_run())


# ============================================================================
# 4. SELECTIVE APPROVAL & REVERSE ROLLBACK IN SHADOW SERVICE
# ============================================================================

def test_selective_approval_execution_logic():
    """Verify that approving specific step IDs marks unchecked steps as skipped."""
    async def _run():
        mock_db = AsyncMock()
        user_id = uuid.uuid4()
        plan_id = uuid.uuid4()

        step1_id = uuid.uuid4()
        step2_id = uuid.uuid4()

        step1 = TransactionStep(
            id=step1_id,
            plan_id=plan_id,
            step_order=1,
            tool_name="create_task",
            reversibility="REVERSIBLE",
            risk_level="LOW",
            params_json={"title": "Approved Step"},
            before_state_json={},
            after_state_json={"title": "Approved Step"},
            status="pending",
        )
        step2 = TransactionStep(
            id=step2_id,
            plan_id=plan_id,
            step_order=2,
            tool_name="create_habit",
            reversibility="REVERSIBLE",
            risk_level="LOW",
            params_json={"title": "Skipped Step"},
            before_state_json={},
            after_state_json={"title": "Skipped Step"},
            status="pending",
        )

        plan = TransactionPlan(
            id=plan_id,
            user_id=user_id,
            intent_summary="Multi-step test",
            status="AWAITING_APPROVAL",
            plan_metadata={},
            created_at=datetime.now(timezone.utc),
            steps=[step1, step2],
        )

        mock_res = MagicMock()
        mock_res.scalar_one_or_none.return_value = plan
        mock_db.execute.return_value = mock_res

        # Mock tool execution for step 1
        with patch("app.services.shadow_execution_service.get_tool") as mock_get_tool:
            mock_tool = AsyncMock()
            mock_tool.execute.return_value = {"created_task_id": "task-abc-123"}
            mock_get_tool.return_value = mock_tool

            res = await ShadowExecutionService.approve_plan(
                db=mock_db,
                user_id=user_id,
                plan_id=plan_id,
                approved_step_ids=[str(step1_id)],  # Only approve Step 1
            )

        assert res["success"] is True
        assert step1.status == "verified"
        assert step1.approved is True
        assert step2.status == "skipped"
        assert step2.approved is False
        assert plan.status == "VERIFIED"

    asyncio.run(_run())


def test_reverse_order_rollback_execution():
    """Verify rollback compensates verified steps in reverse order (descending step_order)."""
    async def _run():
        mock_db = AsyncMock()
        user_id = uuid.uuid4()
        plan_id = uuid.uuid4()

        execution_order = []

        step1_id = uuid.uuid4()
        step2_id = uuid.uuid4()

        step1 = TransactionStep(
            id=step1_id,
            plan_id=plan_id,
            step_order=1,
            tool_name="create_task",
            reversibility="REVERSIBLE",
            risk_level="LOW",
            params_json={"title": "First Step"},
            before_state_json={},
            after_state_json={"created_task_id": "1"},
            status="verified",
            verification_result_json={"details": {"created_task_id": "1"}},
        )
        step2 = TransactionStep(
            id=step2_id,
            plan_id=plan_id,
            step_order=2,
            tool_name="create_habit",
            reversibility="REVERSIBLE",
            risk_level="LOW",
            params_json={"title": "Second Step"},
            before_state_json={},
            after_state_json={"created_habit_id": "2"},
            status="verified",
            verification_result_json={"details": {"created_habit_id": "2"}},
        )

        plan = TransactionPlan(
            id=plan_id,
            user_id=user_id,
            intent_summary="Rollback test",
            status="VERIFIED",
            plan_metadata={},
            created_at=datetime.now(timezone.utc),
            steps=[step1, step2],
        )

        mock_res = MagicMock()
        mock_res.scalar_one_or_none.return_value = plan
        mock_db.execute.return_value = mock_res

        def make_mock_tool(tool_name):
            tool = AsyncMock()
            async def fake_compensate(db, uid, snapshot):
                execution_order.append(tool_name)
                return {"success": True, "details": {"compensated": tool_name}}
            tool.compensate = fake_compensate
            return tool

        with patch("app.services.shadow_execution_service.get_tool") as mock_get_tool:
            mock_get_tool.side_effect = make_mock_tool

            res = await ShadowExecutionService.rollback_plan(
                db=mock_db,
                user_id=user_id,
                plan_id=plan_id,
            )

        assert res["success"] is True
        assert plan.status == "ROLLED_BACK"
        assert step1.status == "rolled_back"
        assert step2.status == "rolled_back"
        # Verification of REVERSE order: step 2 executed first, then step 1
        assert execution_order == ["create_habit", "create_task"]

    asyncio.run(_run())


# ============================================================================
# 5. SECURITY & CROSS-USER AUTHORIZATION
# ============================================================================

def test_cross_user_isolation_security():
    """Verify User A cannot inspect, approve, or rollback User B's transaction plan."""
    async def _run():
        mock_db = AsyncMock()
        user_a = uuid.uuid4()
        plan_b_id = uuid.uuid4()

        # Query filtered by user_id returns None for unauthorized user
        mock_res = MagicMock()
        mock_res.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_res

        # User A tries to inspect User B's plan
        details = await ShadowExecutionService.get_plan_details(mock_db, user_a, plan_b_id)
        assert details == {}

        # User A tries to approve User B's plan
        approve_res = await ShadowExecutionService.approve_plan(mock_db, user_a, plan_b_id)
        assert approve_res["success"] is False
        assert "unauthorized" in approve_res["error"]

        # User A tries to rollback User B's plan
        rollback_res = await ShadowExecutionService.rollback_plan(mock_db, user_a, plan_b_id)
        assert rollback_res["success"] is False
        assert "unauthorized" in rollback_res["error"]

    asyncio.run(_run())


# ============================================================================
# 6. IDEMPOTENCY PROTECTION
# ============================================================================

def test_idempotency_protection():
    """Verify already VERIFIED or ROLLED_BACK plans cannot be re-executed or re-compensated."""
    async def _run():
        mock_db = AsyncMock()
        user_id = uuid.uuid4()
        plan_id = uuid.uuid4()

        plan = TransactionPlan(
            id=plan_id,
            user_id=user_id,
            intent_summary="Idempotency test",
            status="VERIFIED",
            plan_metadata={},
            created_at=datetime.now(timezone.utc),
            steps=[],
        )

        mock_res = MagicMock()
        mock_res.scalar_one_or_none.return_value = plan
        mock_db.execute.return_value = mock_res

        # Cannot re-approve VERIFIED plan
        approve_res = await ShadowExecutionService.approve_plan(mock_db, user_id, plan_id)
        assert approve_res["success"] is False
        assert "already in finalized state" in approve_res["error"]

        # Rollback once
        plan.status = "ROLLED_BACK"
        # Cannot re-rollback ROLLED_BACK plan
        rollback_res = await ShadowExecutionService.rollback_plan(mock_db, user_id, plan_id)
        assert rollback_res["success"] is False
        assert "already been rolled back" in rollback_res["error"]

    asyncio.run(_run())


# ============================================================================
# 7. API ENDPOINT REGISTRATION
# ============================================================================

def test_shadow_execution_endpoints_mounted():
    """Verify all 6 shadow execution and rollback endpoints are registered on API router."""
    routes = [r.path for r in api_router.routes]

    assert "/executions/plans" in routes
    assert "/executions/simulate" in routes
    assert "/executions/plans/{plan_id}" in routes
    assert "/executions/plans/{plan_id}/approve" in routes
    assert "/executions/plans/{plan_id}/reject" in routes
    assert "/executions/plans/{plan_id}/rollback" in routes
