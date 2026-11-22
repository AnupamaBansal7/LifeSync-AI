import asyncio
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.ai.tools.goal_tools import CreateGoalTool
from app.ai.tools.base import Reversibility
from app.models.intake import IntakeSession
from app.models.productivity import Goal
from app.services.agentic_intake_service import AgenticIntakeService
from app.services.shadow_execution_service import ShadowExecutionService


# ============================================================================
# 1. CREATE GOAL TOOL REVERSIBILITY & COMPENSATION
# ============================================================================

def test_create_goal_tool_contract():
    """Verify CreateGoalTool reversibility and dry-run contract."""
    tool = CreateGoalTool()
    assert tool.is_mutating is True
    assert tool.reversibility == Reversibility.REVERSIBLE

    async def _test():
        mock_db = AsyncMock()
        user_id = uuid.uuid4()
        params = {
            "title": "Master Distributed Systems",
            "horizon": "yearly",
            "role_context": "professional",
            "target_date": "2027-01-01",
        }

        diff = await tool.dry_run(mock_db, user_id, params)
        assert diff["target_entity"] == "Goal"
        assert "Master Distributed Systems" in diff["action_summary"]
        assert diff["before_state"] == {}
        assert diff["after_state"]["title"] == "Master Distributed Systems"
        assert diff["risk_level"] == "LOW"

        # Test compensate
        snapshot = {
            "before_state": {},
            "after_state": {
                "goal_id": str(uuid.uuid4()),
                "title": "Master Distributed Systems",
            },
        }

        comp_res = await tool.compensate(mock_db, user_id, snapshot)
        assert comp_res["success"] is True
        assert comp_res["restored_entity_id"] == snapshot["after_state"]["goal_id"]

    asyncio.run(_test())


# ============================================================================
# 2. START INTAKE SESSION (NO MUTATIONS)
# ============================================================================

def test_high_level_goal_starts_intake_session_no_mutations():
    """Starting an intake session generates clarification card with 0 DB mutations."""
    async def _test():
        mock_db = AsyncMock()
        user_id = uuid.uuid4()
        prompt = "I want to launch a SaaS project this semester"

        # Mock query results
        mock_res = MagicMock()
        mock_res.scalar_one_or_none.return_value = None
        mock_res.scalar.return_value = 3
        mock_db.execute.return_value = mock_res

        res = await AgenticIntakeService.start_or_continue_intake(
            db=mock_db,
            user_id=user_id,
            prompt=prompt,
        )

        assert res["status"] == "CLARIFICATION_REQUIRED"
        assert "clarification_card" in res
        card = res["clarification_card"]
        assert card["step"] == 1
        assert card["estimated_total_steps"] == 4
        assert len(card["options"]) > 0
        assert card["can_skip_and_generate"] is True
        assert card["session_id"] is not None

        # Verify DB session was added, but no tasks or goals were created
        assert mock_db.add.called
        added_entities = [args[0] for args, _ in mock_db.add.call_args_list]
        for ent in added_entities:
            assert not isinstance(ent, Goal)
            assert type(ent).__name__ != "Task"

    asyncio.run(_test())


# ============================================================================
# 3. RESPOND ADVANCES STEP AND SAVES CONTEXT
# ============================================================================

def test_respond_advances_step_and_saves_context():
    """Responding to an intake step saves answers in JSON and moves to step 2."""
    async def _test():
        mock_db = AsyncMock()
        user_id = uuid.uuid4()
        session_id = uuid.uuid4()

        session = IntakeSession(
            id=session_id,
            user_id=user_id,
            initial_prompt="I want to learn rust",
            domain="GOAL_PLANNING",
            status="GATHERING_INFO",
            collected_context_json={},
            current_step=1,
            max_steps=4,
        )

        res_mock = MagicMock()
        res_mock.scalar_one_or_none.return_value = session
        res_mock.scalar.return_value = 2
        mock_db.execute.return_value = res_mock

        res = await AgenticIntakeService.respond_to_intake(
            db=mock_db,
            user_id=user_id,
            session_id=session_id,
            selected_options=["3 months (Quarterly Sprint)"],
            custom_text="",
            skip_and_generate=False,
        )

        assert res["status"] == "CLARIFICATION_REQUIRED"
        assert session.current_step == 2
        assert "step_1" in session.collected_context_json
        assert session.collected_context_json["step_1"]["selected_options"] == ["3 months (Quarterly Sprint)"]

    asyncio.run(_test())


# ============================================================================
# 4. SKIP AND GENERATE CREATES SHADOW PLAN
# ============================================================================

def test_skip_and_generate_creates_shadow_transaction_plan():
    """Skip & Generate immediately compiles a blueprint and returns SIMULATED plan with 0 DB mutations."""
    async def _test():
        mock_db = AsyncMock()
        user_id = uuid.uuid4()
        session_id = uuid.uuid4()

        session = IntakeSession(
            id=session_id,
            user_id=user_id,
            initial_prompt="Prepare for machine learning placements",
            domain="GOAL_PLANNING",
            status="GATHERING_INFO",
            collected_context_json={"step_1": {"selected_options": ["1 month"]}},
            current_step=2,
            max_steps=4,
        )

        res_mock = MagicMock()
        res_mock.scalar_one_or_none.return_value = session
        mock_db.execute.return_value = res_mock

        # Mock ShadowExecutionService.simulate_plan
        fake_plan_id = uuid.uuid4()
        fake_plan_dict = {
            "id": str(fake_plan_id),
            "status": "SIMULATED",
            "total_steps": 6,
            "can_auto_approve": False,
            "steps": [],
        }

        with patch.object(
            ShadowExecutionService,
            "simulate_plan",
            new_callable=AsyncMock
        ) as mock_sim:
            mock_sim.return_value = fake_plan_dict

            res = await AgenticIntakeService.respond_to_intake(
                db=mock_db,
                user_id=user_id,
                session_id=session_id,
                selected_options=[],
                custom_text=None,
                skip_and_generate=True,
            )

            assert res["status"] == "COMPLETED"
            assert "transaction_plan" in res
            assert res["transaction_plan"]["status"] == "SIMULATED"
            assert session.status == "COMPLETED"
            assert session.resulting_plan_id == fake_plan_id

    asyncio.run(_test())


# ============================================================================
# 5. CROSS-USER ISOLATION
# ============================================================================

def test_cross_user_isolation():
    """User B cannot access or respond to User A's intake session."""
    async def _test():
        mock_db = AsyncMock()
        user_b = uuid.uuid4()
        session_id = uuid.uuid4()

        # Database query filtered by user_id returns None for unauthorized user
        res_mock = MagicMock()
        res_mock.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = res_mock

        with pytest.raises(ValueError) as excinfo:
            await AgenticIntakeService.respond_to_intake(
                db=mock_db,
                user_id=user_b,
                session_id=session_id,
                selected_options=["Option A"],
            )

        assert "not found or access denied" in str(excinfo.value).lower()

    asyncio.run(_test())
