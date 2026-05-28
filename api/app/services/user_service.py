from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.user import User, UserStatus
from app.repositories.audit_repository import AuditRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate


class UserService:
    @staticmethod
    def create_user(db: Session, payload: UserCreate, actor: User) -> User:
        existing_user = UserRepository.get_by_email(db, payload.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email is already registered",
            )

        user = UserRepository.create_user(
            db,
            payload,
            get_password_hash(payload.password),
        )
        db.flush()
        AuditRepository.record_activity(
            db,
            actor_user_id=actor.id,
            action="admin.user.create",
            entity_type="user",
            entity_id=str(user.id),
            metadata_json={"email": user.email, "role": user.role.value},
        )
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def list_users(
        db: Session,
        *,
        skip: int = 0,
        limit: int = 50,
        search: str | None = None,
    ) -> list[User]:
        return UserRepository.list_users(
            db,
            skip=skip,
            limit=min(limit, 100),
            search=search,
        )

    @staticmethod
    def reset_password(
        db: Session,
        *,
        user_id: int,
        new_password: str,
        actor: User,
    ) -> User:
        user = UserRepository.get_by_id(db, user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        UserRepository.update_password(db, user, get_password_hash(new_password))
        AuditRepository.record_activity(
            db,
            actor_user_id=actor.id,
            action="admin.user.reset_password",
            entity_type="user",
            entity_id=str(user.id),
        )
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def update_status(
        db: Session,
        *,
        user_id: int,
        user_status: UserStatus,
        actor: User,
    ) -> User:
        user = UserRepository.get_by_id(db, user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        UserRepository.update_status(db, user, user_status)
        AuditRepository.record_activity(
            db,
            actor_user_id=actor.id,
            action="admin.user.update_status",
            entity_type="user",
            entity_id=str(user.id),
            metadata_json={"status": user_status.value},
        )
        db.commit()
        db.refresh(user)
        return user
