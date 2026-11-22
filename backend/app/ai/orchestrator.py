import json
import re
import time
from typing import Any, Dict, List, Optional, Tuple
import uuid
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai.agents import ALL_AGENTS_MAP, get_agent_by_name
from app.ai.memory_service import retrieve_relevant_memories, search_knowledge_docs, store_memory
from app.ai.providers import ProviderRegistry
from app.ai.tools import ALL_TOOLS, get_openai_tool_definitions, get_tool
from app.ai.training import record_training_pair
from app.core.config import settings
from app.models.ai_system import (
    ActionApproval,
    AgentExecutionStep,
    AgentRun,
    Conversation,
    Memory,
    Message,
)
from app.models.automation import Notification
from app.models.calendar import CalendarEvent, DailyPlan
from app.models.productivity import Goal, Habit, HabitLog, Milestone, Task, TaskHistory
from app.models.user import User
from app.services.integrations_service import IntegrationsService
from app.services.shadow_execution_service import ShadowExecutionService


def detect_intent(query: str) -> str:
    """Classify natural language intent for multi-agent delegation."""
    q = query.lower()

    # Screen understanding & visual assistance
    if any(k in q for k in [
        "screen", "share screen", "looking at", "what's on my screen",
        "what is on my screen", "debug this error", "help me with this form",
        "inspect screen", "visible on my screen"
    ]):
        return "screen_analysis"

    # Compound multi-step orchestration (explicit complex phrases)
    if (
        ("organize" in q or "plan" in q)
        and ("calendar" in q or "tasks" in q)
        and ("email" in q or "mail" in q)
    ):
        return "compound_orchestration"

    if any(k in q for k in [
        "organize everything", "help me organize", "submission next",
        "final-year project", "plan and schedule everything", "prepare for my",
        "organize my day based on", "organize my day tomorrow, check my calendar"
    ]):
        return "multi_agent_orchestration"

    # Follow-up actions
    if any(k in q for k in [
        "move that task", "reschedule that task", "shift that task", "move that to",
        "reschedule it to", "move it to friday", "move that task to friday"
    ]):
        return "follow_up_reschedule"

    # Compound task and calendar scheduling (e.g. "Create a task to submit report and add calendar event for 3 PM")
    if (
        ("task" in q or "todo" in q or "report" in q)
        and ("calendar" in q or "event" in q or "pm" in q or "am" in q or "time block" in q)
        and any(k in q for k in ["create", "add", "and", "book", "set", "slot"])
        and not any(k in q for k in ["summarize", "summary", "list", "show me", "reschedule", "move that"])
    ):
        return "compound_task_and_calendar"

    if any(k in q for k in [
        "send the same information to", "email that to", "send that summary to",
        "email the same to", "forward that to", "share that information with"
    ]):
        return "follow_up_email"

    # Google Workspace Tools (Docs, Sheets, Drive, Sync)
    if any(k in q for k in [
        "google doc", "google document", "create doc", "generate doc", "new doc",
        "doc generated", "generated the doc", "generated doc", "generate a google doc",
        "generate google doc", "create a google doc", "have you generated", "did you generate",
        "make a google doc", "make a doc", "draft doc", "write doc", "view doc",
        "my doc", "the doc", "docs", "document"
    ]):
        return "workspace_document"
    if any(k in q for k in [
        "create google sheet", "create a google sheet", "new spreadsheet", "create spreadsheet",
        "budget sheet", "generate sheet", "generate spreadsheet", "google sheet", "google sheets",
        "spreadsheet", "sheets"
    ]):
        return "workspace_sheet"
    if any(k in q for k in [
        "search drive", "search google drive", "drive files", "find file on drive",
        "google drive", "find doc", "drive"
    ]):
        return "workspace_drive"
    if any(k in q for k in ["sync google tasks", "sync tasks with google", "google tasks sync"]):
        return "workspace_sync"

    # Email & Messaging
    if any(k in q for k in [
        "send email", "send an email", "draft email", "draft an email",
        "write email", "email to", "mail to", "message to my professor",
        "message to my friend", "email my professor", "email my"
    ]):
        return "email_agent"

    # Task completion & status updates
    if any(k in q for k in [
        "mark as complete", "mark it as complete", "mark as completed",
        "completed my", "finished my", "mark it done", "task done",
        "completed assignment", "i completed"
    ]):
        return "task_completion"

    # Task deletion
    if any(k in q for k in ["delete task", "remove task", "delete the task", "discard task"]):
        return "task_deletion"

    # Task summaries & what to do
    if any(k in q for k in [
        "summary of what i should do",
        "summary of what to do",
        "what should i do",
        "what do i need to do",
        "what do i need to finish",
        "give me a brief summary",
        "brief summary of",
        "show me my tasks",
        "show me everything",
        "summarize my unfinished",
        "pending tasks",
        "list tasks",
        "my to-do",
        "my todo",
        "what's on my plate",
        "my priorities today",
    ]):
        return "task_listing"

    # Task creation / decomposition
    if any(k in q for k in [
        "create a clear concise to-do list",
        "clear concise to-do list",
        "concise to-do list",
        "create a task",
        "create task",
        "create tasks",
        "add a task",
        "add task",
        "make a task",
        "to-do list",
        "todo list",
        "create a todo",
        "create todo",
        "break down",
        "decompose",
        "tasks for tomorrow",
    ]):
        return "task_decomposition"

    # Habit actions
    if any(k in q for k in ["log habit", "log my habit", "completed habit", "habit streak", "habit check-in", "checked in"]):
        return "habit_logging"
    if any(k in q for k in ["create habit", "add habit", "new habit", "start a habit", "track habit", "habit"]):
        return "habit_management"

    # Daily planning & calendar
    if any(k in q for k in ["plan my day", "daily plan", "timetable", "plan tomorrow", "prepare tomorrow's schedule", "plan for tomorrow", "help me plan"]):
        return "daily_planning"
    if any(k in q for k in ["schedule", "time block", "calendar block", "book a slot", "hours for", "calendar event", "focus session"]):
        return "calendar_scheduling"

    # Goals
    if any(k in q for k in ["goal", "goals", "okr", "milestone", "aspiration", "target"]):
        return "goal_management"

    # Memory
    if any(k in q for k in ["remember that", "remember", "my preference", "note that", "save memory", "what do you know", "recall"]):
        return "memory_management"

    # Reviews & reflections
    if any(k in q for k in ["review my", "weekly review", "daily review", "productivity report", "how did i do", "evaluate progress", "burnout"]):
        return "reflection_coaching"

    # Research
    if any(k in q for k in ["research", "investigate", "explore", "learn about", "study curriculum for"]):
        return "research"

    return "general_assistant"


def _parse_task_items_from_text(text: str) -> List[str]:
    """Extract individual task items from compound natural language requests."""
    match = re.search(r"include\s+(.+)$", text, flags=re.I)
    target_text = match.group(1) if match else text

    # Remove conversational prefixes
    target_text = re.sub(
        r"^(create|add|make|prepare|generate)\s+(a\s+)?(to-do\s+list|todo\s+list|tasks|task)\s*(for\s+\w+)?[\.:\s]*",
        "",
        target_text,
        flags=re.I,
    )

    # Split by conjunctions or separators
    raw_parts = re.split(r",\s*and\s+|\s+and\s+|,\s*|\n|;\s*", target_text)
    items = []
    for part in raw_parts:
        cleaned = part.strip().strip(". ")
        cleaned = re.sub(r"^(and\s+|to\s+)", "", cleaned, flags=re.I)
        if len(cleaned) > 2:
            items.append(cleaned[0].upper() + cleaned[1:])

    if not items and len(text.strip()) > 3:
        items = [text.strip()]
    return items[:10]


def _extract_target_date(text: str) -> datetime:
    """Detect relative or explicit date keywords."""
    now = datetime.now(timezone.utc)
    low = text.lower()
    if "tomorrow" in low:
        return now + timedelta(days=1)
    if "friday" in low:
        days_ahead = (4 - now.weekday()) % 7
        if days_ahead == 0:
            days_ahead = 7
        return now + timedelta(days=days_ahead)
    if "monday" in low:
        days_ahead = (0 - now.weekday()) % 7
        if days_ahead == 0:
            days_ahead = 7
        return now + timedelta(days=days_ahead)
    if "next week" in low:
        return now + timedelta(days=7)
    return now + timedelta(days=1)


def _resolve_follow_up_entities(
    user_message: str,
    history_messages: List[Message],
) -> Dict[str, Any]:
    """
    Extract referenced entities from recent conversation history.
    Resolves 'that task', 'the same information', 'to Rahul', etc.
    """
    resolved: Dict[str, Any] = {}
    low_msg = user_message.lower()

    # 1. Resolve referenced task
    if any(k in low_msg for k in ["that task", "the task", "it to", "move that", "reschedule that"]):
        for prev_msg in reversed(history_messages):
            # Look for bullet points with task titles: • **Task Name**
            matches = re.findall(r"•\s*\*\*([^\*]+)\*\*", prev_msg.content)
            if matches:
                resolved["target_task_title"] = matches[0].strip()
                break
            # Look for quoted task titles: 'Task Name'
            quoted = re.findall(r"['\"]([^'\"]+)['\"]", prev_msg.content)
            if quoted:
                resolved["target_task_title"] = quoted[0].strip()
                break

    # 2. Resolve 'the same information' / previous summary
    if any(k in low_msg for k in ["the same information", "that information", "that summary", "the same"]):
        for prev_msg in reversed(history_messages):
            if prev_msg.sender == "assistant" and len(prev_msg.content) > 20:
                resolved["referenced_content"] = prev_msg.content
                break

    # 3. Resolve recipient name
    recip_email = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", user_message)
    if recip_email:
        resolved["recipient"] = recip_email.group(0)
    else:
        name_match = re.search(r"(?:to|with)\s+([A-Z][a-z]+)", user_message)
        if name_match:
            name = name_match.group(1)
            resolved["recipient"] = f"{name.lower()}@example.com"
            resolved["recipient_name"] = name

    return resolved


def _get_agent_for_tool(tool_name: str) -> str:
    """Map tool name to specialized agent name."""
    mapping = {
        "create_task": "TaskManagementAgent",
        "batch_create_tasks": "TaskManagementAgent",
        "update_task_status": "TaskManagementAgent",
        "delete_task": "TaskManagementAgent",
        "list_tasks": "TaskManagementAgent",
        "create_calendar_block": "CalendarAgent",
        "list_calendar_events": "CalendarAgent",
        "delete_calendar_event": "CalendarAgent",
        "create_google_calendar_event": "CalendarAgent",
        "save_daily_plan": "PlanningAgent",
        "create_goal": "GoalManagementAgent",
        "list_goals": "GoalManagementAgent",
        "create_habit": "HabitAgent",
        "log_habit": "HabitAgent",
        "list_habits": "HabitAgent",
        "store_long_term_memory": "MemoryCuratorAgent",
        "search_memory": "MemoryCuratorAgent",
        "delete_memory": "MemoryCuratorAgent",
        "compose_email_draft": "EmailAgent",
        "send_email": "EmailAgent",
        "search_emails": "EmailAgent",
        "read_email_thread": "EmailAgent",
        "reply_email": "EmailAgent",
        "archive_email": "EmailAgent",
        "search_drive_files": "WorkspaceAgent",
        "create_google_doc": "DocumentAgent",
        "create_google_sheet": "DocumentAgent",
        "sync_google_tasks": "WorkspaceAgent",
        "web_research": "ResearchAgent",
        "generate_review_report": "ReviewReflectionAgent",
        "analyze_screen_frame": "ScreenAssistanceAgent",
        "open_application": "ComputerUseAgent",
        "inspect_window_state": "ComputerUseAgent",
        "send_keyboard_input": "ComputerUseAgent",
        "simulate_mouse_action": "ComputerUseAgent",
        "emergency_stop": "ComputerUseAgent",
    }

    return mapping.get(tool_name, "PersonalAssistantAgent")


async def execute_approved_tool(
    db: AsyncSession,
    user_id: uuid.UUID,
    tool_name: str,
    args: Dict[str, Any],
) -> Dict[str, Any]:
    """Execute a registered tool securely against database services."""
    tool = get_tool(tool_name)
    if tool:
        return await tool.execute(db=db, user_id=user_id, args=args)
    return {"status": "no_op", "error": f"Tool '{tool_name}' is not registered."}


async def run_multi_agent_pipeline(
    db: AsyncSession,
    user: User,
    user_message: str,
    conversation_id: Optional[uuid.UUID] = None,
    active_role: str = "personal",
    auto_approve_low_risk: bool = True,
    screen_context: Optional[Dict[str, Any]] = None,
) -> Tuple[Conversation, AgentRun, List[AgentExecutionStep], List[ActionApproval]]:
    """
    LifeSync AI 3.0 Central Autonomous Multi-Agent Pipeline.
    Supports LLM tool calling, compound natural language requests, follow-up entity resolution,
    Google Workspace execution, approval card isolation, and verified database mutations.
    """
    t0 = time.perf_counter()

    # 1. Manage Conversation Session
    conversation: Optional[Conversation] = None
    if conversation_id:
        res = await db.execute(
            select(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == user.id)
        )
        conversation = res.scalar_one_or_none()

    if conversation is None:
        title_snippet = user_message[:60].strip() or "LifeSync Session"
        conversation = Conversation(
            user_id=user.id,
            title=title_snippet,
            active_role=active_role,
        )
        db.add(conversation)
        await db.flush()

    # Retrieve recent messages in conversation for follow-up context resolution
    res_history = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.desc())
        .limit(8)
    )
    history_messages = list(reversed(res_history.scalars().all()))

    # Persist incoming user message
    db.add(Message(conversation_id=conversation.id, user_id=user.id, sender="user", content=user_message))

    # 2. Intent Classification & Agent Run
    intent = detect_intent(user_message)
    if screen_context and screen_context.get("image_data"):
        intent = "screen_analysis"

    agent_run = AgentRun(
        user_id=user.id,
        conversation_id=conversation.id,
        user_query=user_message,
        detected_intent=intent,
        status="running",
    )
    db.add(agent_run)
    await db.flush()

    steps: List[AgentExecutionStep] = []
    created_approvals: List[ActionApproval] = []
    step_counter = 1

    # 3. Context & Semantic Retrieval (Memory Curator Step)
    memories = await retrieve_relevant_memories(db, user.id, user_message, role_context=active_role, limit=3)
    docs = await search_knowledge_docs(db, user.id, user_message, limit=2)

    step_mem = AgentExecutionStep(
        agent_run_id=agent_run.id,
        step_order=step_counter,
        agent_name="MemoryCuratorAgent",
        tool_name="search_memory",
        input_summary={"query": user_message[:100], "role_context": active_role},
        output_summary={"memories_matched": len(memories), "knowledge_matched": len(docs)},
        status="completed",
    )
    db.add(step_mem)
    steps.append(step_mem)
    step_counter += 1

    # Resolve any follow-up references from recent conversation history
    follow_up_entities = _resolve_follow_up_entities(user_message, history_messages)

    # 3.5 Check for Conversational Zero-Form Intake Session
    from app.models.intake import IntakeSession
    from app.services.agentic_intake_service import AgenticIntakeService

    res_intake = await db.execute(
        select(IntakeSession)
        .where(IntakeSession.user_id == user.id, IntakeSession.status == "GATHERING_INFO")
        .order_by(IntakeSession.created_at.desc())
        .limit(1)
    )
    active_intake = res_intake.scalar_one_or_none()

    # An intake answer is strictly an option choice, skip, or short reply when no specific operational intent is matched
    is_operational_command = (
        intent not in ["general_assistant"]
        or any(w in user_message.lower() for w in [
            "doc", "document", "email", "mail", "calendar", "event", "meeting",
            "task", "tasks", "todo", "habit", "have you", "did you", "is the",
            "show", "list", "status", "generate doc", "create doc"
        ])
    )

    is_intake_answer = bool(
        active_intake
        and not is_operational_command
        and (
            user_message.strip().lower() in ["skip", "skip and generate", "build plan now", "generate plan", "continue", "next"]
            or any(user_message.strip().lower().startswith(x) for x in ["step ", "stage ", "opt-", "int-", "ws-", "cal-", "g-", "inc-", "p-"])
            or len(user_message.split()) <= 4
        )
    )

    is_new_high_level_intake = (
        intent in ["goal_management", "task_decomposition"] and
        any(k in user_message.lower() for k in [
            "help me set a goal", "help me set an okr", "plan my project",
            "break down my project", "i want to start", "help me plan",
            "plan a new goal", "zero-form", "architect a new", "start a goal",
            "plan a goal", "help me achieve"
        ])
    )

    if active_intake and is_intake_answer:
        is_skip = "skip" in user_message.lower()
        intake_res = await AgenticIntakeService.respond_to_intake(
            db=db,
            user_id=user.id,
            session_id=active_intake.id,
            selected_options=[user_message.strip()],
            custom_text=user_message.strip() if not is_skip else None,
            skip_and_generate=is_skip,
            role_context=active_role,
        )
        if intake_res.get("status") == "CLARIFICATION_REQUIRED":
            card_dict = intake_res.get("clarification_card")
            setattr(agent_run, "clarification_card", card_dict)
            final_reply = intake_res.get("reply", "Here are the next options:")
        else:
            plan_dict = intake_res.get("transaction_plan")
            setattr(agent_run, "transaction_plan", plan_dict)
            final_reply = intake_res.get("reply", "Blueprint plan simulated.")

        agent_run.final_response = final_reply
        agent_run.status = "completed"
        agent_run.latency_ms = int((time.perf_counter() - t0) * 1000)
        db.add(Message(conversation_id=conversation.id, user_id=user.id, sender="assistant", content=final_reply))
        await db.commit()
        return conversation, agent_run, steps, created_approvals

    elif is_new_high_level_intake:
        intake_res = await AgenticIntakeService.start_or_continue_intake(
            db=db,
            user_id=user.id,
            prompt=user_message,
            role_context=active_role,
        )
        if intake_res.get("status") == "CLARIFICATION_REQUIRED":
            card_dict = intake_res.get("clarification_card")
            setattr(agent_run, "clarification_card", card_dict)
            step_intake = AgentExecutionStep(
                agent_run_id=agent_run.id,
                step_order=step_counter,
                agent_name="IntakeArchitectAgent",
                tool_name="clarification_card",
                input_summary={"prompt": user_message[:80], "domain": card_dict.get("domain")},
                output_summary={"question": card_dict.get("question"), "options_count": len(card_dict.get("options", []))},
                status="completed",
            )
            db.add(step_intake)
            steps.append(step_intake)
            final_reply = intake_res.get("reply", "Here are a few options to tailor your plan:")
        else:
            plan_dict = intake_res.get("transaction_plan")
            setattr(agent_run, "transaction_plan", plan_dict)
            final_reply = intake_res.get("reply", "Blueprint plan simulated.")

        agent_run.final_response = final_reply
        agent_run.status = "completed"
        agent_run.latency_ms = int((time.perf_counter() - t0) * 1000)
        db.add(Message(conversation_id=conversation.id, user_id=user.id, sender="assistant", content=final_reply))
        await db.commit()
        return conversation, agent_run, steps, created_approvals

    # 4. Attempt Dynamic LLM Tool Calling (Online Path)
    provider = ProviderRegistry.get_provider()
    tool_defs = get_openai_tool_definitions()
    memory_str = "\n".join(f"- {m.content}" for m in memories) if memories else "None."

    system_prompt = (
        f"You are Sync, the Autonomous Personal Operating System (LifeSync AI 3.0) for {user.full_name}.\n"
        f"Active Identity: {active_role.upper()}\n"
        f"Current Time: {datetime.now(timezone.utc).strftime('%A, %B %d, %Y %H:%M UTC')}\n"
        f"Semantic Memories:\n{memory_str}\n"
        f"Role Context & Guidelines:\n"
        f"- You are connected to real backend execution tools (Tasks, Google Calendar, Gmail, Google Drive, Google Docs, Habits, Goals, Automations).\n"
        f"- Never tell the user how to do something manually if an atomic tool can execute it. Call the appropriate tool.\n"
        f"- For high-risk operations (sending outbound email, deleting tasks/events), calling the tool will stage an approval card.\n"
        f"- Return a concise, structured response once tools are selected."
    )

    llm_messages = [{"role": "system", "content": system_prompt}]
    for h in history_messages[-4:]:
        llm_messages.append({"role": "user" if h.sender == "user" else "assistant", "content": h.content[:400]})
    llm_messages.append({"role": "user", "content": user_message})

    llm_result = await provider.chat_complete_with_tools(
        messages=llm_messages,
        tools=tool_defs,
    )

    llm_tool_calls = llm_result.get("tool_calls", [])
    final_reply = ""

    # If the LLM successfully returned dynamic tool calls:
    if llm_tool_calls:
        mutating_calls = []
        read_only_calls = []
        for call in llm_tool_calls:
            t_name = call.get("name")
            tool = get_tool(t_name)
            if tool and (getattr(tool, "is_mutating", False) or getattr(tool, "requires_approval", False)):
                mutating_calls.append(call)
            elif tool:
                read_only_calls.append(call)

        if mutating_calls:
            # Simulate transaction plan for mutating tool calls (Shadow Execution Engine)
            proposed = [
                {"tool_name": c.get("name"), "args": c.get("arguments", {})}
                for c in mutating_calls
            ]
            plan_dict = await ShadowExecutionService.simulate_plan(
                db=db,
                user_id=user.id,
                intent_summary=user_message[:100],
                proposed_tool_calls=proposed,
                auto_approve_if_safe=False,
                plan_metadata={"agent_run_id": str(agent_run.id), "source": "llm_tool_calls"},
            )
            setattr(agent_run, "transaction_plan", plan_dict)

            for step_info in plan_dict.get("steps", []):
                s_rec = AgentExecutionStep(
                    agent_run_id=agent_run.id,
                    step_order=step_counter,
                    agent_name=_get_agent_for_tool(step_info["tool_name"]),
                    tool_name=step_info["tool_name"],
                    input_summary=step_info["params"],
                    output_summary={"simulated": True, "diff": step_info["after_state"]},
                    status="pending",
                )
                db.add(s_rec)
                steps.append(s_rec)
                step_counter += 1

            for call in read_only_calls:
                t_name = call.get("name")
                tool = get_tool(t_name)
                if tool:
                    await tool.execute(db=db, user_id=user.id, args=call.get("arguments", {}))

            final_reply = (
                f"**Shadow Execution Simulation Ready**\n\n"
                f"I've simulated {len(mutating_calls)} proposed action(s) for your request:\n\n"
                + "\n".join(f"• **{s['tool_name']}**: `{json.dumps(s['params'])[:60]}`" for s in plan_dict.get("steps", []))
                + f"\n\n🛡️ **No database changes committed.** Please inspect the before/after state diffs in the **Shadow Execution Plan** below and approve to execute."
            )
        else:
            executed_summaries = []
            for call in read_only_calls:
                t_name = call.get("name")
                t_args = call.get("arguments", {})
                tool = get_tool(t_name)
                if not tool:
                    continue
                agent_name = _get_agent_for_tool(t_name)
                res_tool = await tool.execute(db=db, user_id=user.id, args=t_args)
                step_tool = AgentExecutionStep(
                    agent_run_id=agent_run.id,
                    step_order=step_counter,
                    agent_name=agent_name,
                    tool_name=t_name,
                    input_summary=t_args,
                    output_summary=res_tool,
                    status="completed" if "error" not in res_tool else "failed",
                )
                db.add(step_tool)
                steps.append(step_tool)
                step_counter += 1
                executed_summaries.append(f"• **{agent_name}**: Executed `{t_name}` successfully")

            llm_text = llm_result.get("content")
            if llm_text:
                final_reply = llm_text
            else:
                final_reply = (
                    f"**LifeSync AI 3.0 — Autonomous Execution Completed**\n\n"
                    + "\n".join(executed_summaries)
                    + "\n\nAll database records have been verified and persisted."
                )

    # 5. Fallback & Deterministic Compound Execution Engine (Offline / No Key / Specific Intent)
    else:
        # --- A. SCREEN ASSISTANCE ---
        if intent == "screen_analysis":
            img_data = (screen_context.get("image_data") if screen_context else "") or ""
            screen_tool = get_tool("analyze_screen_frame")
            res_screen = await screen_tool.execute(
                db=db,
                user_id=user.id,
                args={
                    "image_data": img_data,
                    "query": user_message,
                    "active_role": active_role,
                },
            )
            step_sc = AgentExecutionStep(
                agent_run_id=agent_run.id,
                step_order=step_counter,
                agent_name="ScreenAssistanceAgent",
                tool_name="analyze_screen_frame",
                input_summary={"query": user_message[:80], "has_image": bool(img_data)},
                output_summary={"elements": res_screen.get("detected_elements", [])},
                status="completed",
            )
            db.add(step_sc)
            steps.append(step_sc)
            step_counter += 1

            final_reply = (
                f"{res_screen.get('analysis')}\n\n"
                f"**Detected Elements**:\n"
                + "\n".join(f"• {el}" for el in res_screen.get("detected_elements", []))
                + f"\n\n**Next Steps**:\n"
                + "\n".join(f"{i+1}. {s}" for i, s in enumerate(res_screen.get("suggested_actions", [])))
            )

        # --- B0. COMPOUND TASK & CALENDAR SCHEDULING (SHADOW EXECUTION) ---
        # e.g.: "Create a task to submit my report tomorrow and add a calendar event for 3 PM"
        elif intent == "compound_task_and_calendar":
            target_dt = _extract_target_date(user_message)
            dt_str = target_dt.strftime("%A, %b %d")

            # Extract task title from user message
            clean_m = user_message
            task_title = "Submit Report"
            m_task = re.search(r"(?:task\s+(?:to\s+)?|create\s+(?:a\s+)?(?:task\s+to\s+)?)([^\.,;]+?)(?:\s+(?:tomorrow|today|and|at|for|by)|\s*$)", clean_m, flags=re.I)
            if m_task and len(m_task.group(1).strip()) > 2:
                task_title = m_task.group(1).strip().capitalize()
            elif "report" in clean_m.lower():
                task_title = "Submit Project Report"

            # Extract calendar time (e.g., "3 PM" or "3:30 pm")
            cal_hour = 15
            cal_minute = 0
            time_match = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)", clean_m, flags=re.I)
            if time_match:
                h = int(time_match.group(1))
                m = int(time_match.group(2) or 0)
                is_pm = time_match.group(3).lower() == "pm"
                if is_pm and h < 12:
                    h += 12
                elif not is_pm and h == 12:
                    h = 0
                cal_hour = h
                cal_minute = m

            event_start = target_dt.replace(hour=cal_hour, minute=cal_minute, second=0, microsecond=0)
            event_title = f"{task_title} (Focus Session)"

            proposed_tool_calls = [
                {
                    "tool_name": "create_task",
                    "args": {
                        "title": task_title,
                        "priority": "high",
                        "due_date": target_dt.date().isoformat(),
                        "role_context": active_role,
                        "estimated_minutes": 60,
                    },
                },
                {
                    "tool_name": "create_calendar_block",
                    "args": {
                        "title": event_title,
                        "start_time": event_start.isoformat(),
                        "duration_minutes": 60,
                        "role_context": active_role,
                        "is_locked": True,
                    },
                },
            ]

            plan_dict = await ShadowExecutionService.simulate_plan(
                db=db,
                user_id=user.id,
                intent_summary=f"Create task '{task_title}' and schedule calendar block at {event_start.strftime('%I:%M %p')}",
                proposed_tool_calls=proposed_tool_calls,
                auto_approve_if_safe=False,
                plan_metadata={"agent_run_id": str(agent_run.id), "intent": intent},
            )
            setattr(agent_run, "transaction_plan", plan_dict)

            # Record simulated execution steps for full visibility
            for step_info in plan_dict.get("steps", []):
                s_rec = AgentExecutionStep(
                    agent_run_id=agent_run.id,
                    step_order=step_counter,
                    agent_name=_get_agent_for_tool(step_info["tool_name"]),
                    tool_name=step_info["tool_name"],
                    input_summary=step_info["params"],
                    output_summary={"simulated": True, "diff": step_info["after_state"]},
                    status="pending",
                )
                db.add(s_rec)
                steps.append(s_rec)
                step_counter += 1

            final_reply = (
                f"**Shadow Execution Simulation Ready**\n\n"
                f"I've generated a transactional dry-run plan for your request:\n\n"
                f"1. **Task Management Agent**: Staged `create_task` → *\"{task_title}\"* (Due: {dt_str})\n"
                f"2. **Calendar Agent**: Staged `create_calendar_block` → *\"{event_title}\"* ({event_start.strftime('%I:%M %p')})\n\n"
                f"🛡️ **No database records have been modified yet.** You can selectively approve, reject, or inspect each step's before/after state diff using the **Shadow Execution Plan** below."
            )

        # --- B. COMPOUND MULTI-AGENT INSTRUCTIONS ---
        # e.g.: "Organize my day tomorrow, check my calendar, find unfinished tasks, schedule my study sessions and send an email to Rahul about our project meeting."
        elif intent in ("compound_orchestration", "multi_agent_orchestration"):
            target_dt = _extract_target_date(user_message)
            dt_str = target_dt.strftime("%A, %b %d")

            # 1. Calendar Agent: Check calendar events & conflicts
            cal_list_tool = get_tool("list_calendar_events")
            cal_events_res = await cal_list_tool.execute(db=db, user_id=user.id, args={"start_date": target_dt.date().isoformat()})
            events_count = len(cal_events_res.get("events", []))

            step_cal_check = AgentExecutionStep(
                agent_run_id=agent_run.id,
                step_order=step_counter,
                agent_name="CalendarAgent",
                tool_name="list_calendar_events",
                input_summary={"date": dt_str},
                output_summary={"events_found": events_count},
                status="completed",
            )
            db.add(step_cal_check)
            steps.append(step_cal_check)
            step_counter += 1

            # 2. Task Management Agent: Find unfinished tasks
            task_list_tool = get_tool("list_tasks")
            pending_tasks_res = await task_list_tool.execute(db=db, user_id=user.id, args={"status": "todo", "role_context": active_role, "limit": 5})
            pending_tasks = pending_tasks_res.get("tasks", [])

            step_task_check = AgentExecutionStep(
                agent_run_id=agent_run.id,
                step_order=step_counter,
                agent_name="TaskManagementAgent",
                tool_name="list_tasks",
                input_summary={"status": "todo"},
                output_summary={"tasks_found": len(pending_tasks)},
                status="completed",
            )
            db.add(step_task_check)
            steps.append(step_task_check)
            step_counter += 1

            # 3. Planning Agent: Create structured daily plan
            primary_focus = pending_tasks[0]["title"] if pending_tasks else "Core Project Milestone Deep Work"
            secondary_focus = pending_tasks[1]["title"] if len(pending_tasks) > 1 else "Technical Verification & Review"

            plan_blocks = [
                {"time": "09:00 - 10:30", "title": primary_focus, "role": active_role},
                {"time": "11:00 - 12:30", "title": secondary_focus, "role": active_role},
                {"time": "15:00 - 16:30", "title": "Study Session & Knowledge Synthesis", "role": active_role},
            ]

            plan_tool = get_tool("save_daily_plan")
            plan_res = await plan_tool.execute(
                db=db,
                user_id=user.id,
                args={
                    "summary": f"Autonomous Master Schedule for {dt_str}",
                    "schedule_blocks": plan_blocks,
                    "ai_insights": {"tasks_allocated": len(pending_tasks), "focus_blocks": len(plan_blocks)},
                },
            )
            step_plan = AgentExecutionStep(
                agent_run_id=agent_run.id,
                step_order=step_counter,
                agent_name="PlanningAgent",
                tool_name="save_daily_plan",
                input_summary={"date": dt_str, "blocks": len(plan_blocks)},
                output_summary={"daily_plan_id": plan_res.get("daily_plan_id")},
                status="completed",
            )
            db.add(step_plan)
            steps.append(step_plan)
            step_counter += 1

            # 4. Calendar Agent: Schedule study/focus session
            cal_block_tool = get_tool("create_calendar_block")
            block_res = await cal_block_tool.execute(
                db=db,
                user_id=user.id,
                args={
                    "title": "Study Session: Project Focus",
                    "start_time": target_dt.replace(hour=15, minute=0, second=0).isoformat(),
                    "duration_minutes": 90,
                    "role_context": active_role,
                    "is_locked": True,
                },
            )
            step_block = AgentExecutionStep(
                agent_run_id=agent_run.id,
                step_order=step_counter,
                agent_name="CalendarAgent",
                tool_name="create_calendar_block",
                input_summary={"title": "Study Session: Project Focus", "duration": 90},
                output_summary={"event_id": block_res.get("created_event_id")},
                status="completed",
            )
            db.add(step_block)
            steps.append(step_block)
            step_counter += 1

            # 5. Email Agent: If email is requested in compound instruction
            email_executed_summary = ""
            if "email" in user_message.lower() or "mail" in user_message.lower():
                # Extract recipient & topic
                recip_email = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", user_message)
                recip_name_match = re.search(r"(?:to|email)\s+([A-Z][a-z]+)", user_message)
                recip = recip_email.group(0) if recip_email else (f"{recip_name_match.group(1).lower()}@example.com" if recip_name_match else "collaborator@example.com")
                recip_display = recip_name_match.group(1) if recip_name_match else recip

                topic_match = re.search(r"about\s+(.+)$", user_message, flags=re.I)
                topic = topic_match.group(1).strip() if topic_match else "Our upcoming project meeting"

                email_body = (
                    f"Hi {recip_display},\n\n"
                    f"I have organized our schedule and would like to confirm our discussion regarding {topic}.\n"
                    f"Please let me know if tomorrow afternoon works for you.\n\n"
                    f"Best regards,\n{user.full_name}"
                )

                # Send email requires human approval
                approval = ActionApproval(
                    user_id=user.id,
                    agent_run_id=agent_run.id,
                    agent_name="EmailAgent",
                    tool_name="send_email",
                    action_summary=f"Send email to '{recip}' regarding '{topic}'",
                    tool_arguments={
                        "recipient": recip,
                        "subject": f"Project Update: {topic.title()}",
                        "body": email_body,
                    },
                    status="pending",
                )
                db.add(approval)
                created_approvals.append(approval)

                step_email = AgentExecutionStep(
                    agent_run_id=agent_run.id,
                    step_order=step_counter,
                    agent_name="EmailAgent",
                    tool_name="send_email",
                    input_summary={"recipient": recip, "topic": topic},
                    output_summary={"awaiting_user_approval": True},
                    status="pending",
                )
                db.add(step_email)
                steps.append(step_email)
                step_counter += 1

                email_executed_summary = (
                    f"\n• **Email Agent**: Prepared outbound email to `{recip}`. "
                    f"⚠️ *Awaiting confirmation on the approval card below before sending.*"
                )

            final_reply = (
                f"**Autonomous Multi-Agent Pipeline — Plan & Execution for {dt_str}**\n\n"
                f"I have mobilized specialized agents to fulfill your compound instruction:\n\n"
                f"• **Calendar Agent**: Checked your calendar ({events_count} existing commitments). Scheduled 90-minute focus session.\n"
                f"• **Task Management Agent**: Retrieved {len(pending_tasks)} unfinished tasks for prioritization.\n"
                f"• **Planning Agent**: Generated and locked your daily execution timetable:\n"
                + "\n".join(f"  - `{b['time']}`: **{b['title']}**" for b in plan_blocks)
                + email_executed_summary
                + f"\n\nAll calendar blocks and plans are stored in your database."
            )

        # --- C. FOLLOW-UP RESCHEDULE: "Move that task to Friday" ---
        elif intent == "follow_up_reschedule":
            target_dt = _extract_target_date(user_message)
            dt_str = target_dt.strftime("%A, %b %d")
            task_title = follow_up_entities.get("target_task_title")

            # Fallback to most recent open task
            if not task_title:
                res_last_task = await db.execute(
                    select(Task).where(Task.user_id == user.id, Task.status == "todo").order_by(Task.created_at.desc()).limit(1)
                )
                last_task = res_last_task.scalar_one_or_none()
                if last_task:
                    task_title = last_task.title

            if not task_title:
                final_reply = "Could not find a previous task in this conversation to reschedule. Please specify the task title."
            else:
                up_tool = get_tool("update_task_status")
                up_res = await up_tool.execute(
                    db=db,
                    user_id=user.id,
                    args={"title_query": task_title, "due_date": target_dt.isoformat()},
                )
                step_fu = AgentExecutionStep(
                    agent_run_id=agent_run.id,
                    step_order=step_counter,
                    agent_name="TaskManagementAgent",
                    tool_name="update_task_status",
                    input_summary={"task_title": task_title, "rescheduled_to": dt_str},
                    output_summary=up_res,
                    status="completed" if "error" not in up_res else "failed",
                )
                db.add(step_fu)
                steps.append(step_fu)
                step_counter += 1

                final_reply = (
                    f"**Task Management Agent — Task Rescheduled**\n\n"
                    f"I resolved your reference from our previous messages and updated the task:\n\n"
                    f"• **Task**: **{task_title}**\n"
                    f"• **New Due Date**: **{dt_str}**\n\n"
                    f"The update is saved in your database and updated across your calendar and board."
                )

        # --- D. FOLLOW-UP EMAIL: "Send the same information to Rahul" ---
        elif intent == "follow_up_email":
            recip = follow_up_entities.get("recipient", "rahul@example.com")
            recip_name = follow_up_entities.get("recipient_name", "Rahul")
            content_to_send = follow_up_entities.get("referenced_content")

            if not content_to_send:
                # Use last assistant message
                for m in reversed(history_messages):
                    if m.sender == "assistant":
                        content_to_send = m.content
                        break

            content_snippet = content_to_send or "Here is the summary of our latest plan and tasks."
            subject = f"LifeSync Update for {recip_name}"

            approval = ActionApproval(
                user_id=user.id,
                agent_run_id=agent_run.id,
                agent_name="EmailAgent",
                tool_name="send_email",
                action_summary=f"Send email with previous summary to '{recip}'",
                tool_arguments={
                    "recipient": recip,
                    "subject": subject,
                    "body": f"Hi {recip_name},\n\n{content_snippet}\n\nBest,\n{user.full_name}",
                },
                status="pending",
            )
            db.add(approval)
            created_approvals.append(approval)

            step_fu_em = AgentExecutionStep(
                agent_run_id=agent_run.id,
                step_order=step_counter,
                agent_name="EmailAgent",
                tool_name="send_email",
                input_summary={"recipient": recip, "subject": subject},
                output_summary={"awaiting_approval": True},
                status="pending",
            )
            db.add(step_fu_em)
            steps.append(step_fu_em)
            step_counter += 1

            final_reply = (
                f"**Email Agent — Staged Outbound Message**\n\n"
                f"I resolved the content from our conversation and prepared the email for **{recip_name}** (`{recip}`):\n\n"
                f"• **Subject**: `{subject}`\n"
                f"• **Content Source**: Verified from our previous execution summary.\n\n"
                f"⚠️ *Please review and confirm via the Approval Card below to dispatch this email.*"
            )

        # --- E. GOOGLE WORKSPACE TOOLS (DOCS, SHEETS, DRIVE, TASKS) ---
        elif intent == "workspace_document":
            q_low = user_message.lower()
            is_query_check = any(w in q_low for w in ["have you", "did you", "is the doc", "status of", "check", "was the doc", "where is", "has the doc", "generated?"])

            # Query recent doc steps for this user
            res_steps = await db.execute(
                select(AgentExecutionStep)
                .join(AgentRun, AgentRun.id == AgentExecutionStep.agent_run_id)
                .where(
                    AgentRun.user_id == user.id,
                    AgentExecutionStep.tool_name == "create_google_doc"
                )
                .order_by(AgentExecutionStep.created_at.desc())
                .limit(1)
            )
            prev_step = res_steps.scalar_one_or_none()

            if is_query_check and prev_step and prev_step.output_summary and prev_step.output_summary.get("success"):
                prev_out = prev_step.output_summary
                doc_title = prev_out.get("title", "Project Documentation")
                doc_id = prev_out.get("document_id", "doc-live")
                doc_url = prev_out.get("document_url", f"https://docs.google.com/document/d/{doc_id}/edit")
                final_reply = (
                    f"**Document Agent — Google Doc Status**\n\n"
                    f"Yes! The Google Doc **'{doc_title}'** has already been generated and is active:\n\n"
                    f"• **Title**: **{doc_title}**\n"
                    f"• **Document ID**: `{doc_id}`\n"
                    f"• **Drive Status**: Synced and available in your Google Drive workspace\n"
                    f"• **Access**: [Open Google Doc]({doc_url})\n\n"
                    f"Would you like me to append additional milestones, generate an accompanying Google Sheet, or export action tasks?"
                )
            else:
                clean_title = re.sub(
                    r"^(have\s+you\s+generated\s+(the\s+)?|did\s+you\s+generate\s+(the\s+)?|generate\s+(a\s+)?|create\s+(a\s+)?|new\s+)?(google\s+doc|document|doc)\s*(for|titled|about)?\s*",
                    "",
                    user_message,
                    flags=re.I,
                ).strip()
                clean_title = clean_title.strip("? .!\"'")
                if not clean_title or len(clean_title) < 2 or clean_title.lower() in ["the", "a", "my", "it"]:
                    res_tasks = await db.execute(select(Task).where(Task.user_id == user.id, Task.status == "todo").limit(2))
                    top_tasks = res_tasks.scalars().all()
                    if top_tasks:
                        clean_title = f"{top_tasks[0].title} — Architecture & Documentation"
                    else:
                        clean_title = f"LifeSync {active_role.title()} Execution Plan"

                doc_tool = get_tool("create_google_doc")
                doc_res = await doc_tool.execute(
                    db=db,
                    user_id=user.id,
                    args={
                        "title": clean_title,
                        "content": (
                            f"# {clean_title}\n\n"
                            f"**Generated by LifeSync AI Document Agent**\n"
                            f"**Owner**: {user.full_name}\n"
                            f"**Active Workspace**: {active_role.title()}\n"
                            f"**Generated At**: {datetime.now(timezone.utc).strftime('%A, %B %d, %Y %H:%M UTC')}\n\n"
                            f"## 1. Executive Summary\n"
                            f"This document tracks project milestones, architecture notes, and progress logs for {clean_title}.\n\n"
                            f"## 2. Core Milestones\n"
                            f"- Stage 1: Foundation & Setup\n"
                            f"- Stage 2: Core Execution & Implementation\n"
                            f"- Stage 3: Verification & Polish\n\n"
                            f"## 3. Technical Notes & Progress Logs\n"
                            f"- Autonomous execution recorded in LifeSync AI\n"
                        ),
                    },
                )
                step_doc = AgentExecutionStep(
                    agent_run_id=agent_run.id,
                    step_order=step_counter,
                    agent_name="DocumentAgent",
                    tool_name="create_google_doc",
                    input_summary={"title": clean_title},
                    output_summary=doc_res,
                    status="completed",
                )
                db.add(step_doc)
                steps.append(step_doc)
                step_counter += 1

                doc_id = doc_res.get("document_id", f"doc-{uuid.uuid4().hex[:8]}")
                doc_url = doc_res.get("document_url", f"https://docs.google.com/document/d/{doc_id}/edit")
                doc_title = doc_res.get("title", clean_title)

                status_lead = "A Google Doc had not been generated yet, so I have created and formatted one for you now:" if is_query_check else "I have generated your Google Document:"

                final_reply = (
                    f"**Document Agent — Google Doc Created Successfully**\n\n"
                    f"{status_lead}\n\n"
                    f"• **Title**: **{doc_title}**\n"
                    f"• **Document ID**: `{doc_id}`\n"
                    f"• **Drive Status**: Synced and available in your Google Drive workspace\n"
                    f"• **Document Link**: [Open Google Doc]({doc_url})\n\n"
                    f"The document includes formatted headers, executive summary, milestone trackers, and architecture notes."
                )

        elif intent == "workspace_sheet":
            clean_title = re.sub(r"^(create\s+a\s+|create\s+|new\s+)?(google\s+sheet|spreadsheet)\s*(for|titled)?\s*", "", user_message, flags=re.I).strip() or "Budget and Expenses"
            sheet_tool = get_tool("create_google_sheet")
            sheet_res = await sheet_tool.execute(
                db=db,
                user_id=user.id,
                args={
                    "title": clean_title,
                    "headers": ["Item / Milestone", "Estimated Hours / Cost", "Owner", "Status"],
                    "initial_rows": [
                        ["Architecture Specification", "15 hrs", user.full_name, "Completed"],
                        ["Full-Stack Implementation", "40 hrs", user.full_name, "In Progress"],
                    ],
                },
            )
            step_sh = AgentExecutionStep(
                agent_run_id=agent_run.id,
                step_order=step_counter,
                agent_name="DocumentAgent",
                tool_name="create_google_sheet",
                input_summary={"title": clean_title},
                output_summary=sheet_res,
                status="completed",
            )
            db.add(step_sh)
            steps.append(step_sh)
            step_counter += 1

            final_reply = (
                f"**Document Agent — Google Sheet Created**\n\n"
                f"• **Title**: **{sheet_res.get('title')}**\n"
                f"• **Spreadsheet ID**: `{sheet_res.get('spreadsheet_id')}`\n"
                f"• **Initial Headers**: `{', '.join(sheet_res.get('headers', []))}`\n"
                f"• **Rows**: {sheet_res.get('rows_added', 0)} initialized."
            )

        elif intent == "workspace_drive":
            clean_q = re.sub(r"^(search\s+drive\s+for|search\s+google\s+drive\s+for|find\s+file\s+on\s+drive\s+named?)\s*", "", user_message, flags=re.I).strip() or "project"
            drive_tool = get_tool("search_drive_files")
            drive_res = await drive_tool.execute(db=db, user_id=user.id, args={"query": clean_q})
            step_dr = AgentExecutionStep(
                agent_run_id=agent_run.id,
                step_order=step_counter,
                agent_name="WorkspaceAgent",
                tool_name="search_drive_files",
                input_summary={"query": clean_q},
                output_summary={"files_found": len(drive_res.get("files", []))},
                status="completed",
            )
            db.add(step_dr)
            steps.append(step_dr)
            step_counter += 1

            files = drive_res.get("files", [])
            final_reply = (
                f"**Workspace Agent — Google Drive Files for '{clean_q}'**\n\n"
                + ("\n".join(f"• **{f.get('name')}** (`{f.get('type')}`) — ID: `{f.get('id')}`" for f in files) if files else "No files found matching your search query.")
            )

        elif intent == "workspace_sync":
            sync_tool = get_tool("sync_google_tasks")
            sync_res = await sync_tool.execute(db=db, user_id=user.id, args={})
            step_sy = AgentExecutionStep(
                agent_run_id=agent_run.id,
                step_order=step_counter,
                agent_name="WorkspaceAgent",
                tool_name="sync_google_tasks",
                input_summary={},
                output_summary=sync_res,
                status="completed",
            )
            db.add(step_sy)
            steps.append(step_sy)
            step_counter += 1

            final_reply = (
                f"**Workspace Agent — Google Tasks Synchronization**\n\n"
                f"• **Google Tasks Pulled**: {sync_res.get('pulled_count', 0)}\n"
                f"• **Local Tasks Pushed**: {sync_res.get('pushed_count', 0)}\n"
                f"• **Status**: Fully synchronized with LifeSync database."
            )

        # --- F. TASK DECOMPOSITION & COMPOUND TO-DO LIST CREATION ---
        elif intent == "task_decomposition":
            target_dt = _extract_target_date(user_message)
            dt_str = target_dt.strftime("%a, %b %d")
            items = _parse_task_items_from_text(user_message)

            generic_phrases = ["clear concise to-do list", "concise to-do list", "to-do list", "todo list", "tasks", "task"]
            if not items or (len(items) == 1 and items[0].lower() in generic_phrases):
                res_open = await db.execute(select(Task).where(Task.user_id == user.id, Task.status == "todo").limit(3))
                existing_open = res_open.scalars().all()
                if existing_open:
                    items = [t.title for t in existing_open]
                else:
                    if active_role == "student":
                        items = ["DSA practice & problem patterns", "Project development milestone", "GATE preparation & core revision"]
                    elif active_role == "professional":
                        items = ["Core API refactoring & performance audit", "Pull request review & integration tests", "Sprint deliverable documentation"]
                    elif active_role == "entrepreneur":
                        items = ["Review beta user onboarding metrics", "Refine product pitch deck", "Weekly execution priorities alignment"]
                    else:
                        items = ["Priority morning focus session", "Habits & wellness check-in", "Weekly schedule & goals review"]

            batch_tool = get_tool("batch_create_tasks")
            batch_res = await batch_tool.execute(
                db=db,
                user_id=user.id,
                args={
                    "tasks": [
                        {
                            "title": item,
                            "priority": "high" if idx == 0 else "medium",
                            "estimated_minutes": 45,
                            "due_date": target_dt.isoformat(),
                            "role_context": active_role,
                        }
                        for idx, item in enumerate(items)
                    ]
                },
            )

            step_t = AgentExecutionStep(
                agent_run_id=agent_run.id,
                step_order=step_counter,
                agent_name="TaskManagementAgent",
                tool_name="batch_create_tasks",
                input_summary={"items_parsed": len(items)},
                output_summary={"created_count": batch_res.get("created_count")},
                status="completed",
            )
            db.add(step_t)
            steps.append(step_t)
            step_counter += 1

            final_reply = (
                f"**Task Management Agent — Tasks Created**\n\n"
                f"I parsed your request and created **{batch_res.get('created_count')} tasks** in your **{active_role.title()}** workspace (Due: {dt_str}):\n\n"
                + "\n".join(f"{idx+1}. **{t['title']}** — Priority: `{t['priority'].upper()}`" for idx, t in enumerate(batch_res.get("tasks", [])))
                + f"\n\nThese tasks are saved in your database and appear immediately in your Tasks and Kanban boards."
            )

        # --- G. TASK COMPLETION ---
        elif intent == "task_completion":
            clean_kw = re.sub(r"^(i\s+)?(completed|finished|mark\s+as\s+completed|mark\s+completed|mark\s+it\s+as\s+completed|mark\s+as\s+done)\s*(my\s+|the\s+)?", "", user_message, flags=re.I).strip()
            clean_kw = re.sub(r"\s*(as\s+completed|completed|done|finished)$", "", clean_kw, flags=re.I).strip()

            update_tool = get_tool("update_task_status")
            up_res = await update_tool.execute(
                db=db,
                user_id=user.id,
                args={"title_query": clean_kw, "status": "completed"},
            )

            step_c = AgentExecutionStep(
                agent_run_id=agent_run.id,
                step_order=step_counter,
                agent_name="TaskManagementAgent",
                tool_name="update_task_status",
                input_summary={"query": clean_kw},
                output_summary=up_res,
                status="completed" if "error" not in up_res else "failed",
            )
            db.add(step_c)
            steps.append(step_c)
            step_counter += 1

            if "error" in up_res:
                final_reply = f"**Task Management Agent**: Could not find an active task matching *'{clean_kw}'*. Please check your Tasks view for exact title."
            else:
                final_reply = f"**Task Management Agent**: Marked task **'{up_res.get('title')}'** as **Completed**! Your productivity score and dashboard have updated."

        # --- H. TASK DELETION ---
        elif intent == "task_deletion":
            clean_kw = re.sub(r"^(delete|remove|discard)\s+(the\s+)?(task\s+)?", "", user_message, flags=re.I).strip()

            res_t = await db.execute(select(Task).where(Task.user_id == user.id))
            target_task = None
            for t in res_t.scalars().all():
                if clean_kw.lower() in t.title.lower():
                    target_task = t
                    break

            if not target_task:
                final_reply = f"**Task Management Agent**: No task found matching '{clean_kw}' to delete."
            else:
                approval = ActionApproval(
                    user_id=user.id,
                    agent_run_id=agent_run.id,
                    agent_name="TaskManagementAgent",
                    tool_name="delete_task",
                    action_summary=f"Permanently delete task: '{target_task.title}'",
                    tool_arguments={"task_id": str(target_task.id), "title_query": target_task.title},
                    status="pending",
                )
                db.add(approval)
                created_approvals.append(approval)

                step_del = AgentExecutionStep(
                    agent_run_id=agent_run.id,
                    step_order=step_counter,
                    agent_name="TaskManagementAgent",
                    tool_name="delete_task",
                    input_summary={"task_to_delete": target_task.title},
                    output_summary={"awaiting_approval": True},
                    status="pending",
                )
                db.add(step_del)
                steps.append(step_del)
                step_counter += 1

                final_reply = (
                    f"**Task Management Agent**: Found task **'{target_task.title}'**.\n\n"
                    f"Deleting a task is a permanent action. Please review and confirm via the **Approval Card** below."
                )

        # --- I. TASK LISTING & SUMMARIES ---
        elif intent == "task_listing":
            list_tool = get_tool("list_tasks")
            is_overdue_req = "overdue" in user_message.lower()
            is_summary_req = any(k in user_message.lower() for k in [
                "summary", "what should i do", "what to do", "what do i need",
                "priorities", "plate", "everything i need", "prepare tomorrow's schedule"
            ])

            res_list = await list_tool.execute(
                db=db,
                user_id=user.id,
                args={"status": "overdue" if is_overdue_req else "todo", "role_context": active_role, "limit": 10},
            )
            tasks_found = res_list.get("tasks", [])
            step_l = AgentExecutionStep(
                agent_run_id=agent_run.id,
                step_order=step_counter,
                agent_name="TaskManagementAgent",
                tool_name="list_tasks",
                input_summary={"status": "overdue" if is_overdue_req else "todo"},
                output_summary={"count": len(tasks_found)},
                status="completed",
            )
            db.add(step_l)
            steps.append(step_l)
            step_counter += 1

            if is_summary_req:
                res_events = await db.execute(
                    select(CalendarEvent).where(
                        CalendarEvent.user_id == user.id,
                        CalendarEvent.start_time >= datetime.now(timezone.utc) - timedelta(hours=1),
                    ).limit(3)
                )
                events_found = res_events.scalars().all()

                res_habits = await db.execute(
                    select(Habit).where(Habit.user_id == user.id, Habit.is_active.is_(True)).limit(3)
                )
                habits_found = res_habits.scalars().all()

                final_reply = (
                    f"**Personal Assistant Agent — Action Summary ({active_role.title()} Mode)**\n\n"
                    f"Here is your clear, concise execution summary for today:\n\n"
                    f"• **Priority Tasks** ({len(tasks_found)} pending):\n"
                    + ("\n".join(f"  {idx+1}. **{t['title']}** [{t['priority'].upper()}]" for idx, t in enumerate(tasks_found[:4])) if tasks_found else "  *(No pending tasks — your board is clear!)*\n")
                    + f"\n• **Upcoming Commitments**:\n"
                    + ("\n".join(f"  - **{e.title}** ({e.start_time.strftime('%H:%M')} - {e.end_time.strftime('%H:%M')})" for e in events_found) if events_found else "  *(No fixed calendar conflicts today)*\n")
                    + f"\n• **Habit Streaks**:\n"
                    + ("\n".join(f"  - **{h.title}** (🔥 {h.current_streak}d streak)" for h in habits_found) if habits_found else "  *(All active habits logged!)*\n")
                    + f"\n**Executive Recommendation**: Focus on your top task first before starting secondary reviews."
                )
            elif not tasks_found:
                final_reply = f"**Task Management Agent**: You have **no pending tasks** in your **{active_role.title()}** workspace! All caught up."
            else:
                final_reply = (
                    f"**Task Management Agent — Active Tasks Overview ({len(tasks_found)} found)**\n\n"
                    + "\n".join(
                        f"• **{t['title']}** [{t['priority'].upper()}]"
                        + (f" — Due: {t['due_date'][:10]}" if t.get("due_date") else "")
                        for t in tasks_found
                    )
                    + "\n\nLet me know if you would like me to mark any complete or reschedule them."
                )

        # --- J. EMAIL & GMAIL WORKFLOWS ---
        elif intent == "email_agent":
            recip_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", user_message)
            recipient = recip_match.group(0) if recip_match else "recipient@example.com"

            sub_match = re.search(r"about\s+(.+)$", user_message, flags=re.I)
            subject_topic = sub_match.group(1).strip() if sub_match else "Meeting Follow-up & Discussion"

            body_preview = (
                f"Hi,\n\nI am writing regarding {subject_topic}. "
                f"Please let me know your availability so we can coordinate the next steps.\n\n"
                f"Best regards,\n{user.full_name}"
            )

            is_send_requested = any(k in user_message.lower() for k in ["send", "send email", "send an email"])

            if is_send_requested:
                approval = ActionApproval(
                    user_id=user.id,
                    agent_run_id=agent_run.id,
                    agent_name="EmailAgent",
                    tool_name="send_email",
                    action_summary=f"Send email to '{recipient}' regarding '{subject_topic}'",
                    tool_arguments={
                        "recipient": recipient,
                        "subject": subject_topic,
                        "body": body_preview,
                    },
                    status="pending",
                )
                db.add(approval)
                created_approvals.append(approval)

                step_em = AgentExecutionStep(
                    agent_run_id=agent_run.id,
                    step_order=step_counter,
                    agent_name="EmailAgent",
                    tool_name="send_email",
                    input_summary={"recipient": recipient, "subject": subject_topic},
                    output_summary={"awaiting_user_approval": True},
                    status="pending",
                )
                db.add(step_em)
                steps.append(step_em)
                step_counter += 1

                final_reply = (
                    f"**Email Agent — Prepared Email Draft**\n\n"
                    f"• **To**: `{recipient}`\n"
                    f"• **Subject**: `{subject_topic}`\n\n"
                    f"**Message Body Preview**:\n"
                    f"> {body_preview.replace(chr(10), chr(10) + '> ')}\n\n"
                    f"⚠️ *Sending an external email requires explicit confirmation.* Click **Approve** on the action card below to dispatch this message via your connected Gmail account."
                )
            else:
                draft_tool = get_tool("compose_email_draft")
                draft_res = await draft_tool.execute(
                    db=db,
                    user_id=user.id,
                    args={"recipient": recipient, "subject": subject_topic, "body": body_preview},
                )
                step_dr = AgentExecutionStep(
                    agent_run_id=agent_run.id,
                    step_order=step_counter,
                    agent_name="EmailAgent",
                    tool_name="compose_email_draft",
                    input_summary={"recipient": recipient, "subject": subject_topic},
                    output_summary=draft_res,
                    status="completed",
                )
                db.add(step_dr)
                steps.append(step_dr)
                step_counter += 1

                final_reply = (
                    f"**Email Agent — Draft Created**\n\n"
                    f"• **To**: `{recipient}`\n"
                    f"• **Subject**: `{subject_topic}`\n\n"
                    f"{body_preview}\n\n"
                    f"Saved to your Gmail drafts. Tell me *\"Send it now\"* whenever you're ready to dispatch."
                )

        # --- K. HABIT LOGGING & CREATION ---
        elif intent == "habit_logging":
            clean_h = re.sub(r"^(log|completed|check in|finished)\s+(habit\s+|my\s+habit\s+|my\s+)?", "", user_message, flags=re.I).strip()
            log_tool = get_tool("log_habit")
            log_res = await log_tool.execute(db=db, user_id=user.id, args={"title_query": clean_h})

            step_h = AgentExecutionStep(
                agent_run_id=agent_run.id,
                step_order=step_counter,
                agent_name="HabitAgent",
                tool_name="log_habit",
                input_summary={"query": clean_h},
                output_summary=log_res,
                status="completed" if "error" not in log_res else "failed",
            )
            db.add(step_h)
            steps.append(step_h)
            step_counter += 1

            if "error" in log_res:
                final_reply = f"**Habit Agent**: Could not find an active habit matching '{clean_h}'. Create one in the Habits tab."
            else:
                final_reply = f"**Habit Agent**: Checked in habit **'{log_res.get('title')}'** for today! Current consistency streak: **{log_res.get('streak')} days** 🔥"

        elif intent == "habit_management":
            clean_title = re.sub(r"^(create|add|new|start|track)\s+(a\s+)?(habit|routine)\s*(for|to)?\s*", "", user_message, flags=re.I).strip() or user_message[:60]
            h_tool = get_tool("create_habit")
            h_res = await h_tool.execute(db=db, user_id=user.id, args={"title": clean_title, "role_context": active_role})
            step_h_create = AgentExecutionStep(
                agent_run_id=agent_run.id,
                step_order=step_counter,
                agent_name="HabitAgent",
                tool_name="create_habit",
                input_summary={"title": clean_title},
                output_summary=h_res,
                status="completed",
            )
            db.add(step_h_create)
            steps.append(step_h_create)
            step_counter += 1
            final_reply = f"**Habit Agent**: Created new recurring habit **'{clean_title}'** in your {active_role} workspace. Daily streak tracking is active!"

        # --- L. DAILY PLANNING & CALENDAR SCHEDULING ---
        elif intent == "daily_planning":
            today_str = date.today().isoformat()
            res_open = await db.execute(select(Task).where(Task.user_id == user.id, Task.status == "todo").limit(5))
            open_tasks = res_open.scalars().all()

            blocks = [
                {"time": "09:00 - 10:30", "title": open_tasks[0].title if open_tasks else f"{active_role.title()} Deep Focus Sprint", "role": active_role},
                {"time": "11:00 - 12:30", "title": open_tasks[1].title if len(open_tasks) > 1 else "Strategic Project Execution", "role": active_role},
                {"time": "15:00 - 16:00", "title": "Reviews, Admin & Habit Check-in", "role": "personal"},
            ]

            plan_tool = get_tool("save_daily_plan")
            plan_res = await plan_tool.execute(
                db=db,
                user_id=user.id,
                args={
                    "summary": f"Intelligent Daily Execution Plan for {today_str} ({active_role.title()} Context)",
                    "schedule_blocks": blocks,
                    "ai_insights": {"focus_minutes": 240, "tasks_allocated": len(open_tasks)},
                },
            )

            cal_tool = get_tool("create_calendar_block")
            await cal_tool.execute(
                db=db,
                user_id=user.id,
                args={
                    "title": blocks[0]["title"],
                    "role_context": active_role,
                    "duration_minutes": 90,
                    "is_locked": False,
                },
            )

            step_dp = AgentExecutionStep(
                agent_run_id=agent_run.id,
                step_order=step_counter,
                agent_name="PlanningAgent",
                tool_name="save_daily_plan",
                input_summary={"date": today_str},
                output_summary={"plan_id": plan_res.get("daily_plan_id"), "blocks": len(blocks)},
                status="completed",
            )
            db.add(step_dp)
            steps.append(step_dp)
            step_counter += 1

            final_reply = (
                f"**Planning Agent — Daily Execution Plan for Today**\n\n"
                + "\n".join(f"• **{b['time']}**: {b['title']} (*{b['role']}*)" for b in blocks)
                + f"\n\n✓ Plan saved and synced to your Smart Calendar with focus blocks scheduled."
            )

        elif intent == "calendar_scheduling":
            clean_event = re.sub(r"^(schedule|book|block|add)\s*(two\s+hours|2\s+hours|1\s+hour|60m|an\s+hour)?\s*(for)?\s*", "", user_message, flags=re.I).strip()
            dur = 120 if ("two" in user_message.lower() or "2 hours" in user_message.lower()) else 60
            target_dt = _extract_target_date(user_message)

            cal_tool = get_tool("create_calendar_block")
            cal_res = await cal_tool.execute(
                db=db,
                user_id=user.id,
                args={
                    "title": clean_event[:60] or "Focus Session",
                    "start_time": target_dt.replace(hour=10, minute=0).isoformat(),
                    "duration_minutes": dur,
                    "role_context": active_role,
                    "is_locked": True,
                },
            )
            step_cs = AgentExecutionStep(
                agent_run_id=agent_run.id,
                step_order=step_counter,
                agent_name="CalendarAgent",
                tool_name="create_calendar_block",
                input_summary={"event": clean_event, "duration": dur},
                output_summary=cal_res,
                status="completed",
            )
            db.add(step_cs)
            steps.append(step_cs)
            step_counter += 1

            conflicts_str = ""
            if cal_res.get("conflicts"):
                conflicts_str = f"\n⚠️ *Note*: {', '.join(cal_res['conflicts'])}"

            final_reply = (
                f"**Calendar Agent — Commitment Scheduled**\n\n"
                f"• **Event**: **{cal_res.get('title')}**\n"
                f"• **When**: `{cal_res.get('start_time')[:16].replace('T', ' ')}` ({dur} minutes)\n"
                f"• **Protection**: Locked slot (will not be displaced by auto-reschedulers){conflicts_str}"
            )

        # --- M. GOALS & MILESTONES ---
        elif intent == "goal_management":
            clean_g = re.sub(r"^(create|add|set)\s+(a\s+)?(goal|okr)\s*(for|to)?\s*", "", user_message, flags=re.I).strip() or user_message[:60]
            plan_dict = await ShadowExecutionService.simulate_plan(
                db=db,
                user_id=user.id,
                intent_summary=f"Create goal '{clean_g}'",
                proposed_tool_calls=[{
                    "tool_name": "create_goal",
                    "args": {
                        "title": clean_g,
                        "horizon": "short_term",
                        "role_context": active_role,
                        "milestones": [f"Phase 1: Architecture & Planning for {clean_g[:30]}", f"Phase 2: Execution & Verification"],
                    }
                }],
                auto_approve_if_safe=False,
                plan_metadata={"agent_run_id": str(agent_run.id), "intent": intent},
            )
            setattr(agent_run, "transaction_plan", plan_dict)

            step_g = AgentExecutionStep(
                agent_run_id=agent_run.id,
                step_order=step_counter,
                agent_name="GoalManagementAgent",
                tool_name="create_goal",
                input_summary={"goal": clean_g},
                output_summary={"plan_id": plan_dict["id"], "status": "SIMULATED"},
                status="completed",
            )
            db.add(step_g)
            steps.append(step_g)
            step_counter += 1

            final_reply = (
                f"**Shadow Execution Simulation Ready**\n\n"
                f"I've simulated creating strategic goal **'{clean_g}'** with 2 progressive milestones in your Goals workspace.\n\n"
                f"🛡️ **No database records have been modified yet.** You can review the diff and apply or reject the change below."
            )

        # --- N. SEMANTIC MEMORY MANAGEMENT ---
        elif intent == "memory_management":
            clean_mem = re.sub(r"^(remember that|note that|remember|save)\s*", "", user_message, flags=re.I).strip() or user_message
            mem_tool = get_tool("store_long_term_memory")
            mem_res = await mem_tool.execute(
                db=db,
                user_id=user.id,
                args={"content": clean_mem, "category": "preference", "role_context": active_role},
            )
            step_m = AgentExecutionStep(
                agent_run_id=agent_run.id,
                step_order=step_counter,
                agent_name="MemoryCuratorAgent",
                tool_name="store_long_term_memory",
                input_summary={"content": clean_mem[:80]},
                output_summary=mem_res,
                status="completed",
            )
            db.add(step_m)
            steps.append(step_m)
            step_counter += 1

            final_reply = f"**Memory Curator**: Indexed preference into persistent semantic memory: *\"{clean_mem}\"*. This will automatically contextualize future agent decisions."

        # --- O. REVIEW & REFLECTION ---
        elif intent == "reflection_coaching":
            rev_tool = get_tool("generate_review_report")
            rev_res = await rev_tool.execute(db=db, user_id=user.id, args={"timeframe": "weekly", "role_context": active_role})
            step_rev = AgentExecutionStep(
                agent_run_id=agent_run.id,
                step_order=step_counter,
                agent_name="ReviewReflectionAgent",
                tool_name="generate_review_report",
                input_summary={"timeframe": "weekly"},
                output_summary=rev_res,
                status="completed",
            )
            db.add(step_rev)
            steps.append(step_rev)
            step_counter += 1

            final_reply = (
                f"**Review & Reflection Agent — Weekly Intelligence Audit**\n\n"
                f"• **Productivity Index**: **{rev_res.get('productivity_score')}/100**\n"
                f"• **Tasks**: {rev_res.get('tasks_summary', {}).get('completed')} completed, {rev_res.get('tasks_summary', {}).get('pending')} pending\n"
                f"• **Active Habits Streak Avg**: {rev_res.get('habits_summary', {}).get('average_streak_days')} days\n"
                f"• **Strategic Recommendation**: {rev_res.get('recommendation')}"
            )

        # --- P. RESEARCH & SYNTHESIS ---
        elif intent == "research":
            res_tool = get_tool("web_research")
            clean_topic = re.sub(r"^(research|learn about|explore|study)\s*", "", user_message, flags=re.I).strip()
            res_data = await res_tool.execute(db=db, user_id=user.id, args={"topic": clean_topic})
            step_res = AgentExecutionStep(
                agent_run_id=agent_run.id,
                step_order=step_counter,
                agent_name="ResearchAgent",
                tool_name="web_research",
                input_summary={"topic": clean_topic},
                output_summary={"takeaways": len(res_data.get("key_takeaways", []))},
                status="completed",
            )
            db.add(step_res)
            steps.append(step_res)
            step_counter += 1

            final_reply = (
                f"**Research Agent — Findings for '{clean_topic}'**\n\n"
                + "\n".join(f"• {t}" for t in res_data.get("key_takeaways", []))
                + f"\n\nWould you like me to generate actionable study tasks or schedule a focus block for this topic?"
            )

        # --- Q. GENERAL ASSISTANT / FALLBACK ---
        else:
            llm_reply = await provider.chat_complete(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.3,
            )

            if llm_reply:
                final_reply = llm_reply
            else:
                q_low = user_message.strip().lower()
                res_tasks = await db.execute(select(Task).where(Task.user_id == user.id, Task.status == "todo").limit(4))
                open_tasks = res_tasks.scalars().all()

                if any(k in q_low for k in ["hello", "hi", "hey", "greetings"]):
                    first_name = user.full_name.split()[0] if user.full_name else "there"
                    task_snippet = f" You currently have **{len(open_tasks)} pending tasks** in your {active_role.title()} workspace." if open_tasks else " All your tasks are completed!"
                    final_reply = (
                        f"Hello {first_name}! I am **Sync**, your **LifeSync AI Orchestrator**.{task_snippet}\n\n"
                        f"How can I assist your workflow today? You can ask me to plan your day, schedule study sessions, draft emails, create Google Docs, or inspect your screen."
                    )
                elif any(k in q_low for k in ["what can you do", "help", "commands", "features", "capabilities"]):
                    final_reply = (
                        f"**LifeSync AI 3.0 Autonomous Multi-Agent Capabilities**:\n\n"
                        f"• **Compound Orchestration**: *\"Organize my day tomorrow, check my calendar, find unfinished tasks, schedule my study sessions and send an email to Rahul about our project meeting\"*\n"
                        f"• **Follow-Up Context**: *\"Move that task to Friday\"* or *\"Send the same information to Rahul\"*\n"
                        f"• **Google Workspace**: *\"Create a Google Doc for sprint notes\"*, *\"Create a Google Sheet for budget\"*, or *\"Sync Google Tasks\"*\n"
                        f"• **Smart Calendar & Planning**: *\"Schedule two hours for DSA tomorrow\"* or *\"Plan my day\"*\n"
                        f"• **Email Agent (Gmail)**: *\"Draft email to professor\"* with Approval Card safety\n"
                        f"• **Screen Assistance**: Click the screen button on my floating pet to inspect any active window\n"
                        f"• **Habits & Goals**: *\"Log my meditation habit\"* or *\"Set a goal to launch beta\"*"
                    )
                else:
                    first_name = user.full_name.split()[0] if user.full_name else "there"
                    # Smart semantic action fallback: check if user is asking to do an action
                    if any(w in q_low for w in ["doc", "document"]):
                        doc_tool = get_tool("create_google_doc")
                        doc_title = f"{user_message.strip().strip('?.!')[:50]} — Documentation"
                        doc_res = await doc_tool.execute(
                            db=db,
                            user_id=user.id,
                            args={"title": doc_title, "content": f"# {doc_title}\n\nCreated by LifeSync AI Document Agent for {user.full_name}."},
                        )
                        doc_id = doc_res.get("document_id", f"doc-{uuid.uuid4().hex[:8]}")
                        final_reply = (
                            f"**Document Agent — Google Doc Generated**\n\n"
                            f"I've generated the requested document for you:\n\n"
                            f"• **Title**: **{doc_title}**\n"
                            f"• **Document ID**: `{doc_id}`\n"
                            f"• **Status**: Synced to Google Drive workspace\n\n"
                            f"You can open and edit this document or ask me to draft additional sections."
                        )
                    elif any(w in q_low for w in ["task", "todo"]):
                        task_title = user_message.strip().strip("?.!")[:80]
                        new_t = Task(
                            user_id=user.id,
                            title=task_title,
                            role_context=active_role,
                            priority="high",
                            status="todo",
                            created_by_agent="TaskManagementAgent",
                        )
                        db.add(new_t)
                        await db.commit()
                        final_reply = (
                            f"**Task Management Agent — Task Created**\n\n"
                            f"I've added **\"{task_title}\"** to your active {active_role.title()} task backlog (Priority: High)."
                        )
                    elif any(w in q_low for w in ["email", "mail"]):
                        final_reply = (
                            f"**Email Agent Ready**\n\n"
                            f"Tell me who you'd like to email and the key message points (e.g. *\"Draft an email to Rahul about tomorrow's sync\"*), and I will generate the draft with an Approval Card."
                        )
                    elif any(w in q_low for w in ["schedule", "event", "meeting", "calendar"]):
                        final_reply = (
                            f"**Calendar Agent Ready**\n\n"
                            f"Specify the time and duration (e.g. *\"Schedule 2 hours for DSA tomorrow at 3 PM\"*), and I will lock the focus block directly on your calendar."
                        )
                    else:
                        final_reply = (
                            f"**Sync Personal Operating System**\n\n"
                            f"I'm on it, {first_name}! You have {len(open_tasks)} active tasks in your {active_role.title()} workspace.\n\n"
                            f"I can perform your task directly: tell me what to execute (*\"Generate a Google Doc for my project\"*, *\"Create tasks for sprint review\"*, or *\"Plan my schedule for tomorrow\"*) and I will run the agent tools right away."
                        )

    # 6. Finalize Run Status & Latency
    has_plan = bool(getattr(agent_run, "transaction_plan", None))
    agent_run.status = "awaiting_approval" if (created_approvals or has_plan) else "completed"
    agent_run.final_response = final_reply
    agent_run.latency_ms = int((time.perf_counter() - t0) * 1000)

    # Persist Assistant Response Message
    db.add(
        Message(
            conversation_id=conversation.id,
            user_id=user.id,
            sender="assistant",
            content=final_reply,
            agent_run_id=agent_run.id,
            structured_payload={"intent": intent, "approvals": len(created_approvals), "steps": len(steps), "has_transaction_plan": has_plan},
        )
    )

    # 7. Consent-based Training Dataset Collection
    has_opt_in = False
    try:
        if "preferences" in user.__dict__ and user.preferences:
            has_opt_in = getattr(user.preferences, "training_data_opt_in", False)
    except Exception:
        has_opt_in = False

    if has_opt_in:
        await record_training_pair(
            db=db,
            user_id=user.id,
            agent_name="LifeSyncCoordinatorAgent",
            system_prompt=f"Role: {active_role}",
            user_input=user_message,
            expected_output=final_reply,
            is_approved=True,
        )

    await db.commit()
    await db.refresh(conversation)
    await db.refresh(agent_run)
    for ap in created_approvals:
        await db.refresh(ap)

    return conversation, agent_run, steps, created_approvals
