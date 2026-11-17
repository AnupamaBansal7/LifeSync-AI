import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.db.session import get_db
from app.models.user import User, UserModule, UserPreference, UserProfile
from app.schemas.auth import (
    AuthSessionResponse,
    RefreshTokenRequest,
    TokenResponse,
    UserAuthSummary,
    UserLoginRequest,
    UserRegisterRequest,
)
from app.schemas.user import UserMeResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])

DEFAULT_CORE_MODULES = ["tasks", "goals", "habits", "calendar", "memory", "analytics"]


def _build_token_pair(user_id: uuid.UUID) -> TokenResponse:
    subject = str(user_id)
    return TokenResponse(
        access_token=create_access_token(subject),
        refresh_token=create_refresh_token(subject),
        expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )


@router.post("/register", response_model=AuthSessionResponse, status_code=status.HTTP_201_CREATED)
async def register_user(payload: UserRegisterRequest, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == payload.email.lower()))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    user = User(
        email=payload.email.lower(),
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name.strip(),
        is_active=True,
        is_onboarded=False,
    )
    db.add(user)
    await db.flush()

    db.add(UserProfile(user_id=user.id))
    db.add(UserPreference(user_id=user.id))
    for mod_key in DEFAULT_CORE_MODULES:
        db.add(UserModule(user_id=user.id, module_key=mod_key, is_enabled=True))

    await db.commit()
    await db.refresh(user)

    return AuthSessionResponse(
        user=UserAuthSummary.model_validate(user),
        tokens=_build_token_pair(user.id),
    )


@router.post("/login", response_model=AuthSessionResponse)
async def login_user(payload: UserLoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email.lower()))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled.",
        )

    return AuthSessionResponse(
        user=UserAuthSummary.model_validate(user),
        tokens=_build_token_pair(user.id),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(payload: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    try:
        decoded = decode_token(payload.refresh_token)
        if decoded.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token.")
        user_id = uuid.UUID(decoded["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token.")

    result = await db.execute(select(User).where(User.id == user_id, User.is_active.is_(True)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found.")

    return _build_token_pair(user.id)


@router.get("/me", response_model=UserMeResponse)
async def get_authenticated_user(current_user: User = Depends(get_current_user)):
    return current_user