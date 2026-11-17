from enum import Enum
from typing import Dict, List, Set


class RoleSlug(str, Enum):
    PERSONAL = "personal"
    STUDENT = "student"
    TEACHER = "teacher"
    MANAGER = "manager"
    FREELANCER = "freelancer"
    ENTREPRENEUR = "entrepreneur"
    WORKING_PROFESSIONAL = "working_professional"


class ModuleKey(str, Enum):
    DASHBOARD = "dashboard"
    TASKS = "tasks"
    GOALS = "goals"
    HABITS = "habits"
    CALENDAR = "calendar"
    ASSISTANT = "assistant"
    AGENTS = "agents"
    MEMORY = "memory"
    INSIGHTS = "insights"
    AUTOMATIONS = "automations"


class ToolRiskLevel(str, Enum):
    READ_ONLY = "read_only"           # Safe to execute automatically
    LOW_IMPACT_WRITE = "low_write"    # Auto-executable if user enabled auto-mode, else approval
    HIGH_IMPACT_WRITE = "high_write"  # Always requires explicit user approval


ROLE_DEFAULT_AGENTS: Dict[str, List[str]] = {
    RoleSlug.PERSONAL.value: ["chat_agent", "task_agent", "planning_agent", "goal_agent", "habit_agent", "memory_agent", "review_agent"],
    RoleSlug.STUDENT.value: ["study_planning_agent", "exam_prep_agent", "assignment_agent", "placement_prep_agent", "skill_dev_agent"],
    RoleSlug.TEACHER.value: ["lesson_planning_agent", "evaluation_assistant_agent", "academic_schedule_agent"],
    RoleSlug.MANAGER.value: ["project_coordination_agent", "meeting_management_agent", "strategic_planning_agent"],
    RoleSlug.FREELANCER.value: ["client_management_agent", "project_delivery_agent", "invoice_reminder_agent", "time_tracking_agent"],
    RoleSlug.ENTREPRENEUR.value: ["strategic_planning_agent", "project_coordination_agent", "client_management_agent"],
    RoleSlug.WORKING_PROFESSIONAL.value: ["project_coordination_agent", "meeting_management_agent", "skill_dev_agent"],
}


def get_authorized_agents_for_roles(role_slugs: List[str]) -> Set[str]:
    """Compute union of common agents + role-specific agents authorized for a user's active roles."""
    authorized: Set[str] = set(ROLE_DEFAULT_AGENTS[RoleSlug.PERSONAL.value])
    for slug in role_slugs:
        if slug in ROLE_DEFAULT_AGENTS:
            authorized.update(ROLE_DEFAULT_AGENTS[slug])
    return authorized