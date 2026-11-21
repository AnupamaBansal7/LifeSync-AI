from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import Role

DEFAULT_ROLES = [
    {
        "slug": "personal",
        "name": "Personal Life & Wellness",
        "description": "Daily routines, health & wellness habits, personal finance check-ins, reading, and life admin.",
        "default_modules": ["tasks", "goals", "habits", "calendar", "memory"],
    },
    {
        "slug": "student",
        "name": "Student & Researcher",
        "description": "Coursework, exam preparation, academic deadlines, technical projects, study schedules, and subject mastery.",
        "default_modules": ["tasks", "goals", "habits", "calendar", "memory", "analytics"],
    },
    {
        "slug": "professional",
        "name": "Working Professional",
        "description": "Engineering sprints, workplace deliverables, deep-work time blocks, meetings, and career milestones.",
        "default_modules": ["tasks", "goals", "calendar", "memory", "analytics"],
    },
    {
        "slug": "entrepreneur",
        "name": "Entrepreneur & Founder",
        "description": "Product roadmaps, business OKRs, investor updates, strategic launches, and weekly execution reviews.",
        "default_modules": ["tasks", "goals", "calendar", "memory", "analytics"],
    },
    {
        "slug": "manager",
        "name": "Manager & Team Lead",
        "description": "Team project tracking, 1-on-1s, delegation, operational delivery, and cross-functional coordination.",
        "default_modules": ["tasks", "goals", "calendar", "memory", "analytics"],
    },
    {
        "slug": "freelancer",
        "name": "Freelancer & Consultant",
        "description": "Client management, milestone delivery, hourly tracking, proposal pipelines, and workload balancing.",
        "default_modules": ["tasks", "goals", "habits", "calendar", "memory", "analytics"],
    },
    {
        "slug": "teacher",
        "name": "Teacher & Educator",
        "description": "Curriculum planning, lecture schedules, grading deadlines, student feedback, and academic management.",
        "default_modules": ["tasks", "goals", "calendar", "memory"],
    },
    {
        "slug": "homemaker",
        "name": "Homemaker & Household Manager",
        "description": "Family schedules, household chores, meal routines, shopping lists, and wellness habits.",
        "default_modules": ["tasks", "habits", "calendar", "memory"],
    },
    {
        "slug": "custom",
        "name": "Custom Role",
        "description": "User-defined identity and specialized domain responsibilities with customizable AI agent prompts.",
        "default_modules": ["tasks", "goals", "habits", "calendar", "memory", "analytics"],
    },
]


async def seed_default_roles(db: AsyncSession) -> None:
    result = await db.execute(select(Role.slug))
    existing_slugs = set(result.scalars().all())

    created = False
    for role_data in DEFAULT_ROLES:
        if role_data["slug"] not in existing_slugs:
            db.add(Role(**role_data))
            created = True

    if created:
        await db.commit()
