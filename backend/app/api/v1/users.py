from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.ai_system import Memory
from app.models.productivity import Goal
from app.models.user import Role, User, UserModule, UserPreference, UserProfile, UserRole
from app.schemas.user import (
    OnboardingCompleteRequest,
    RoleOut,
    UserMeResponse,
    UserModuleOut,
    UserModuleToggleRequest,
    UserPreferenceOut,
    UserPreferenceUpdate,
    UserProfileOut,
    UserProfileUpdate,
    UserRoleAssignmentInput,
    UserRoleOut,
)

router = APIRouter(prefix="/users", tags=["Users, Roles & Onboarding"])


async def _reload_user(db: AsyncSession, user_id) -> User:
    stmt = (
        select(User)
        .where(User.id == user_id)
        .options(
            selectinload(User.profile),
            selectinload(User.preferences),
            selectinload(User.roles).selectinload(UserRole.role),
            selectinload(User.modules),
        )
    )
    res = await db.execute(stmt)
    return res.scalar_one()


@router.get("/roles/catalog", response_model=List[RoleOut])
async def list_available_roles(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Role).order_by(Role.name))
    return result.scalars().all()


@router.post("/onboarding", response_model=UserMeResponse)
async def complete_onboarding(
    payload: OnboardingCompleteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    requested_slugs = [r.role_slug.lower() for r in payload.roles]
    roles_res = await db.execute(select(Role).where(Role.slug.in_(requested_slugs)))
    role_map = {r.slug: r for r in roles_res.scalars().all()}

    missing = set(requested_slugs) - set(role_map.keys())
    if missing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown role slugs: {', '.join(sorted(missing))}",
        )

    # Replace existing role assignments cleanly
    await db.execute(delete(UserRole).where(UserRole.user_id == current_user.id))

    has_primary = any(r.is_primary for r in payload.roles)
    primary_slug = requested_slugs[0]
    for idx, role_input in enumerate(payload.roles):
        slug = role_input.role_slug.lower()
        is_primary = role_input.is_primary if has_primary else (idx == 0)
        if is_primary:
            primary_slug = slug
        db.add(
            UserRole(
                user_id=current_user.id,
                role_id=role_map[slug].id,
                is_primary=is_primary,
                context_metadata=role_input.context_metadata,
            )
        )

    # Update profile
    profile = current_user.profile or UserProfile(user_id=current_user.id)
    profile.headline = payload.headline
    profile.organization = payload.organization
    profile.focus_areas = payload.focus_areas
    profile.work_hours_start = payload.work_hours_start
    profile.work_hours_end = payload.work_hours_end
    db.add(profile)

    # Update preferences
    prefs = current_user.preferences or UserPreference(user_id=current_user.id)
    prefs.timezone = payload.timezone
    prefs.training_data_opt_in = payload.training_data_opt_in
    db.add(prefs)

    # Sync enabled modules
    enabled_set = set(payload.enabled_modules)
    existing_modules = {m.module_key: m for m in current_user.modules}
    all_keys = enabled_set | set(existing_modules.keys())
    for key in all_keys:
        if key in existing_modules:
            existing_modules[key].is_enabled = key in enabled_set
        else:
            db.add(UserModule(user_id=current_user.id, module_key=key, is_enabled=key in enabled_set))

    # Seed initial goals & long-term memory anchor from onboarding
    for goal_title in payload.initial_goals:
        clean_title = goal_title.strip()
        if clean_title:
            db.add(
                Goal(
                    user_id=current_user.id,
                    title=clean_title,
                    role_context=primary_slug,
                    horizon="short_term",
                )
            )

    role_names = ", ".join(role_map[s].name for s in requested_slugs)
    db.add(
        Memory(
            user_id=current_user.id,
            category="responsibility",
            role_context=primary_slug,
            content=f"User operates across roles: {role_names}. Focus areas: {', '.join(payload.focus_areas) or 'general productivity'}. Active work hours: {payload.work_hours_start}-{payload.work_hours_end} ({payload.timezone}).",
            importance_score=0.9,
            source="onboarding",
            consent_for_training=payload.training_data_opt_in,
        )
    )

    current_user.is_onboarded = True
    await db.commit()
    return await _reload_user(db, current_user.id)


@router.put("/roles", response_model=List[UserRoleOut])
async def update_user_roles(
    roles: List[UserRoleAssignmentInput],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not roles:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one role is required.")

    requested_slugs = [r.role_slug.lower() for r in roles]
    roles_res = await db.execute(select(Role).where(Role.slug.in_(requested_slugs)))
    role_map = {r.slug: r for r in roles_res.scalars().all()}

    missing = set(requested_slugs) - set(role_map.keys())
    if missing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown role slugs: {', '.join(sorted(missing))}",
        )

    await db.execute(delete(UserRole).where(UserRole.user_id == current_user.id))
    has_primary = any(r.is_primary for r in roles)
    for idx, role_input in enumerate(roles):
        slug = role_input.role_slug.lower()
        db.add(
            UserRole(
                user_id=current_user.id,
                role_id=role_map[slug].id,
                is_primary=role_input.is_primary if has_primary else (idx == 0),
                context_metadata=role_input.context_metadata,
            )
        )

    await db.commit()
    reloaded = await _reload_user(db, current_user.id)
    return reloaded.roles


@router.patch("/profile", response_model=UserProfileOut)
async def update_profile(
    payload: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = current_user.profile or UserProfile(user_id=current_user.id)
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return profile


@router.patch("/preferences", response_model=UserPreferenceOut)
async def update_preferences(
    payload: UserPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    prefs = current_user.preferences or UserPreference(user_id=current_user.id)
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(prefs, field, value)
    db.add(prefs)
    await db.commit()
    await db.refresh(prefs)
    return prefs


@router.patch("/modules/{module_key}", response_model=UserModuleOut)
async def toggle_module(
    module_key: str,
    payload: UserModuleToggleRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(UserModule).where(UserModule.user_id == current_user.id, UserModule.module_key == module_key)
    )
    mod = res.scalar_one_or_none()
    if mod is None:
        mod = UserModule(
            user_id=current_user.id,
            module_key=module_key,
            is_enabled=payload.is_enabled,
            config=payload.config or {},
        )
    else:
        mod.is_enabled = payload.is_enabled
        if payload.config is not None:
            mod.config = payload.config

    db.add(mod)
    await db.commit()
    await db.refresh(mod)
    return mod