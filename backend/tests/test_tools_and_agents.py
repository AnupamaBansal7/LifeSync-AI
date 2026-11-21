import pytest
from app.ai.agents import COMMON_AGENTS, ROLE_SPECIFIC_AGENTS, get_agent_by_name, list_agents_for_roles
from app.ai.orchestrator import detect_intent
from app.ai.providers import ProviderRegistry
from app.ai.tools import ALL_TOOLS, get_tool


def test_intent_detection():
    assert detect_intent("plan my day and schedule focus blocks") == "daily_planning"
    assert detect_intent("break down the capstone project into tasks") == "task_decomposition"
    assert detect_intent("remember that I prefer morning workouts") == "memory_management"
    assert detect_intent("review my productivity this week") == "reflection_coaching"
    assert detect_intent("set a goal to launch the startup") == "goal_management"
    assert detect_intent("track habit: read 20 pages every night") == "habit_management"


def test_agent_catalog():
    assert len(COMMON_AGENTS) >= 9
    assert len(ROLE_SPECIFIC_AGENTS) >= 8

    # Verify agent lookups
    planner = get_agent_by_name("planning_agent")
    assert planner is not None
    assert planner.display_name == "Daily & Weekly Planning Agent"

    email_agent = get_agent_by_name("email_agent")
    assert email_agent is not None
    assert "send_email" in email_agent.allowed_tools

    student_planner = get_agent_by_name("student_study_planner")
    assert student_planner is not None
    assert "student" in student_planner.supported_roles

    # Verify role-based agent listing
    student_agents = list_agents_for_roles(["student"])
    names = [a.name for a in student_agents]
    assert "student_study_planner" in names
    assert "student_exam_prep" in names
    assert "personal_assistant" in names  # Common agents always included


def test_tools_registry():
    expected_tools = [
        "create_task",
        "batch_create_tasks",
        "update_task_status",
        "delete_task",
        "list_tasks",
        "create_goal",
        "list_goals",
        "create_habit",
        "log_habit",
        "list_habits",
        "create_calendar_block",
        "list_calendar_events",
        "delete_calendar_event",
        "save_daily_plan",
        "store_long_term_memory",
        "search_memory",
        "delete_memory",
        "compose_email_draft",
        "send_email",
        "web_research",
        "generate_review_report",
    ]
    for t_name in expected_tools:
        tool = get_tool(t_name)
        assert tool is not None, f"Tool {t_name} should be registered in ALL_TOOLS"
        assert tool.name == t_name
        assert len(tool.description) > 5


def test_provider_registry():
    prov = ProviderRegistry.get_provider("openai_compatible")
    assert prov.provider_name == "openai_compatible"

    ollama = ProviderRegistry.get_provider("ollama_local")
    assert ollama.provider_name == "ollama_local"
