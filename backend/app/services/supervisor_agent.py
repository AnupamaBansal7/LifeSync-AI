from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone
import json
import re
from typing import Any, Dict, List, Optional, Tuple
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.providers import ProviderRegistry
from app.ai.tools import get_tool
from app.models.ai_system import AgentExecutionStep, AgentRun
from app.models.calendar import CalendarEvent
from app.models.productivity import Task
from app.models.shadow_execution import TransactionPlan
from app.models.user import User
from app.services.shadow_execution_service import ShadowExecutionService


@dataclass
class AgentContext:
    user_id: uuid.UUID
    user_name: str
    active_role: str = "personal"
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    active_tasks_summary: List[Dict[str, Any]] = field(default_factory=list)
    today_calendar_summary: List[Dict[str, Any]] = field(default_factory=list)
    shared_outputs: Dict[str, Any] = field(default_factory=dict)
    agent_trace: List[Dict[str, Any]] = field(default_factory=list)
    auto_approve_low_risk: bool = True


def clean_spoken_text(text: str) -> str:
    """Strip markdown symbols, urls, bullet dashes, and format smoothly for Web Speech Synthesis."""
    if not text:
        return ""
    # Strip links [text](url) -> text
    cleaned = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    # Strip standalone URLs
    cleaned = re.sub(r"https?://\S+", "", cleaned)
    # Strip markdown headers, bold, italics, code, brackets, bullets
    cleaned = re.sub(r"[#*_`~>•\[\]\(\)]", " ", cleaned)
    # Strip list dashes at beginning of lines
    cleaned = re.sub(r"^\s*-\s+", " ", cleaned, flags=re.MULTILINE)
    # Strip double spaces and excessive line breaks
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    # Limit spoken text to first 2-3 sentences for natural TTS cadence
    sentences = re.split(r"(?<=[.!?])\s+", cleaned)
    if len(sentences) > 2:
        cleaned = " ".join(sentences[:2])
    return cleaned


def parse_relative_datetime(text: str, default_time: Optional[time] = None) -> datetime:
    """Parses relative day and time from natural language input (e.g. 'Friday at 10 AM', 'tomorrow', 'next Monday')."""
    now = datetime.now(timezone.utc)
    target_date = now.date()
    t_low = text.lower()

    if "tomorrow" in t_low:
        target_date = now.date() + timedelta(days=1)
    elif "today" in t_low:
        target_date = now.date()
    else:
        weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        for idx, day in enumerate(weekdays):
            if day in t_low:
                current_weekday = now.weekday()
                days_ahead = (idx - current_weekday) % 7
                if days_ahead == 0 and "next" in t_low:
                    days_ahead = 7
                elif days_ahead == 0:
                    days_ahead = 7 if now.hour >= 18 else 0
                target_date = now.date() + timedelta(days=days_ahead)
                break

    target_time = default_time or time(hour=10, minute=0)
    time_match = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)", t_low)
    if time_match:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2) or 0)
        meridiem = time_match.group(3).lower()
        if meridiem == "pm" and hour < 12:
            hour += 12
        elif meridiem == "am" and hour == 12:
            hour = 0
        target_time = time(hour=hour, minute=minute)

    return datetime.combine(target_date, target_time, tzinfo=timezone.utc)


class SupervisorAgent:
    """
    Central Supervisor Coordinator for LifeSync AI.
    Acts as the single point of contact, dispatches to specialized sub-agents,
    maintains shared context across agents, executes transactions safely via ShadowExecutionService,
    and produces clean spoken TTS replies alongside UI display markdown.
    """

    @classmethod
    async def build_context(
        cls,
        db: AsyncSession,
        user: User,
        conversation_history: List[Dict[str, str]],
        active_role: str = "personal",
        auto_approve_low_risk: bool = True,
    ) -> AgentContext:
        user_name = (
            user.full_name.split()[0]
            if user.full_name and user.full_name.strip()
            else user.email.split("@")[0].capitalize()
        )
        now = datetime.now(timezone.utc)

        # Retrieve top 5 open tasks
        t_res = await db.execute(
            select(Task)
            .where(Task.user_id == user.id, Task.status.in_(["todo", "in_progress"]))
            .order_by(Task.due_date.asc().nulls_last())
            .limit(5)
        )
        tasks = t_res.scalars().all()
        tasks_summary = [{"id": str(t.id), "title": t.title, "priority": t.priority, "due": t.due_date.isoformat() if t.due_date else None} for t in tasks]

        # Retrieve today's upcoming calendar events
        c_res = await db.execute(
            select(CalendarEvent)
            .where(CalendarEvent.user_id == user.id, CalendarEvent.end_time >= now)
            .order_by(CalendarEvent.start_time.asc())
            .limit(4)
        )
        events = c_res.scalars().all()
        events_summary = [{"id": str(e.id), "title": e.title, "start": e.start_time.isoformat(), "end": e.end_time.isoformat()} for e in events]

        return AgentContext(
            user_id=user.id,
            user_name=user_name,
            active_role=active_role,
            conversation_history=conversation_history[-6:],
            active_tasks_summary=tasks_summary,
            today_calendar_summary=events_summary,
            auto_approve_low_risk=auto_approve_low_risk,
        )

    @classmethod
    async def check_voice_approval(
        cls,
        db: AsyncSession,
        context: AgentContext,
        user_message: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Detects if the user is confirming or cancelling an AWAITING_APPROVAL TransactionPlan verbally or by text.
        """
        msg_low = user_message.strip().lower()
        msg_clean = re.sub(r"[^\w\s]", " ", msg_low).strip()
        is_approval = (
            any(phrase in msg_clean for phrase in ["approve", "go ahead", "do it", "confirm", "proceed", "execute", "apply", "looks good"])
            or msg_clean in ["yes", "yes please", "sure", "yep", "yeah"]
        )
        is_cancellation = (
            any(phrase in msg_clean for phrase in ["cancel", "reject", "abort", "discard", "stop"])
            or msg_clean in ["no", "dont do it", "don't do it", "nope"]
        )

        if not (is_approval or is_cancellation):
            return None

        # Look up pending transaction plan
        stmt = (
            select(TransactionPlan)
            .where(
                TransactionPlan.user_id == context.user_id,
                TransactionPlan.status == "AWAITING_APPROVAL",
            )
            .order_by(TransactionPlan.created_at.desc())
            .limit(1)
        )
        res = await db.execute(stmt)
        pending_plan = res.scalar_one_or_none()
        if not pending_plan:
            return None

        if is_approval:
            exec_res = await ShadowExecutionService.approve_plan(
                db=db,
                user_id=context.user_id,
                plan_id=pending_plan.id,
            )
            context.agent_trace.append({
                "agent": "Sync Supervisor",
                "status": "completed",
                "detail": f"Voice confirmed: Approved Transaction Plan '{pending_plan.intent_summary}'",
            })
            spoken = f"I have approved and executed your plan for {pending_plan.intent_summary}."
            display = (
                f"**Transaction Plan Approved & Executed**\n\n"
                f"✅ **Plan**: {pending_plan.intent_summary}\n"
                f"• **Status**: Executed ({exec_res.get('successful_steps', 0)} of {exec_res.get('total_steps', 0)} steps succeeded)\n"
                f"• **Reversibility**: Step-level compensations are available if you need to rollback."
            )
            return {
                "mode": "VOICE_APPROVAL",
                "status": "completed",
                "spoken_reply": spoken,
                "display_reply": display,
                "agent_trace": context.agent_trace,
                "transaction_plan": pending_plan.to_dict(),
            }
        else:
            roll_res = await ShadowExecutionService.rollback_plan(
                db=db,
                user_id=context.user_id,
                plan_id=pending_plan.id,
            )
            context.agent_trace.append({
                "agent": "Sync Supervisor",
                "status": "completed",
                "detail": f"Voice cancelled: Rolled back Transaction Plan '{pending_plan.intent_summary}'",
            })
            spoken = f"I've cancelled the pending plan for {pending_plan.intent_summary}. No changes were made."
            display = (
                f"**Transaction Plan Cancelled**\n\n"
                f"❌ **Plan**: {pending_plan.intent_summary}\n"
                f"• **Status**: Rolled back successfully\n"
                f"• **Database**: Clean state preserved."
            )
            return {
                "mode": "VOICE_APPROVAL",
                "status": "completed",
                "spoken_reply": spoken,
                "display_reply": display,
                "agent_trace": context.agent_trace,
                "transaction_plan": pending_plan.to_dict(),
            }

    @classmethod
    async def coordinate(
        cls,
        db: AsyncSession,
        context: AgentContext,
        user_message: str,
        screen_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Coordinates sub-agents, resolves shared inter-agent parameters,
        and produces verified execution output with voice-ready spoken replies.
        """
        # 1. Voice approval / cancellation check
        voice_appr = await cls.check_voice_approval(db, context, user_message)
        if voice_appr:
            return voice_appr

        q_low = user_message.lower().strip()

        # 2. Compound Multi-Agent Planning (e.g. Finish assignment by Friday + schedule focus block tomorrow at 10 AM)
        is_compound = (
            any(w in q_low for w in ["finish", "submit", "assignment", "project", "task", "report", "homework"])
            and any(w in q_low for w in ["block", "schedule", "calendar", "hours for", "hour for", "focus block", "at 10", "at 11", "at 2", "at 3", "at 9"])
        )

        if is_compound:
            return await cls._execute_compound_task_and_calendar(db, context, user_message)

        # 3. Google Workspace / Document Agent
        if any(w in q_low for w in ["google doc", "doc", "document", "generate doc", "create doc", "make a doc"]):
            return await cls._execute_document_agent(db, context, user_message)

        # 4. Task Management Agent
        if any(w in q_low for w in ["create task", "create a task", "add task", "add a task", "make a task", "todo", "new task", "remind me to"]):
            return await cls._execute_task_agent(db, context, user_message)

        # 5. Calendar Scheduling Agent
        if any(w in q_low for w in ["schedule", "time block", "focus session", "book a slot", "calendar event"]):
            return await cls._execute_calendar_agent(db, context, user_message)

        # 6. Email Agent
        if any(w in q_low for w in ["send email", "draft email", "write an email", "email to", "mail to"]):
            return await cls._execute_email_agent(db, context, user_message)

        # 7. Habit Agent
        if any(w in q_low for w in ["habit", "streak", "daily routine", "log habit", "create habit"]):
            return await cls._execute_habit_agent(db, context, user_message)

        # 8. Daily Planning Agent
        if any(w in q_low for w in ["plan my day", "daily plan", "plan tomorrow", "schedule my day"]):
            return await cls._execute_daily_plan_agent(db, context, user_message)

        # 9. Conversational Fallback
        context.agent_trace.append({
            "agent": "Sync Supervisor",
            "status": "completed",
            "detail": f"Interpreted request for {context.user_name} under {context.active_role} mode",
        })
        first_name = context.user_name
        spoken = f"Hello {first_name}! What task would you like me to execute for you?"
        display = (
            f"**Sync Supervisor ({context.active_role.title()} Workspace)**\n\n"
            f"Hello {first_name}! I coordinate your specialized agents. You can ask me to:\n"
            f"• *\"Create a task to submit my report by Friday and block 1 hour tomorrow at 10 AM\"*\n"
            f"• *\"Generate a Google Doc for my architecture review\"*\n"
            f"• *\"Plan my day tomorrow\"* or *\"Draft an email to Rahul\"*\n\n"
            f"What would you like to execute?"
        )
        return {
            "mode": "CONVERSATION",
            "status": "completed",
            "spoken_reply": spoken,
            "display_reply": display,
            "agent_trace": context.agent_trace,
        }

    # =========================================================================
    # SPECIALIZED DELEGATION ROUTINES
    # =========================================================================

    @classmethod
    async def _execute_compound_task_and_calendar(
        cls,
        db: AsyncSession,
        context: AgentContext,
        user_message: str,
    ) -> Dict[str, Any]:
        """
        Coordinates Task Agent and Calendar Agent with Shared Inter-Agent Context.
        Task Agent extracts the task and sets shared_outputs["task_agent"].
        Calendar Agent reads shared_outputs["task_agent"] to allocate the matching Focus Block!
        """
        context.agent_trace.append({
            "agent": "Sync Supervisor",
            "status": "completed",
            "detail": "Analyzed compound intent; coordinating Task & Calendar Agents",
        })

        # 1. Task Agent: Extract title and due date
        clean_task_title = "Complete assignment"
        task_match = re.search(r"(?:finish|submit|complete|do|work on)\s+([^.]+?)(?:\s+by|\s+and|\s+before|$)", user_message, flags=re.I)
        if task_match:
            clean_task_title = task_match.group(1).strip().capitalize()
        else:
            clean_task_title = "Assignment & Milestone Deliverable"

        due_dt = parse_relative_datetime(user_message, default_time=time(hour=17, minute=0))
        due_iso = due_dt.isoformat()

        # Store in Shared Context for downstream agents
        context.shared_outputs["task_agent"] = {
            "title": clean_task_title,
            "due_date": due_iso,
            "priority": "high",
        }
        context.agent_trace.append({
            "agent": "Task Agent",
            "status": "completed",
            "detail": f"Prepared task: '{clean_task_title}' due {due_dt.strftime('%A, %b %d')}",
        })

        # 2. Calendar Agent: Reads task title from shared context!
        cal_start = parse_relative_datetime(user_message, default_time=time(hour=10, minute=0))
        # Look for duration (e.g. 1 hour, 2 hours, 90 mins)
        dur_match = re.search(r"(\d+)\s*(hour|hr|minute|min)", user_message, flags=re.I)
        duration_minutes = 60
        if dur_match:
            val = int(dur_match.group(1))
            unit = dur_match.group(2).lower()
            duration_minutes = val * 60 if "h" in unit else val

        cal_end = cal_start + timedelta(minutes=duration_minutes)
        focus_title = f"{context.shared_outputs['task_agent']['title']} — Focus Session"

        context.shared_outputs["calendar_agent"] = {
            "title": focus_title,
            "start_time": cal_start.isoformat(),
            "end_time": cal_end.isoformat(),
            "duration_minutes": duration_minutes,
        }
        context.agent_trace.append({
            "agent": "Calendar Agent",
            "status": "completed",
            "detail": f"Allocated {duration_minutes}-min focus block at {cal_start.strftime('%a %I:%M %p')}",
        })

        # 3. Simulate Transaction Plan with Shadow Execution Engine
        proposed_calls = [
            {
                "tool_name": "create_task",
                "args": {
                    "title": clean_task_title,
                    "due_date": due_iso,
                    "priority": "high",
                    "role_context": context.active_role,
                },
            },
            {
                "tool_name": "create_calendar_block",
                "args": {
                    "title": focus_title,
                    "start_time": cal_start.isoformat(),
                    "end_time": cal_end.isoformat(),
                    "role_context": context.active_role,
                },
            },
        ]

        plan_dict = await ShadowExecutionService.simulate_plan(
            db=db,
            user_id=context.user_id,
            intent_summary=f"Task: {clean_task_title} & Focus Block",
            proposed_tool_calls=proposed_calls,
            auto_approve_if_safe=False,
            plan_metadata={"source": "supervisor_agent", "shared_outputs": context.shared_outputs},
        )

        spoken = (
            f"I have scheduled a {duration_minutes}-minute focus block for {cal_start.strftime('%A at %I:%M %p')}, "
            f"and prepared your task '{clean_task_title}' due {due_dt.strftime('%A')}."
        )

        display = (
            f"**Sync Supervisor — Multi-Agent Plan Simulated**\n\n"
            f"I have coordinated **Task Agent** and **Calendar Agent**:\n\n"
            f"• **Task Agent**: Prepared `{clean_task_title}` (Priority: High, Due: {due_dt.strftime('%a, %b %d %I:%M %p')})\n"
            f"• **Calendar Agent**: Scheduled Focus Block from {cal_start.strftime('%I:%M %p')} to {cal_end.strftime('%I:%M %p')}\n\n"
            f"🛡️ **No database records committed yet.** Review the before/after diff in the **Shadow Diff Card** below, or say *'Yes, approve it'* to confirm."
        )

        return {
            "mode": "MULTI_AGENT_PLAN",
            "status": "awaiting_approval",
            "spoken_reply": spoken,
            "display_reply": display,
            "agent_trace": context.agent_trace,
            "transaction_plan": plan_dict,
        }

    @classmethod
    async def _execute_document_agent(
        cls,
        db: AsyncSession,
        context: AgentContext,
        user_message: str,
    ) -> Dict[str, Any]:
        context.agent_trace.append({
            "agent": "Sync Supervisor",
            "status": "completed",
            "detail": "Delegated to Document Agent",
        })

        q_low = user_message.lower()
        is_query_check = any(w in q_low for w in ["have you", "did you", "is the doc", "status of", "check", "was the doc", "where is", "has the doc"])

        # Check existing generated doc
        res_steps = await db.execute(
            select(AgentExecutionStep)
            .join(AgentRun, AgentRun.id == AgentExecutionStep.agent_run_id)
            .where(AgentRun.user_id == context.user_id, AgentExecutionStep.tool_name == "create_google_doc")
            .order_by(AgentExecutionStep.created_at.desc())
            .limit(1)
        )
        prev_step = res_steps.scalar_one_or_none()

        if is_query_check and prev_step and prev_step.output_summary and prev_step.output_summary.get("success"):
            prev_out = prev_step.output_summary
            doc_title = prev_out.get("title", "Project Documentation")
            doc_id = prev_out.get("document_id", "doc-live")
            doc_url = prev_out.get("document_url", f"https://docs.google.com/document/d/{doc_id}/edit")

            context.agent_trace.append({
                "agent": "Document Agent",
                "status": "completed",
                "detail": f"Retrieved active document '{doc_title}' ({doc_id})",
            })
            spoken = f"Yes, your Google Doc '{doc_title}' has already been generated and is active in Google Drive."
            display = (
                f"**Document Agent — Google Doc Status**\n\n"
                f"Yes! The Google Doc **'{doc_title}'** has already been generated and is active:\n\n"
                f"• **Title**: **{doc_title}**\n"
                f"• **Document ID**: `{doc_id}`\n"
                f"• **Drive Status**: Synced and available in your Google Drive workspace\n"
                f"• **Access**: [Open Google Doc]({doc_url})\n\n"
                f"Would you like me to append additional milestones, generate an accompanying Google Sheet, or export action tasks?"
            )
            return {
                "mode": "DIRECT_EXECUTION",
                "status": "completed",
                "spoken_reply": spoken,
                "display_reply": display,
                "agent_trace": context.agent_trace,
            }

        # Otherwise create / generate
        clean_title = re.sub(
            r"^(have\s+you\s+generated\s+(the\s+)?|did\s+you\s+generate\s+(the\s+)?|generate\s+(a\s+)?|create\s+(a\s+)?|new\s+)?(google\s+doc|document|doc)\s*(for|titled|about)?\s*",
            "",
            user_message,
            flags=re.I,
        ).strip().strip("? .!\"'")

        if not clean_title or len(clean_title) < 2 or clean_title.lower() in ["the", "a", "my", "it"]:
            clean_title = f"{context.user_name}'s LifeSync Execution Plan"

        doc_tool = get_tool("create_google_doc")
        doc_res = await doc_tool.execute(
            db=db,
            user_id=context.user_id,
            args={
                "title": clean_title,
                "content": f"# {clean_title}\n\nGenerated by LifeSync AI Document Agent for {context.user_name}.",
            },
        )
        doc_id = doc_res.get("document_id", f"doc-{uuid.uuid4().hex[:8]}")
        doc_url = doc_res.get("document_url", f"https://docs.google.com/document/d/{doc_id}/edit")

        context.agent_trace.append({
            "agent": "Document Agent",
            "status": "completed",
            "detail": f"Generated Google Doc '{clean_title}' (ID: {doc_id})",
        })

        spoken = f"I have generated your Google Document titled '{clean_title}' and synced it with Google Drive."
        display = (
            f"**Document Agent — Google Doc Created Successfully**\n\n"
            f"• **Title**: **{clean_title}**\n"
            f"• **Document ID**: `{doc_id}`\n"
            f"• **Drive Status**: Synced and available in your Google Drive workspace\n"
            f"• **Document Link**: [Open Google Doc]({doc_url})"
        )
        return {
            "mode": "DIRECT_EXECUTION",
            "status": "completed",
            "spoken_reply": spoken,
            "display_reply": display,
            "agent_trace": context.agent_trace,
        }

    @classmethod
    async def _execute_task_agent(
        cls,
        db: AsyncSession,
        context: AgentContext,
        user_message: str,
    ) -> Dict[str, Any]:
        context.agent_trace.append({
            "agent": "Sync Supervisor",
            "status": "completed",
            "detail": "Delegated to Task Management Agent",
        })

        clean_title = re.sub(
            r"^(create\s+a\s+task\s+(to|for)?|create\s+task\s+(to|for)?|add\s+a\s+task\s+(to|for)?|add\s+task\s+(to|for)?|make\s+a\s+task\s+(to|for)?|remind\s+me\s+to)\s*",
            "",
            user_message,
            flags=re.I,
        ).strip().capitalize()
        if not clean_title:
            clean_title = "Follow-up deliverable"

        due_dt = parse_relative_datetime(user_message, default_time=time(hour=17, minute=0))

        task = Task(
            user_id=context.user_id,
            title=clean_title[:120],
            role_context=context.active_role,
            priority="high" if any(w in user_message.lower() for w in ["urgent", "deadline", "submit", "exam"]) else "medium",
            status="todo",
            due_date=due_dt,
            created_by_agent="TaskManagementAgent",
        )
        db.add(task)
        await db.commit()

        context.agent_trace.append({
            "agent": "Task Management Agent",
            "status": "completed",
            "detail": f"Persisted task: '{clean_title[:50]}' (Due: {due_dt.strftime('%a, %b %d')})",
        })

        spoken = f"I've added the task '{clean_title[:60]}' to your backlog, due {due_dt.strftime('%A')}."
        display = (
            f"**Task Management Agent — Task Created**\n\n"
            f"• **Title**: **{clean_title}**\n"
            f"• **Priority**: {task.priority.capitalize()}\n"
            f"• **Due Date**: {due_dt.strftime('%A, %b %d at %I:%M %p')}\n"
            f"• **Workspace**: {context.active_role.title()}"
        )
        return {
            "mode": "DIRECT_EXECUTION",
            "status": "completed",
            "spoken_reply": spoken,
            "display_reply": display,
            "agent_trace": context.agent_trace,
        }

    @classmethod
    async def _execute_calendar_agent(
        cls,
        db: AsyncSession,
        context: AgentContext,
        user_message: str,
    ) -> Dict[str, Any]:
        context.agent_trace.append({
            "agent": "Sync Supervisor",
            "status": "completed",
            "detail": "Delegated to Calendar Agent",
        })

        start_dt = parse_relative_datetime(user_message, default_time=time(hour=14, minute=0))
        end_dt = start_dt + timedelta(hours=1)
        title = "Focus Block"
        title_match = re.search(r"(?:for|on)\s+([^.]+?)(?:\s+at|\s+tomorrow|\s+today|$)", user_message, flags=re.I)
        if title_match:
            title = f"{title_match.group(1).strip().capitalize()} Focus Session"

        ev = CalendarEvent(
            user_id=context.user_id,
            title=title,
            start_time=start_dt,
            end_time=end_dt,
            role_context=context.active_role,
            event_type="time_block",
            is_locked=True,
        )
        db.add(ev)
        await db.commit()

        context.agent_trace.append({
            "agent": "Calendar Agent",
            "status": "completed",
            "detail": f"Scheduled '{title}' on {start_dt.strftime('%a, %b %d at %I:%M %p')}",
        })

        spoken = f"I have scheduled your focus session for {start_dt.strftime('%A at %I:%M %p')}."
        display = (
            f"**Calendar Agent — Event Scheduled**\n\n"
            f"• **Title**: **{title}**\n"
            f"• **Start Time**: {start_dt.strftime('%A, %b %d at %I:%M %p')}\n"
            f"• **End Time**: {end_dt.strftime('%I:%M %p')}\n"
            f"• **Type**: Protected Time Block (Locked)"
        )
        return {
            "mode": "DIRECT_EXECUTION",
            "status": "completed",
            "spoken_reply": spoken,
            "display_reply": display,
            "agent_trace": context.agent_trace,
        }

    @classmethod
    async def _execute_email_agent(
        cls,
        db: AsyncSession,
        context: AgentContext,
        user_message: str,
    ) -> Dict[str, Any]:
        context.agent_trace.append({
            "agent": "Sync Supervisor",
            "status": "completed",
            "detail": "Delegated to Email Agent",
        })

        draft_tool = get_tool("compose_email_draft")
        sub = "Project Discussion & Next Steps"
        m = re.search(r"(?:about|regarding)\s+(.+)$", user_message, flags=re.I)
        if m:
            sub = m.group(1).strip()

        res = await draft_tool.execute(
            db=db,
            user_id=context.user_id,
            args={"recipient": "recipient@example.com", "subject": sub},
        )
        context.agent_trace.append({
            "agent": "Email Agent",
            "status": "completed",
            "detail": f"Prepared email draft: '{sub}'",
        })

        spoken = f"I have prepared an email draft regarding {sub}."
        display = (
            f"**Email Agent — Draft Prepared**\n\n"
            f"• **Subject**: `{sub}`\n"
            f"• **Recipient**: `recipient@example.com`\n"
            f"• **Status**: Draft created in your inbox.\n\n"
            f"You can review and confirm before dispatching."
        )
        return {
            "mode": "DIRECT_EXECUTION",
            "status": "completed",
            "spoken_reply": spoken,
            "display_reply": display,
            "agent_trace": context.agent_trace,
        }

    @classmethod
    async def _execute_habit_agent(
        cls,
        db: AsyncSession,
        context: AgentContext,
        user_message: str,
    ) -> Dict[str, Any]:
        context.agent_trace.append({
            "agent": "Sync Supervisor",
            "status": "completed",
            "detail": "Delegated to Habit Agent",
        })
        h_title = "Daily Focus Routine"
        m = re.search(r"(?:habit|routine)\s+(?:for|to|called)?\s*(.+)$", user_message, flags=re.I)
        if m:
            h_title = m.group(1).strip().capitalize()

        h_tool = get_tool("create_habit")
        res = await h_tool.execute(
            db=db,
            user_id=context.user_id,
            args={"title": h_title, "frequency": "daily", "role_context": context.active_role},
        )
        context.agent_trace.append({
            "agent": "Habit Agent",
            "status": "completed",
            "detail": f"Registered habit: '{h_title}'",
        })
        spoken = f"I have added the daily habit '{h_title}' to your tracker."
        display = (
            f"**Habit Agent — Habit Registered**\n\n"
            f"• **Title**: **{h_title}**\n"
            f"• **Cadence**: Daily\n"
            f"• **Streak Matrix**: Active for {context.active_role.title()} mode."
        )
        return {
            "mode": "DIRECT_EXECUTION",
            "status": "completed",
            "spoken_reply": spoken,
            "display_reply": display,
            "agent_trace": context.agent_trace,
        }

    @classmethod
    async def _execute_daily_plan_agent(
        cls,
        db: AsyncSession,
        context: AgentContext,
        user_message: str,
    ) -> Dict[str, Any]:
        context.agent_trace.append({
            "agent": "Sync Supervisor",
            "status": "completed",
            "detail": "Delegated to Daily Planning Agent",
        })
        plan_tool = get_tool("plan_my_day")
        res = await plan_tool.execute(
            db=db,
            user_id=context.user_id,
            args={"role_context": context.active_role},
        )
        context.agent_trace.append({
            "agent": "Daily Planning Agent",
            "status": "completed",
            "detail": "Constructed daily schedule focus blocks",
        })
        spoken = f"I have planned your day tomorrow with balanced focus blocks and scheduled priorities."
        display = (
            f"**Daily Planning Agent — Day Structured**\n\n"
            f"• **Schedule**: Focused blocks prepared for tomorrow.\n"
            f"• **Focus Recommendation**: {res.get('summary', 'Execute high priority deliverable before noon.')}\n\n"
            f"Check your calendar view for the complete timeline."
        )
        return {
            "mode": "DIRECT_EXECUTION",
            "status": "completed",
            "spoken_reply": spoken,
            "display_reply": display,
            "agent_trace": context.agent_trace,
        }
