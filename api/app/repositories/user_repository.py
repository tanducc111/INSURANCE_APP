from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.models.user import User, UserStatus
from app.schemas.user import UserCreate


class UserRepository:
    @staticmethod
    def get_by_id(db: Session, user_id: int) -> User | None:
        return db.scalar(select(User).where(User.id == user_id))

    @staticmethod
    def get_by_email(db: Session, email: str) -> User | None:
        return db.scalar(select(User).where(User.email == email.lower()))

    @staticmethod
    def list_users(
        db: Session,
        *,
        skip: int = 0,
        limit: int = 50,
        search: str | None = None,
    ) -> list[User]:
        query: Select[tuple[User]] = select(User).order_by(User.created_at.desc())
        if search:
            pattern = f"%{search.lower()}%"
            query = query.where(
                func.lower(User.email).like(pattern)
                | func.lower(User.full_name).like(pattern)
            )
        return list(db.scalars(query.offset(skip).limit(limit)))

    @staticmethod
    def create_user(db: Session, payload: UserCreate, password_hash: str) -> User:
        user = User(
            email=payload.email.lower(),
            password_hash=password_hash,
            full_name=payload.full_name,
            role=payload.role,
            status=payload.status,
        )
        db.add(user)
        return user

    @staticmethod
    def update_password(db: Session, user: User, password_hash: str) -> User:
        user.password_hash = password_hash
        db.add(user)
        return user

    @staticmethod
    def update_status(db: Session, user: User, status: UserStatus) -> User:
        user.status = status
        db.add(user)
        return user
