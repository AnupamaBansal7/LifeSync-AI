from typing import List
from app.ai.agents.base import BaseAgent


# --- STUDENT ---
class StudyPlanningAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "student_study_planner"

    @property
    def display_name(self) -> str:
        return "Study Planning Agent"

    @property
    def description(self) -> str:
        return "Builds structured revision timetables, pomodoro study sessions, and subject mastery schedules."

    @property
    def category(self) -> str:
        return "role_specific"

    @property
    def supported_roles(self) -> List[str]:
        return ["student"]

    @property
    def allowed_tools(self) -> List[str]:
        return ["create_task", "create_calendar_block"]


class ExamPrepAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "student_exam_prep"

    @property
    def display_name(self) -> str:
        return "Exam Preparation Agent"

    @property
    def description(self) -> str:
        return "Analyzes upcoming exams, calculates remaining revision days, and creates spaced-repetition schedules."

    @property
    def category(self) -> str:
        return "role_specific"

    @property
    def supported_roles(self) -> List[str]:
        return ["student"]

    @property
    def allowed_tools(self) -> List[str]:
        return ["create_task", "create_calendar_block", "create_goal"]


# --- WORKING PROFESSIONAL ---
class WorkPlanningAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "professional_work_planner"

    @property
    def display_name(self) -> str:
        return "Work Planning Agent"

    @property
    def description(self) -> str:
        return "Organizes daily sprint commitments, syncs with working hours, and shields deep work blocks from meeting fatigue."

    @property
    def category(self) -> str:
        return "role_specific"

    @property
    def supported_roles(self) -> List[str]:
        return ["professional", "working_professional"]

    @property
    def allowed_tools(self) -> List[str]:
        return ["create_task", "create_calendar_block"]


class CareerDevelopmentAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "professional_career_dev"

    @property
    def display_name(self) -> str:
        return "Career Development Agent"

    @property
    def description(self) -> str:
        return "Maps career milestones, promotion targets, skill acquisitions, and strategic networking goals."

    @property
    def category(self) -> str:
        return "role_specific"

    @property
    def supported_roles(self) -> List[str]:
        return ["professional", "working_professional"]

    @property
    def allowed_tools(self) -> List[str]:
        return ["create_goal", "create_task"]


# --- ENTREPRENEUR ---
class BusinessPlanningAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "entrepreneur_business_planner"

    @property
    def display_name(self) -> str:
        return "Business Planning Agent"

    @property
    def description(self) -> str:
        return "Translates startup vision and revenue targets into quarterly OKRs, product launches, and operational roadmaps."

    @property
    def category(self) -> str:
        return "role_specific"

    @property
    def supported_roles(self) -> List[str]:
        return ["entrepreneur"]

    @property
    def allowed_tools(self) -> List[str]:
        return ["create_goal", "create_task", "create_calendar_block"]


# --- MANAGER ---
class TeamPlanningAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "manager_team_planner"

    @property
    def display_name(self) -> str:
        return "Team & Project Planning Agent"

    @property
    def description(self) -> str:
        return "Assists in workload delegation, 1-on-1 meeting preparation, delivery risk tracking, and team objectives."

    @property
    def category(self) -> str:
        return "role_specific"

    @property
    def supported_roles(self) -> List[str]:
        return ["manager"]

    @property
    def allowed_tools(self) -> List[str]:
        return ["create_task", "create_calendar_block"]


# --- FREELANCER ---
class FreelancerWorkloadAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "freelancer_workload_planner"

    @property
    def display_name(self) -> str:
        return "Client & Workload Agent"

    @property
    def description(self) -> str:
        return "Balances multiple client deliverables, tracks project deadlines, and guards against over-commitment."

    @property
    def category(self) -> str:
        return "role_specific"

    @property
    def supported_roles(self) -> List[str]:
        return ["freelancer"]

    @property
    def allowed_tools(self) -> List[str]:
        return ["create_task", "create_goal", "create_calendar_block"]


# --- TEACHER ---
class LessonPlanningAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "teacher_lesson_planner"

    @property
    def display_name(self) -> str:
        return "Lesson & Curriculum Agent"

    @property
    def description(self) -> str:
        return "Organizes curriculum modules, lesson preparations, assignment grading schedules, and student progress milestones."

    @property
    def category(self) -> str:
        return "role_specific"

    @property
    def supported_roles(self) -> List[str]:
        return ["teacher"]

    @property
    def allowed_tools(self) -> List[str]:
        return ["create_task", "create_calendar_block"]


# --- HOMEMAKER ---
class HouseholdPlanningAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "homemaker_routine_planner"

    @property
    def display_name(self) -> str:
        return "Household & Routine Agent"

    @property
    def description(self) -> str:
        return "Manages household operations, meal planning, family schedules, grocery routines, and personal wellness."

    @property
    def category(self) -> str:
        return "role_specific"

    @property
    def supported_roles(self) -> List[str]:
        return ["homemaker"]

    @property
    def allowed_tools(self) -> List[str]:
        return ["create_task", "create_habit", "create_calendar_block"]


# --- CUSTOM ROLE ---
class CustomRoleAgent(BaseAgent):
    def __init__(self, role_slug: str = "custom", role_name: str = "Custom Role"):
        self._slug = role_slug
        self._role_name = role_name

    @property
    def name(self) -> str:
        return f"custom_{self._slug}_agent"

    @property
    def display_name(self) -> str:
        return f"{self._role_name} Assistant"

    @property
    def description(self) -> str:
        return f"Tailored AI assistance and priority optimization for {self._role_name}."

    @property
    def category(self) -> str:
        return "role_specific"

    @property
    def supported_roles(self) -> List[str]:
        return [self._slug, "custom"]

    @property
    def allowed_tools(self) -> List[str]:
        return ["create_task", "create_goal", "create_calendar_block"]
