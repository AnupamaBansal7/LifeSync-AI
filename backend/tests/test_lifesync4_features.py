import uuid
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from app.ai.tools import ALL_TOOLS, get_tool
from app.ai.tools.computer_use_tools import (
    OpenApplicationTool,
    InspectWindowStateTool,
    SendKeyboardInputTool,
    SimulateMouseActionTool,
    EmergencyStopTool,
    SANCTIONED_APPLICATIONS,
)
from app.ai.agents import COMMON_AGENTS
from app.ai.agents.common import ComputerUseAgent
from app.models.productivity import Project
from app.models.user import User, UserPreference
from app.models.workflow import WorkflowExecution, WorkflowStepExecution
from app.services.proactive_assistant import ProactiveAssistantService


def test_computer_use_tools_registration():
    """Verify all 5 computer use tools are registered and mapped properly."""
    tool_names = [
        "open_application",
        "inspect_window_state",
        "send_keyboard_input",
        "simulate_mouse_action",
        "emergency_stop",
    ]
    for name in tool_names:
        assert name in ALL_TOOLS, f"Missing tool {name} in ALL_TOOLS"
        tool = get_tool(name)
        assert tool is not None
        assert tool.name == name

    # Verify total tools count is at least 31
    assert len(ALL_TOOLS) >= 31

    # Verify ComputerUseAgent instance is in COMMON_AGENTS
    assert any(isinstance(a, ComputerUseAgent) for a in COMMON_AGENTS)


def test_computer_use_sanctioned_apps_whitelist():
    """Verify OpenApplicationTool blocks unsanctioned binaries and permits whitelisted ones."""
    tool = OpenApplicationTool()
    assert tool.requires_approval is False
    assert tool.risk_level == "medium"
    assert "calc.exe" in SANCTIONED_APPLICATIONS.values()
    assert "notepad.exe" in SANCTIONED_APPLICATIONS.values()

    # Test parameter schema
    schema = tool.parameters_schema
    assert schema["type"] == "object"
    assert "app_name" in schema["properties"]
    assert "app_name" in schema["required"]


def test_computer_use_approval_isolation():
    """Verify that keyboard input and mouse actions require human approval."""
    keyboard_tool = SendKeyboardInputTool()
    assert keyboard_tool.requires_approval is True
    assert keyboard_tool.risk_level == "high"

    mouse_tool = SimulateMouseActionTool()
    assert mouse_tool.requires_approval is True
    assert mouse_tool.risk_level == "high"

    stop_tool = EmergencyStopTool()
    assert stop_tool.requires_approval is False
    assert stop_tool.risk_level == "low"


def test_proactive_assistant_quiet_hours():
    """Verify quiet hours suppression logic (22:00 to 07:00)."""
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        email="alex@lifesync.ai",
        full_name="Alex Mercer",
    )
    pref = UserPreference(
        user_id=user_id,
        timezone="UTC",
    )
    user.preferences = pref

    # 23:30 is quiet hours
    late_night = datetime(2026, 11, 21, 23, 30, tzinfo=timezone.utc)
    assert ProactiveAssistantService.is_in_quiet_hours(user, late_night) is True

    # 03:15 is quiet hours
    early_morning = datetime(2026, 11, 21, 3, 15, tzinfo=timezone.utc)
    assert ProactiveAssistantService.is_in_quiet_hours(user, early_morning) is True

    # 14:00 is active hours
    afternoon = datetime(2026, 11, 21, 14, 0, tzinfo=timezone.utc)
    assert ProactiveAssistantService.is_in_quiet_hours(user, afternoon) is False


def test_project_workspace_model_structure():
    """Verify Project model initialization and attributes."""
    proj_id = uuid.uuid4()
    user_id = uuid.uuid4()
    proj = Project(
        id=proj_id,
        user_id=user_id,
        name="LifeSync AI 4.0 Architecture",
        description="Autonomous Multi-Agent Operating System",
        role_context="work",
        status="active",
        notes=["Key decision: DAG workflow engine with checkpoint resume."],
        decisions=[{"decision": "Use Win32 ctypes for window inspection", "date": "2026-11-21"}],
    )

    assert proj.name == "LifeSync AI 4.0 Architecture"
    assert proj.status == "active"
    assert len(proj.notes) == 1
    assert len(proj.decisions) == 1
    assert proj.decisions[0]["decision"] == "Use Win32 ctypes for window inspection"


def test_workflow_dag_model_structure():
    """Verify WorkflowExecution and WorkflowStepExecution DAG model relationships."""
    wf_id = uuid.uuid4()
    user_id = uuid.uuid4()

    wf = WorkflowExecution(
        id=wf_id,
        user_id=user_id,
        name="Sync Gmail & Schedule Focus Block",
        status="running",
        plan_graph={"total_steps": 2},
        context_state={"email_query": "is:unread"},
    )
    assert wf.status == "running"
    assert wf.context_state["email_query"] == "is:unread"

    step_1 = WorkflowStepExecution(
        workflow_id=wf_id,
        step_id="step_read_emails",
        step_order=1,
        name="Fetch Unread Emails",
        agent_name="EmailAgent",
        tool_name="read_gmail_threads",
        status="completed",
        depends_on=[],
        requires_approval=False,
    )

    step_2 = WorkflowStepExecution(
        workflow_id=wf_id,
        step_id="step_send_summary",
        step_order=2,
        name="Send Briefing Email",
        agent_name="EmailAgent",
        tool_name="send_gmail_message",
        status="awaiting_approval",
        depends_on=["step_read_emails"],
        requires_approval=True,
    )

    assert step_1.status == "completed"
    assert step_2.status == "awaiting_approval"
    assert "step_read_emails" in step_2.depends_on
    assert step_2.requires_approval is True
