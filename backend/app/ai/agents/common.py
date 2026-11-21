from typing import List
from app.ai.agents.base import BaseAgent


class PersonalAssistantAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "personal_assistant"

    @property
    def display_name(self) -> str:
        return "Personal Assistant Agent"

    @property
    def description(self) -> str:
        return "Central AI companion that understands natural language queries, coordinates specialized agents, and executes cross-cutting tasks."

    @property
    def allowed_tools(self) -> List[str]:
        return [
            "search_memory",
            "create_task",
            "batch_create_tasks",
            "list_tasks",
            "create_calendar_block",
            "compose_email_draft",
            "send_email",
            "log_habit",
        ]


class TaskManagementAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "task_management"

    @property
    def display_name(self) -> str:
        return "Task Management Agent"

    @property
    def description(self) -> str:
        return "Creates single and multiple tasks, marks completion, updates priorities, lists pending/overdue items, and deletes tasks."

    @property
    def allowed_tools(self) -> List[str]:
        return [
            "create_task",
            "batch_create_tasks",
            "update_task_status",
            "delete_task",
            "list_tasks",
        ]


class EmailAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "email_agent"

    @property
    def display_name(self) -> str:
        return "Email & Messaging Agent"

    @property
    def description(self) -> str:
        return "Searches inbox, summarizes threads, composes, drafts, replies, and sends emails through connected Gmail accounts with human approval for outgoing messages."

    @property
    def allowed_tools(self) -> List[str]:
        return [
            "search_emails",
            "read_email_thread",
            "compose_email_draft",
            "reply_email",
            "send_email",
            "archive_email",
        ]


class WorkspaceAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "workspace_agent"

    @property
    def display_name(self) -> str:
        return "Google Workspace Agent"

    @property
    def description(self) -> str:
        return "Orchestrates Google Workspace operations across Drive files, Google Docs, Sheets, and Google Tasks synchronization."

    @property
    def allowed_tools(self) -> List[str]:
        return [
            "search_drive_files",
            "create_google_doc",
            "create_google_sheet",
            "sync_google_tasks",
            "create_google_calendar_event",
            "search_emails",
        ]


class DocumentAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "document_agent"

    @property
    def display_name(self) -> str:
        return "Document & Report Agent"

    @property
    def description(self) -> str:
        return "Drafts structured documents, technical summaries, reports, and creates live Google Docs."

    @property
    def allowed_tools(self) -> List[str]:
        return ["create_google_doc", "search_drive_files", "store_long_term_memory"]


class AutomationAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "automation_agent"

    @property
    def display_name(self) -> str:
        return "Automation & Workflow Agent"

    @property
    def description(self) -> str:
        return "Designs, schedules, and triggers persistent automated routines, briefings, and alert workflows."

    @property
    def allowed_tools(self) -> List[str]:
        return ["save_daily_plan", "list_tasks", "list_calendar_events", "store_long_term_memory"]


class PlanningAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "planning_agent"

    @property
    def display_name(self) -> str:
        return "Daily & Weekly Planning Agent"

    @property
    def description(self) -> str:
        return "Generates realistic daily, weekly, and monthly time-blocked execution plans balancing commitments and priority deadlines."

    @property
    def allowed_tools(self) -> List[str]:
        return [
            "save_daily_plan",
            "create_calendar_block",
            "list_tasks",
            "batch_create_tasks",
            "list_calendar_events",
        ]


class GoalManagementAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "goal_management"

    @property
    def display_name(self) -> str:
        return "Goal & Milestone Agent"

    @property
    def description(self) -> str:
        return "Converts broad personal and professional aspirations into actionable milestones, monitors momentum, and identifies stalled goals."

    @property
    def allowed_tools(self) -> List[str]:
        return ["create_goal", "list_goals", "create_task"]


class HabitAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "habit_agent"

    @property
    def display_name(self) -> str:
        return "Habit & Consistency Agent"

    @property
    def description(self) -> str:
        return "Establishes recurring daily/weekly habits, tracks streaks without negative punishment, and nudges consistency."

    @property
    def allowed_tools(self) -> List[str]:
        return ["create_habit", "log_habit", "list_habits"]


class CalendarAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "calendar_agent"

    @property
    def display_name(self) -> str:
        return "Calendar & Scheduling Agent"

    @property
    def description(self) -> str:
        return "Organizes schedules, detects meeting collisions, protects locked events, and suggests alternative focus slots."

    @property
    def allowed_tools(self) -> List[str]:
        return [
            "create_calendar_block",
            "create_google_calendar_event",
            "list_calendar_events",
            "delete_calendar_event",
            "save_daily_plan",
        ]


class MemoryAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "memory_agent"

    @property
    def display_name(self) -> str:
        return "Memory & Knowledge Curator"

    @property
    def description(self) -> str:
        return "Extracts personal preferences, decisions, and recurring patterns from conversations into persistent semantic memory."

    @property
    def allowed_tools(self) -> List[str]:
        return ["store_long_term_memory", "search_memory", "delete_memory"]


class ResearchAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "research_agent"

    @property
    def display_name(self) -> str:
        return "Research & Synthesis Agent"

    @property
    def description(self) -> str:
        return "Analyzes complex topics, synthesizes findings, and saves actionable insights into the user's personal knowledge base."

    @property
    def allowed_tools(self) -> List[str]:
        return ["web_research", "store_long_term_memory", "create_task"]


class ReviewReflectionAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "review_reflection"

    @property
    def display_name(self) -> str:
        return "Review & Reflection Agent"

    @property
    def description(self) -> str:
        return "Generates daily debriefs, weekly progress summaries, detects burnout indicators, and highlights productivity patterns."

    @property
    def allowed_tools(self) -> List[str]:
        return ["generate_review_report", "save_daily_plan"]


class ScreenAssistanceAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "screen_assistant"

    @property
    def display_name(self) -> str:
        return "Screen Assistance Agent"

    @property
    def description(self) -> str:
        return "Inspects shared screen frames, reads visible UI elements, identifies workflows, forms, and error dialogs, and provides contextual execution guidance."

    @property
    def allowed_tools(self) -> List[str]:
        return ["analyze_screen_frame", "create_task", "search_memory"]


class ComputerUseAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "computer_use"

    @property
    def display_name(self) -> str:
        return "Computer Use Agent"

    @property
    def description(self) -> str:
        return "Executes sanctioned OS-level application interactions, navigates desktop windows, types input, and performs guided computer tasks with approval gates."

    @property
    def allowed_tools(self) -> List[str]:
        return [
            "open_application",
            "inspect_window_state",
            "send_keyboard_input",
            "simulate_mouse_action",
            "emergency_stop",
            "analyze_screen_frame",
        ]


