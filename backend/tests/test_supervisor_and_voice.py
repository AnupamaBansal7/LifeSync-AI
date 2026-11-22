import asyncio
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.models.user import User
from app.models.productivity import Task
from app.models.calendar import CalendarEvent
from app.models.shadow_execution import TransactionPlan
from app.services.supervisor_agent import (
    SupervisorAgent,
    AgentContext,
    clean_spoken_text,
    parse_relative_datetime,
)
from app.services.shadow_execution_service import ShadowExecutionService
from app.api.v1.agents import get_proactive_greeting


# ============================================================================
# 1. TEXT CLEANING & RELATIVE DATETIME PARSING
# ============================================================================

def test_clean_spoken_text():
    """Verify clean_spoken_text strips markdown characters, bullets, and URLs."""
    raw = "### Sync Supervisor\n• Created **Assignment Report** [HIGH]\n- Scheduled `10:00 AM` [Link](https://lifesync.ai)"
    cleaned = clean_spoken_text(raw)
    assert "#" not in cleaned
    assert "*" not in cleaned
    assert "`" not in cleaned
    assert "•" not in cleaned
    assert "[" not in cleaned
    assert "]" not in cleaned
    assert "https://" not in cleaned
    assert "Assignment Report" in cleaned


def test_parse_relative_datetime():
    """Verify parse_relative_datetime accurately parses tomorrow and specific hours."""
    dt_tom = parse_relative_datetime("tomorrow at 10 AM")
    now = datetime.now(timezone.utc)
    expected_day = (now + timedelta(days=1)).day
    assert dt_tom.day == expected_day
    assert dt_tom.hour == 10
    assert dt_tom.minute == 0

    dt_pm = parse_relative_datetime("Friday at 3 PM")
    assert dt_pm.hour == 15
    assert dt_pm.minute == 0


# ============================================================================
# 2. VOICE APPROVAL ROUTING & LIFECYCLE
# ============================================================================

def test_voice_approval_flow_executes_plan():
    """Verify user verbal approval routes directly to ShadowExecutionService.approve_plan."""
    async def _test():
        mock_db = AsyncMock()
        user_id = uuid.uuid4()
        plan_id = uuid.uuid4()

        # Mock active plan
        mock_plan = MagicMock()
        mock_plan.id = plan_id
        mock_plan.intent_summary = "Create task and block calendar"
        mock_plan.status = "AWAITING_APPROVAL"
        mock_plan.to_dict.return_value = {"id": str(plan_id), "status": "VERIFIED"}

        mock_res = MagicMock()
        mock_res.scalar_one_or_none.return_value = mock_plan
        mock_db.execute = AsyncMock(return_value=mock_res)

        ctx = AgentContext(
            user_id=user_id,
            user_name="Anupama",
            conversation_history=[],
            active_role="student",
        )

        with patch.object(ShadowExecutionService, "approve_plan", new_callable=AsyncMock) as mock_approve:
            mock_approve.return_value = {
                "success": True,
                "plan_id": str(plan_id),
                "status": "VERIFIED",
                "executed_steps": 2,
            }

            res = await SupervisorAgent.coordinate(
                db=mock_db,
                context=ctx,
                user_message="Yes, approve it",
            )

            assert res["mode"] == "VOICE_APPROVAL"
            assert "Approved" in res["display_reply"] and "Executed" in res["display_reply"]
            assert res["spoken_reply"] is not None
            assert len(res["agent_trace"]) >= 1
            assert res["agent_trace"][0]["agent"] == "Sync Supervisor"
            mock_approve.assert_called_once_with(db=mock_db, user_id=user_id, plan_id=plan_id)

    asyncio.run(_test())


def test_voice_cancellation_flow():
    """Verify user verbal cancellation rejects the pending transaction plan."""
    async def _test():
        mock_db = AsyncMock()
        user_id = uuid.uuid4()
        plan_id = uuid.uuid4()

        mock_plan = MagicMock()
        mock_plan.id = plan_id
        mock_plan.intent_summary = "Create task and block calendar"
        mock_plan.status = "AWAITING_APPROVAL"
        mock_plan.to_dict.return_value = {"id": str(plan_id), "status": "CANCELLED"}

        mock_res = MagicMock()
        mock_res.scalar_one_or_none.return_value = mock_plan
        mock_db.execute = AsyncMock(return_value=mock_res)

        ctx = AgentContext(
            user_id=user_id,
            user_name="Anupama",
            conversation_history=[],
            active_role="student",
        )

        with patch.object(ShadowExecutionService, "rollback_plan", new_callable=AsyncMock) as mock_rollback:
            mock_rollback.return_value = {
                "success": True,
                "plan_id": str(plan_id),
                "status": "ROLLED_BACK",
            }

            res = await SupervisorAgent.coordinate(
                db=mock_db,
                context=ctx,
                user_message="Cancel it",
            )

            assert res["mode"] == "VOICE_APPROVAL"
            assert "Cancelled" in res["display_reply"]
            assert res["spoken_reply"] is not None
            mock_rollback.assert_called_once_with(db=mock_db, user_id=user_id, plan_id=plan_id)

    asyncio.run(_test())


# ============================================================================
# 3. SUPERVISOR COMPOUND MULTI-AGENT EXECUTION WITH SHARED CONTEXT
# ============================================================================

def test_supervisor_compound_task_and_calendar():
    """Verify compound command routes to Task and Calendar agents with shared context."""
    async def _test():
        mock_db = AsyncMock()
        user_id = uuid.uuid4()

        ctx = AgentContext(
            user_id=user_id,
            user_name="Anupama",
            conversation_history=[],
            active_role="student",
        )

        mock_simulated_plan = {
            "id": str(uuid.uuid4()),
            "status": "SIMULATED",
            "overall_risk": "LOW",
            "intent_summary": "Finish my assignment and block 1 hour tomorrow at 10 AM",
            "steps": [
                {
                    "tool_name": "create_task",
                    "params": {"title": "Finish my assignment", "due_date": "2026-11-27T17:00:00Z"},
                    "reversibility": "REVERSIBLE",
                },
                {
                    "tool_name": "create_calendar_block",
                    "params": {"title": "Focus: Finish my assignment", "start_time": "2026-11-24T10:00:00Z"},
                    "reversibility": "REVERSIBLE",
                },
            ],
        }

        with patch.object(ShadowExecutionService, "simulate_plan", new_callable=AsyncMock) as mock_sim:
            mock_sim.return_value = mock_simulated_plan

            msg = "I need to finish my assignment by Friday and block 1 hour tomorrow at 10 AM"
            res = await SupervisorAgent.coordinate(
                db=mock_db,
                context=ctx,
                user_message=msg,
            )

            assert res["mode"] == "MULTI_AGENT_PLAN"
            assert "transaction_plan" in res
            assert len(res["transaction_plan"]["steps"]) == 2

            # Verify multi-agent trace contains Supervisor, Task Agent, and Calendar Agent
            agents_in_trace = [item["agent"] for item in res["agent_trace"]]
            assert "Sync Supervisor" in agents_in_trace
            assert "Task Agent" in agents_in_trace
            assert "Calendar Agent" in agents_in_trace

            # Verify spoken_reply is clean, natural speech without markdown
            assert res["spoken_reply"] is not None
            assert "*" not in res["spoken_reply"]
            assert "#" not in res["spoken_reply"]

            # Verify shared_outputs captured task agent's output
            assert "task_agent" in ctx.shared_outputs
            assert "assignment" in ctx.shared_outputs["task_agent"]["title"].lower()

    asyncio.run(_test())


# ============================================================================
# 4. PROACTIVE GREETING ENDPOINT & USER ISOLATION
# ============================================================================

def test_proactive_greeting_endpoint():
    """Verify GET /api/v1/agents/greeting personalized text and quick suggestions."""
    async def _test():
        mock_db = AsyncMock()
        user_a = User(
            id=uuid.uuid4(),
            email="anupama@example.com",
            full_name="Anupama Sharma",
            hashed_password="pw",
            is_active=True,
        )

        # 1. User has 3 pending tasks
        mock_tasks_res = MagicMock()
        mock_tasks_res.scalar.return_value = 3
        mock_event_res = MagicMock()
        mock_event_res.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(side_effect=[mock_tasks_res, mock_event_res])

        res = await get_proactive_greeting(current_user=user_a, db=mock_db)

        assert res.user_name == "Anupama"
        assert res.pending_tasks_count == 3
        assert "Hello Anupama!" in res.greeting_text
        assert "3 tasks due today" in res.greeting_text
        assert len(res.quick_suggestions) == 3
        assert "Plan my day" in res.quick_suggestions

        # 2. User has next upcoming event
        next_event = CalendarEvent(
            id=uuid.uuid4(),
            user_id=user_a.id,
            title="Sprint Architecture Review",
            start_time=datetime(2026, 11, 23, 14, 0, 0, tzinfo=timezone.utc),
            end_time=datetime(2026, 11, 23, 15, 0, 0, tzinfo=timezone.utc),
            event_type="meeting",
        )
        mock_tasks_res2 = MagicMock()
        mock_tasks_res2.scalar.return_value = 1
        mock_event_res2 = MagicMock()
        mock_event_res2.scalar_one_or_none.return_value = next_event
        mock_db.execute = AsyncMock(side_effect=[mock_tasks_res2, mock_event_res2])

        res_event = await get_proactive_greeting(current_user=user_a, db=mock_db)
        assert "Sprint Architecture Review" in res_event.greeting_text
        assert "1 tasks due today" in res_event.greeting_text

    asyncio.run(_test())
