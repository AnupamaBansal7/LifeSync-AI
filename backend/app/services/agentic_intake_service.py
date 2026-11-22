import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.calendar import CalendarEvent
from app.models.intake import IntakeSession
from app.models.productivity import Task
from app.services.shadow_execution_service import ShadowExecutionService


class AgenticIntakeService:
    @staticmethod
    def detect_domain(prompt: str) -> str:
        p = prompt.lower()
        if any(w in p for w in ["goal", "achieve", "aspire", "master", "learn", "okr", "target", "resolution"]):
            return "GOAL_PLANNING"
        if any(w in p for w in ["project", "build", "develop", "launch", "redesign", "migrate", "overhaul", "architect"]):
            return "PROJECT_BREAKDOWN"
        if any(w in p for w in ["habit", "routine", "streak", "daily", "workout", "fitness", "meditate", "morning"]):
            return "HABIT_DESIGN"
        if any(w in p for w in ["task", "todo", "to-do", "backlog", "chore", "checklist", "errand"]):
            return "TASK_CAPTURE"
        return "GENERAL"

    @staticmethod
    async def get_user_schedule_density(db: AsyncSession, user_id: uuid.UUID) -> Dict[str, Any]:
        """Inspects current active tasks count and upcoming calendar density to personalize options."""
        now = datetime.now(timezone.utc)
        week_end = now + timedelta(days=7)

        # Active tasks count
        t_res = await db.execute(
            select(func.count(Task.id)).where(Task.user_id == user_id, Task.status != "completed")
        )
        active_tasks = t_res.scalar() or 0

        # Calendar events in the next 7 days
        c_res = await db.execute(
            select(func.count(CalendarEvent.id)).where(
                CalendarEvent.user_id == user_id,
                CalendarEvent.start_time >= now,
                CalendarEvent.start_time <= week_end,
            )
        )
        upcoming_events = c_res.scalar() or 0

        if upcoming_events >= 8 or active_tasks >= 10:
            density = "high"
            density_hint = f"You have {active_tasks} pending tasks and {upcoming_events} calendar commitments this week."
        elif upcoming_events >= 3 or active_tasks >= 4:
            density = "moderate"
            density_hint = f"Your schedule is balanced with {upcoming_events} upcoming events and {active_tasks} open tasks."
        else:
            density = "low"
            density_hint = "Your schedule has plenty of open focus capacity right now."

        return {
            "active_tasks": active_tasks,
            "upcoming_events": upcoming_events,
            "density": density,
            "density_hint": density_hint,
        }

    @classmethod
    async def start_or_continue_intake(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        prompt: str,
        session_id: Optional[uuid.UUID] = None,
        role_context: str = "personal",
    ) -> Dict[str, Any]:
        """Starts a new intake session or resumes an existing one, returning a ClarificationCard or TransactionPlan."""
        # Check for active existing session
        session = None
        if session_id:
            res = await db.execute(
                select(IntakeSession).where(IntakeSession.id == session_id, IntakeSession.user_id == user_id)
            )
            session = res.scalar_one_or_none()

        if not session:
            # Check if there is an existing in-progress session for this user
            res = await db.execute(
                select(IntakeSession)
                .where(IntakeSession.user_id == user_id, IntakeSession.status == "GATHERING_INFO")
                .order_by(IntakeSession.created_at.desc())
                .limit(1)
            )
            existing = res.scalar_one_or_none()
            if existing and prompt.lower() in ["continue", "next", "resume"]:
                session = existing
            else:
                domain = cls.detect_domain(prompt)
                session = IntakeSession(
                    user_id=user_id,
                    initial_prompt=prompt.strip(),
                    domain=domain,
                    status="GATHERING_INFO",
                    collected_context_json={"initial_prompt": prompt, "role_context": role_context},
                    current_step=1,
                    max_steps=3 if domain in ["HABIT_DESIGN", "TASK_CAPTURE"] else 4,
                )
                db.add(session)
                await db.commit()
                await db.refresh(session)

        # Generate question for current step
        density_info = await cls.get_user_schedule_density(db, user_id)
        card = cls._generate_card_for_step(session, density_info, role_context)
        return {
            "status": "CLARIFICATION_REQUIRED",
            "session_id": str(session.id),
            "clarification_card": card,
            "reply": card["question"],
        }

    @classmethod
    async def respond_to_intake(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        session_id: uuid.UUID,
        selected_options: List[str],
        custom_text: Optional[str] = None,
        skip_and_generate: bool = False,
        role_context: str = "personal",
    ) -> Dict[str, Any]:
        """Processes the user's answer, advances the intake step, or compiles the blueprint into a simulated plan."""
        res = await db.execute(
            select(IntakeSession).where(IntakeSession.id == session_id, IntakeSession.user_id == user_id)
        )
        session = res.scalar_one_or_none()
        if not session:
            raise ValueError(f"Intake session '{session_id}' not found or access denied.")

        if session.status in ["COMPLETED", "CANCELLED"]:
            return {
                "status": session.status,
                "session_id": str(session.id),
                "reply": f"This intake session is already {session.status.lower()}.",
                "transaction_plan": None,
            }

        # Record answers into collected_context_json
        context = dict(session.collected_context_json or {})
        step_key = f"step_{session.current_step}"
        context[step_key] = {
            "selected_options": selected_options,
            "custom_text": custom_text,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        }
        session.collected_context_json = context

        # Check completion condition
        if skip_and_generate or session.current_step >= session.max_steps:
            session.status = "READY_TO_SIMULATE"
            return await cls._compile_and_simulate_blueprint(db, user_id, session, role_context)

        # Advance step
        session.current_step += 1
        await db.commit()
        await db.refresh(session)

        density_info = await cls.get_user_schedule_density(db, user_id)
        card = cls._generate_card_for_step(session, density_info, role_context)
        return {
            "status": "CLARIFICATION_REQUIRED",
            "session_id": str(session.id),
            "clarification_card": card,
            "reply": card["question"],
        }

    @classmethod
    async def cancel_intake(cls, db: AsyncSession, user_id: uuid.UUID, session_id: uuid.UUID) -> Dict[str, Any]:
        """Cancels an active intake session."""
        res = await db.execute(
            select(IntakeSession).where(IntakeSession.id == session_id, IntakeSession.user_id == user_id)
        )
        session = res.scalar_one_or_none()
        if not session:
            raise ValueError(f"Intake session '{session_id}' not found.")
        session.status = "CANCELLED"
        await db.commit()
        return {"status": "CANCELLED", "session_id": str(session.id), "message": "Intake session cancelled."}

    @classmethod
    def _generate_card_for_step(
        cls, session: IntakeSession, density_info: Dict[str, Any], role_context: str
    ) -> Dict[str, Any]:
        step = session.current_step
        domain = session.domain
        prompt = session.initial_prompt
        density = density_info.get("density", "moderate")
        density_hint = density_info.get("density_hint", "")

        # Default options and questions per domain & step
        if domain == "GOAL_PLANNING":
            if step == 1:
                return {
                    "session_id": str(session.id),
                    "step": 1,
                    "estimated_total_steps": session.max_steps,
                    "domain": domain,
                    "question": f"Awesome! What target timeframe best fits your goal: '{prompt}'?",
                    "selection_mode": "single",
                    "options": [
                        {"id": "opt-2w", "label": "2-Week Rapid Sprint", "description": "High-intensity burst to prove momentum", "value": "2_weeks"},
                        {"id": "opt-1m", "label": "1-Month Structured Goal", "description": "Balanced, milestone-driven pacing", "value": "1_month"},
                        {"id": "opt-1q", "label": "Quarterly Milestone (3 Months)", "description": "Comprehensive habit & skill development", "value": "3_months"},
                        {"id": "opt-fl", "label": "Flexible / Long-term", "description": "Ongoing progression without hard deadlines", "value": "flexible"},
                    ],
                    "allow_custom_input": True,
                    "can_skip_and_generate": True,
                }
            elif step == 2:
                intensity_rec = "15-30 min/day" if density == "high" else "45-60 min/day"
                return {
                    "session_id": str(session.id),
                    "step": 2,
                    "estimated_total_steps": session.max_steps,
                    "domain": domain,
                    "question": f"{density_hint} How much time would you like to dedicate each day?",
                    "selection_mode": "single",
                    "options": [
                        {"id": "int-micro", "label": "Micro-Habits (15-20 min/day)", "description": "Low cognitive load, effortless consistency", "value": "15_min"},
                        {"id": "int-standard", "label": f"Deep Work ({intensity_rec})", "description": "Dedicated focus blocks to build real mastery", "value": "45_min"},
                        {"id": "int-intensive", "label": "Intensive (90+ min/day)", "description": "Rapid acceleration and deep immersion", "value": "90_min"},
                        {"id": "int-weekend", "label": "Weekend Sprints", "description": "Preserve weekdays and cluster on weekends", "value": "weekend_only"},
                    ],
                    "allow_custom_input": True,
                    "can_skip_and_generate": True,
                }
            else:
                return {
                    "session_id": str(session.id),
                    "step": 3,
                    "estimated_total_steps": session.max_steps,
                    "domain": domain,
                    "question": "Which supporting areas should I include in your blueprint?",
                    "selection_mode": "multi",
                    "options": [
                        {"id": "inc-tasks", "label": "Breakdown into Sequential Tasks", "description": "Specific deliverables ordered by priority", "value": "tasks"},
                        {"id": "inc-habits", "label": "Daily Consistency Habit", "description": "Track streaks and daily completion check-ins", "value": "habit"},
                        {"id": "inc-calendar", "label": "Calendar Focus Blocks", "description": "Schedule protected time slots on your calendar", "value": "calendar"},
                        {"id": "inc-milestones", "label": "3-Stage Milestones", "description": "Foundation → Core Build → Polish & Launch", "value": "milestones"},
                    ],
                    "allow_custom_input": True,
                    "can_skip_and_generate": True,
                }

        elif domain == "PROJECT_BREAKDOWN":
            if step == 1:
                return {
                    "session_id": str(session.id),
                    "step": 1,
                    "estimated_total_steps": session.max_steps,
                    "domain": domain,
                    "question": f"Let's architect your project: '{prompt}'. What is the primary milestone horizon?",
                    "selection_mode": "single",
                    "options": [
                        {"id": "p-mvp", "label": "MVP / Prototype (7-10 Days)", "description": "Focus strictly on the core functional slice", "value": "mvp_7d"},
                        {"id": "p-v1", "label": "Production Release (3-4 Weeks)", "description": "Full end-to-end architecture, tests, and polish", "value": "prod_4w"},
                        {"id": "p-enterprise", "label": "Enterprise / Capstone (2 Months)", "description": "Scalable design, docs, and multi-stage rollout", "value": "capstone_2m"},
                    ],
                    "allow_custom_input": True,
                    "can_skip_and_generate": True,
                }
            elif step == 2:
                return {
                    "session_id": str(session.id),
                    "step": 2,
                    "estimated_total_steps": session.max_steps,
                    "domain": domain,
                    "question": "What engineering workstreams should we structure for this project?",
                    "selection_mode": "multi",
                    "options": [
                        {"id": "ws-arch", "label": "System Design & Schemas", "description": "Database models, API contracts, and architecture diagrams", "value": "architecture"},
                        {"id": "ws-backend", "label": "Backend & Tool Calling Engine", "description": "Services, endpoints, background workers, and business logic", "value": "backend"},
                        {"id": "ws-frontend", "label": "Frontend & Interactive UI", "description": "Components, state management, animations, and voice inputs", "value": "frontend"},
                        {"id": "ws-testing", "label": "Verification & Integration Tests", "description": "Automated unit test suite, smoke tests, and linting", "value": "testing"},
                    ],
                    "allow_custom_input": True,
                    "can_skip_and_generate": True,
                }
            else:
                return {
                    "session_id": str(session.id),
                    "step": 3,
                    "estimated_total_steps": session.max_steps,
                    "domain": domain,
                    "question": f"{density_hint} How would you like me to block your calendar for deep execution?",
                    "selection_mode": "single",
                    "options": [
                        {"id": "cal-morning", "label": "Morning Deep Focus (09:00 - 10:30)", "description": "Tackle complex coding before other obligations", "value": "morning_focus"},
                        {"id": "cal-afternoon", "label": "Afternoon Sprint (14:30 - 16:00)", "description": "Implementation blocks post-lunch", "value": "afternoon_focus"},
                        {"id": "cal-async", "label": "No Calendar Blocks (Tasks Only)", "description": "Keep schedule open and execute flexibly", "value": "tasks_only"},
                    ],
                    "allow_custom_input": True,
                    "can_skip_and_generate": True,
                }

        # Generic / Habit / Task domain fallback
        return {
            "session_id": str(session.id),
            "step": step,
            "estimated_total_steps": session.max_steps,
            "domain": domain,
            "question": f"How would you prefer to pace '{prompt}'?",
            "selection_mode": "single",
            "options": [
                {"id": "g-high", "label": "Immediate Priority (Next 3 Days)", "description": "Front-load tasks to achieve fast results", "value": "high_priority"},
                {"id": "g-balanced", "label": "Standard Cadence (Next 2 Weeks)", "description": "Balanced daily execution", "value": "balanced"},
                {"id": "g-routine", "label": "Daily Routine Check-in", "description": "Establish a consistent repeating habit", "value": "routine"},
            ],
            "allow_custom_input": True,
            "can_skip_and_generate": True,
        }

    @classmethod
    async def _compile_and_simulate_blueprint(
        cls, db: AsyncSession, user_id: uuid.UUID, session: IntakeSession, role_context: str
    ) -> Dict[str, Any]:
        """Compiles the collected intake context into a Personal Jira Blueprint and simulates it with ShadowExecutionService."""
        context = session.collected_context_json or {}
        prompt = session.initial_prompt
        domain = session.domain
        now = datetime.now(timezone.utc)

        # 1. Determine timeline & intensity
        s1 = context.get("step_1", {}).get("selected_options", [])
        s2 = context.get("step_2", {}).get("selected_options", [])

        timeframe_days = 14
        if any("2w" in x or "mvp" in x for x in s1):
            timeframe_days = 14
        elif any("1m" in x or "prod" in x for x in s1):
            timeframe_days = 30
        elif any("1q" in x or "capstone" in x for x in s1):
            timeframe_days = 90
        elif any("3d" in x or "high" in x for x in s1):
            timeframe_days = 3

        target_date_str = (now.date() + timedelta(days=timeframe_days)).isoformat()

        # 2. Build Goal (Epic)
        goal_title = prompt.strip().capitalize()
        if len(goal_title) > 80:
            goal_title = goal_title[:77] + "..."

        milestones = [
            f"Stage 1: Foundation & Setup for {goal_title[:30]}",
            f"Stage 2: Core Execution & Implementation",
            f"Stage 3: Verification, Polish & Launch",
        ]
        goal_args = {
            "title": goal_title,
            "description": f"AI-generated blueprint from intake prompt: '{prompt}'",
            "horizon": "short_term" if timeframe_days <= 30 else "long_term",
            "role_context": role_context,
            "category": "Career" if role_context == "professional" else "Personal Growth",
            "target_date": target_date_str,
            "milestones": milestones,
        }

        # 3. Build concrete prioritized tasks (3 - 5 actionable tasks)
        clean_name = goal_title.replace("Goal:", "").replace("Project:", "").strip()
        task_specs = [
            {
                "title": f"Define requirements and setup workspace for {clean_name[:40]}",
                "priority": "high",
                "estimated_minutes": 45,
                "due_offset_days": 2,
            },
            {
                "title": f"Implement core milestone 1 deliverables for {clean_name[:40]}",
                "priority": "high",
                "estimated_minutes": 60,
                "due_offset_days": max(4, timeframe_days // 3),
            },
            {
                "title": f"Execute deep sprint on {clean_name[:40]}",
                "priority": "medium",
                "estimated_minutes": 60,
                "due_offset_days": max(7, (timeframe_days * 2) // 3),
            },
            {
                "title": f"Conduct review, testing, and retrospective on {clean_name[:40]}",
                "priority": "medium",
                "estimated_minutes": 45,
                "due_offset_days": timeframe_days,
            },
        ]

        tasks = []
        for spec in task_specs:
            due_iso = (now + timedelta(days=spec["due_offset_days"])).replace(hour=18, minute=0, second=0).isoformat()
            tasks.append({
                "title": spec["title"],
                "priority": spec["priority"],
                "role_context": role_context,
                "estimated_minutes": spec["estimated_minutes"],
                "due_date": due_iso,
            })

        # 4. Build supporting habit
        habit_args = {
            "title": f"Daily Focus: {clean_name[:35]}",
            "description": f"Dedicated practice block for '{clean_name}'",
            "role_context": role_context,
            "frequency": "daily",
            "target_days_per_week": 5,
            "reminder_time": "09:00",
        }

        # 5. Build calendar focus block
        block_start = (now + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
        block_end = block_start + timedelta(minutes=60)
        cal_args = {
            "title": f"Deep Focus: {clean_name[:35]}",
            "start_time": block_start.isoformat(),
            "end_time": block_end.isoformat(),
            "duration_minutes": 60,
            "role_context": role_context,
            "event_type": "time_block",
        }

        # Assemble tool calls
        proposed_calls = [
            {"tool_name": "create_goal", "args": goal_args},
            *[{"tool_name": "create_task", "args": t} for t in tasks],
            {"tool_name": "create_habit", "args": habit_args},
            {"tool_name": "create_calendar_block", "args": cal_args},
        ]

        # Simulate through ShadowExecutionService (NO mutations yet!)
        plan_dict = await ShadowExecutionService.simulate_plan(
            db=db,
            user_id=user_id,
            intent_summary=f"Personal Blueprint: {goal_title}",
            proposed_tool_calls=proposed_calls,
            auto_approve_if_safe=False,
            plan_metadata={
                "intake_session_id": str(session.id),
                "domain": domain,
                "timeframe_days": timeframe_days,
            },
        )

        # Update session status
        session.status = "COMPLETED"
        session.resulting_plan_id = uuid.UUID(plan_dict["id"])
        await db.commit()

        summary_reply = (
            f"🎯 **Blueprint Compiled & Simulated!**\n\n"
            f"I have architected a cohesive execution plan for **{goal_title}**:\n"
            f"• **1 Goal/Epic**: Targeted for {target_date_str} with 3 milestones\n"
            f"• **{len(tasks)} Tasks**: Structured across your {timeframe_days}-day horizon\n"
            f"• **1 Habit**: Daily focus habit (5 days/week)\n"
            f"• **1 Calendar Focus Block**: Tomorrow at 09:00 AM\n\n"
            f"🛡️ **No database records have been modified yet.** Review the diff below to selectively approve or apply the blueprint."
        )

        return {
            "status": "COMPLETED",
            "session_id": str(session.id),
            "reply": summary_reply,
            "transaction_plan": plan_dict,
        }
