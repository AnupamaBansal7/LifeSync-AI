import pytest
import uuid
from datetime import datetime, timezone

from app.ai.orchestrator import (
    _extract_target_date,
    _parse_task_items_from_text,
    _resolve_follow_up_entities,
    detect_intent,
)
from app.ai.tools import ALL_TOOLS, get_tool
from app.ai.tools.workspace_tools import (
    ArchiveEmailTool,
    CreateGoogleCalendarEventTool,
    CreateGoogleDocTool,
    CreateGoogleSheetTool,
    ReadEmailThreadTool,
    ReplyEmailTool,
    SearchDriveFilesTool,
    SearchEmailsTool,
    SyncGoogleTasksTool,
)
from app.models.ai_system import Message
from app.services.integrations_service import IntegrationsService


def test_intent_detection_lifesync3_matrix():
    # Compound multi-step orchestration
    assert detect_intent("Organize my day tomorrow, check my calendar, find unfinished tasks, schedule my study sessions and send an email to Rahul about our project meeting.") in ("compound_orchestration", "multi_agent_orchestration")

    # Follow-up actions
    assert detect_intent("Move that task to Friday") == "follow_up_reschedule"
    assert detect_intent("Reschedule that task to tomorrow") == "follow_up_reschedule"
    assert detect_intent("Send the same information to Rahul") == "follow_up_email"
    assert detect_intent("Email that to Sarah") == "follow_up_email"

    # Google Workspace tools
    assert detect_intent("Create a Google Doc for sprint notes") == "workspace_document"
    assert detect_intent("Create a Google Sheet for budget") == "workspace_sheet"
    assert detect_intent("Search drive for project architecture") == "workspace_drive"
    assert detect_intent("Sync Google Tasks with LifeSync") == "workspace_sync"


def test_follow_up_entity_resolution():
    history = [
        Message(
            conversation_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            sender="user",
            content="Create a task for DBMS project submission",
        ),
        Message(
            conversation_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            sender="assistant",
            content="• **DBMS Project Submission** [HIGH] — Due: Tomorrow\nHere is the plan for today.",
        ),
    ]

    # Test resolving "that task"
    res1 = _resolve_follow_up_entities("Move that task to Friday", history)
    assert res1.get("target_task_title") == "DBMS Project Submission"

    # Test resolving "the same information" & recipient
    res2 = _resolve_follow_up_entities("Send the same information to Rahul", history)
    assert "DBMS Project Submission" in res2.get("referenced_content", "")
    assert res2.get("recipient") == "rahul@example.com"
    assert res2.get("recipient_name") == "Rahul"


def test_google_workspace_tools_registration_and_schemas():
    tools = [
        ("search_emails", SearchEmailsTool, False, "low"),
        ("read_email_thread", ReadEmailThreadTool, False, "low"),
        ("reply_email", ReplyEmailTool, True, "high"),
        ("archive_email", ArchiveEmailTool, False, "low"),
        ("create_google_calendar_event", CreateGoogleCalendarEventTool, False, "low"),
        ("search_drive_files", SearchDriveFilesTool, False, "low"),
        ("create_google_doc", CreateGoogleDocTool, False, "low"),
        ("create_google_sheet", CreateGoogleSheetTool, False, "low"),
        ("sync_google_tasks", SyncGoogleTasksTool, False, "low"),
    ]

    for name, tool_cls, req_app, risk in tools:
        tool = get_tool(name)
        assert tool is not None, f"Tool {name} should be in registry"
        assert isinstance(tool, tool_cls)
        assert tool.requires_approval is req_app, f"Tool {name} requires_approval expected {req_app}"
        assert tool.risk_level == risk, f"Tool {name} risk expected {risk}"
        assert isinstance(tool.parameters_schema, dict)


def test_google_workspace_tools_isolation_and_parameters():
    search_emails = SearchEmailsTool()
    assert search_emails.name == "search_emails"
    assert search_emails.requires_approval is False
    assert search_emails.risk_level == "low"
    assert "query" in search_emails.parameters_schema["properties"]

    reply_email = ReplyEmailTool()
    assert reply_email.name == "reply_email"
    assert reply_email.requires_approval is True
    assert reply_email.risk_level == "high"
    assert "message_id" in reply_email.parameters_schema["required"]

    create_doc = CreateGoogleDocTool()
    assert create_doc.name == "create_google_doc"
    assert create_doc.requires_approval is False
    assert "title" in create_doc.parameters_schema["required"]

    create_sheet = CreateGoogleSheetTool()
    assert create_sheet.name == "create_google_sheet"
    assert "headers" in create_sheet.parameters_schema["required"]

    search_drive = SearchDriveFilesTool()
    assert search_drive.name == "search_drive_files"
    assert "query" in search_drive.parameters_schema["properties"]

    create_cal = CreateGoogleCalendarEventTool()
    assert create_cal.name == "create_google_calendar_event"
    assert "title" in create_cal.parameters_schema["required"]
    assert "start_time" in create_cal.parameters_schema["required"]





