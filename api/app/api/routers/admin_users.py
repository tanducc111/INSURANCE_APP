from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.auth import require_roles
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.user import (
    PasswordResetRequest,
    UserCreate,
    UserRead,
    UserStatusUpdate,
)
from app.services.user_service import UserService

router = APIRouter(prefix="/admin/users", tags=["admin-users"])


@router.post("", response_model=UserRead, status_code=201)
async def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles(UserRole.ADMIN)),
) -> User:
    return UserService.create_user(db, payload, current_admin)


@router.get("", response_model=list[UserRead])
async def list_users(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    search: str | None = Query(default=None, max_length=255),
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles(UserRole.ADMIN)),
) -> list[User]:
    _ = current_admin
    return UserService.list_users(db, skip=skip, limit=limit, search=search)


@router.patch("/{user_id}/reset-password", response_model=UserRead)
async def reset_user_password(
    user_id: int,
    payload: PasswordResetRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles(UserRole.ADMIN)),
) -> User:
    return UserService.reset_password(
        db,
        user_id=user_id,
        new_password=payload.new_password,
        actor=current_admin,
    )


@router.patch("/{user_id}/status", response_model=UserRead)
async def update_user_status(
    user_id: int,
    payload: UserStatusUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles(UserRole.ADMIN)),
) -> User:
    return UserService.update_status(
        db,
        user_id=user_id,
        user_status=payload.status,
        actor=current_admin,
    )
