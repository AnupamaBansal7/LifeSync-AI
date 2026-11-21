import pytest
import uuid
from app.ai.orchestrator import _parse_task_items_from_text, detect_intent
from app.ai.tools import get_tool
from app.ai.tools.email_tools import ComposeEmailDraftTool, SendEmailTool
from app.ai.tools.task_tools import BatchCreateTasksTool, CreateTaskTool
from app.ai.tools.screen_tools import AnalyzeScreenFrameTool


def test_task_parsing():
    q = "Create a to-do list for tomorrow. Include completing my project documentation, studying DBMS and revising DSA."
    items = _parse_task_items_from_text(q)
    assert len(items) == 3
    assert "Completing my project documentation" in items
    assert "Studying DBMS" in items
    assert "Revising DSA" in items


def test_intent_detection_matrix():
    assert detect_intent("I completed my DBMS assignment. Mark it as completed.") == "task_completion"
    assert detect_intent("Send an email to my friend about tomorrow's meeting") == "email_agent"
    assert detect_intent("Draft an email to my professor requesting an extension") == "email_agent"
    assert detect_intent("Schedule two hours for DSA tomorrow") == "calendar_scheduling"
    assert detect_intent("I have my final-year project submission next Friday. Help me organize everything.") == "multi_agent_orchestration"
    assert detect_intent("Summarize my unfinished tasks and prepare tomorrow's schedule") == "task_listing"
    assert detect_intent("Delete task: Old assignment") == "task_deletion"
    assert detect_intent("Log habit: Morning Meditation") == "habit_logging"


def test_email_agent_approval_isolation():
    send_tool = SendEmailTool()
    draft_tool = ComposeEmailDraftTool()

    # Outbound email transmission MUST be high-risk and require human approval
    assert send_tool.requires_approval is True
    assert send_tool.risk_level == "high"

    # Drafting an email is safe and does not require pre-approval
    assert draft_tool.requires_approval is False
    assert draft_tool.risk_level == "low"


def test_screen_assistance_tool():
    screen_tool = AnalyzeScreenFrameTool()
    assert screen_tool.name == "analyze_screen_frame"
    assert screen_tool.requires_approval is False

    schema = screen_tool.parameters_schema
    assert "image_data" in schema["properties"]
    assert "query" in schema["properties"]


def test_batch_create_tasks_tool_properties():
    tool = BatchCreateTasksTool()
    assert tool.name == "batch_create_tasks"
    assert tool.requires_approval is False
    assert tool.risk_level == "low"

    schema = tool.parameters_schema
    assert "tasks" in schema["properties"]
    assert schema["properties"]["tasks"]["type"] == "array"
