from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import Role

DEFAULT_ROLES = [
    {
        "slug": "student",
        "name": "Student & Researcher",
        "description": "Coursework, exam preparation, technical projects, coding practice, and academic deadlines.",
        "default_modules": ["tasks", "goals", "habits", "calendar", "memory", "analytics"],
    },
    {
        "slug": "professional",
        "name": "Software / Industry Professional",
        "description": "Engineering sprints, meetings, deep-work blocks, career milestones, and deliverables.",
        "default_modules": ["tasks", "goals", "calendar", "memory", "analytics"],
    },
    {
        "slug": "creator",
        "name": "Digital Creator & Educator",
        "description": "Content calendars, script pipelines, video production, digital products, and audience growth.",
        "default_modules": ["tasks", "goals", "habits", "calendar", "memory", "analytics"],
    },
    {
        "slug": "entrepreneur",
        "name": "Founder & Builder",
        "description": "Product roadmaps, launches, client operations, strategic OKRs, and weekly reviews.",
        "default_modules": ["tasks", "goals", "calendar", "memory", "analytics"],
    },
    {
        "slug": "personal",
        "name": "Personal Life & Wellness",
        "description": "Daily routines, health habits, personal finance check-ins, reading, and life admin.",
        "default_modules": ["tasks", "goals", "habits", "calendar", "memory"],
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