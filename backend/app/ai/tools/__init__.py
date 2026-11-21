from typing import Dict, List
from app.ai.tools.base import BaseTool
from app.ai.tools.calendar_tools import (
    CreateCalendarBlockTool,
    DeleteCalendarEventTool,
    ListCalendarEventsTool,
    SaveDailyPlanTool,
)
from app.ai.tools.email_tools import ComposeEmailDraftTool, SendEmailTool
from app.ai.tools.computer_use_tools import (
    EmergencyStopTool,
    InspectWindowStateTool,
    OpenApplicationTool,
    SendKeyboardInputTool,
    SimulateMouseActionTool,
)
from app.ai.tools.goal_tools import CreateGoalTool, ListGoalsTool

from app.ai.tools.habit_tools import CreateHabitTool, ListHabitsTool, LogHabitTool
from app.ai.tools.memory_tools import (
    DeleteMemoryTool,
    SearchMemoryTool,
    StoreLongTermMemoryTool,
)
from app.ai.tools.research_review_tools import (
    GenerateReviewReportTool,
    WebResearchTool,
)
from app.ai.tools.screen_tools import AnalyzeScreenFrameTool
from app.ai.tools.task_tools import (
    BatchCreateTasksTool,
    CreateTaskTool,
    DeleteTaskTool,
    ListTasksTool,
    UpdateTaskStatusTool,
)
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

ALL_TOOLS: Dict[str, BaseTool] = {
    # Tasks
    "create_task": CreateTaskTool(),
    "batch_create_tasks": BatchCreateTasksTool(),
    "update_task_status": UpdateTaskStatusTool(),
    "delete_task": DeleteTaskTool(),
    "list_tasks": ListTasksTool(),
    # Calendar
    "create_calendar_block": CreateCalendarBlockTool(),
    "list_calendar_events": ListCalendarEventsTool(),
    "delete_calendar_event": DeleteCalendarEventTool(),
    "save_daily_plan": SaveDailyPlanTool(),
    "create_google_calendar_event": CreateGoogleCalendarEventTool(),
    # Goals
    "create_goal": CreateGoalTool(),
    "list_goals": ListGoalsTool(),
    # Habits
    "create_habit": CreateHabitTool(),
    "log_habit": LogHabitTool(),
    "list_habits": ListHabitsTool(),
    # Memory
    "store_long_term_memory": StoreLongTermMemoryTool(),
    "search_memory": SearchMemoryTool(),
    "delete_memory": DeleteMemoryTool(),
    # Email (Gmail)
    "compose_email_draft": ComposeEmailDraftTool(),
    "send_email": SendEmailTool(),
    "search_emails": SearchEmailsTool(),
    "read_email_thread": ReadEmailThreadTool(),
    "reply_email": ReplyEmailTool(),
    "archive_email": ArchiveEmailTool(),
    # Google Workspace (Docs, Sheets, Drive, Tasks)
    "search_drive_files": SearchDriveFilesTool(),
    "create_google_doc": CreateGoogleDocTool(),
    "create_google_sheet": CreateGoogleSheetTool(),
    "sync_google_tasks": SyncGoogleTasksTool(),
    # Research & Review
    "web_research": WebResearchTool(),
    "generate_review_report": GenerateReviewReportTool(),
    # Screen Understanding
    "analyze_screen_frame": AnalyzeScreenFrameTool(),
    # Computer Use Agent Tools
    "open_application": OpenApplicationTool(),
    "inspect_window_state": InspectWindowStateTool(),
    "send_keyboard_input": SendKeyboardInputTool(),
    "simulate_mouse_action": SimulateMouseActionTool(),
    "emergency_stop": EmergencyStopTool(),
}



def get_tool(name: str) -> BaseTool | None:
    return ALL_TOOLS.get(name)


def get_openai_tool_definitions() -> List[dict]:
    """Convert registered tools to OpenAI / Ollama compatible function calling schemas."""
    tools = []
    for tool_name, tool_obj in ALL_TOOLS.items():
        tools.append({
            "type": "function",
            "function": {
                "name": tool_name,
                "description": tool_obj.description,
                "parameters": tool_obj.parameters_schema,
            },
        })
    return tools
