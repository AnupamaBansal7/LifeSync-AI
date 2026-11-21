from typing import Dict, List, Optional
from app.ai.agents.base import BaseAgent
from app.ai.agents.common import (
    AutomationAgent,
    CalendarAgent,
    ComputerUseAgent,
    DocumentAgent,
    EmailAgent,
    GoalManagementAgent,
    HabitAgent,
    MemoryAgent,
    PersonalAssistantAgent,
    PlanningAgent,
    ResearchAgent,
    ReviewReflectionAgent,
    ScreenAssistanceAgent,
    TaskManagementAgent,
    WorkspaceAgent,
)

from app.ai.agents.role_specific import (
    BusinessPlanningAgent,
    CareerDevelopmentAgent,
    CustomRoleAgent,
    ExamPrepAgent,
    FreelancerWorkloadAgent,
    HouseholdPlanningAgent,
    LessonPlanningAgent,
    StudyPlanningAgent,
    TeamPlanningAgent,
    WorkPlanningAgent,
)

COMMON_AGENTS: List[BaseAgent] = [
    PersonalAssistantAgent(),
    TaskManagementAgent(),
    EmailAgent(),
    PlanningAgent(),
    GoalManagementAgent(),
    HabitAgent(),
    CalendarAgent(),
    WorkspaceAgent(),
    DocumentAgent(),
    AutomationAgent(),
    MemoryAgent(),
    ResearchAgent(),
    ReviewReflectionAgent(),
    ScreenAssistanceAgent(),
    ComputerUseAgent(),
]


ROLE_SPECIFIC_AGENTS: List[BaseAgent] = [
    StudyPlanningAgent(),
    ExamPrepAgent(),
    WorkPlanningAgent(),
    CareerDevelopmentAgent(),
    BusinessPlanningAgent(),
    TeamPlanningAgent(),
    FreelancerWorkloadAgent(),
    LessonPlanningAgent(),
    HouseholdPlanningAgent(),
]

ALL_AGENTS_MAP: Dict[str, BaseAgent] = {a.name: a for a in COMMON_AGENTS + ROLE_SPECIFIC_AGENTS}


def get_agent_by_name(name: str) -> Optional[BaseAgent]:
    return ALL_AGENTS_MAP.get(name)


def list_agents_for_roles(active_roles: List[str]) -> List[BaseAgent]:
    """Return all common agents plus role-specific agents matching any active role."""
    roles_set = set(r.lower() for r in active_roles)
    matched = list(COMMON_AGENTS)

    for agent in ROLE_SPECIFIC_AGENTS:
        if any(r in roles_set for r in agent.supported_roles):
            matched.append(agent)

    return matched
