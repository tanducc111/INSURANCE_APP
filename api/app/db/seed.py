from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_password_hash
from app.db.session import SessionLocal
from app.models.user import UserRole, UserStatus
from app.repositories.audit_repository import AuditRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate


def seed_admin(db: Session) -> None:
    existing_admin = UserRepository.get_by_email(db, settings.SEED_ADMIN_EMAIL)
    if existing_admin:
        existing_admin.password_hash = get_password_hash(settings.SEED_ADMIN_PASSWORD)
        existing_admin.full_name = settings.SEED_ADMIN_FULL_NAME
        existing_admin.role = UserRole.ADMIN
        existing_admin.status = UserStatus.ACTIVE
        AuditRepository.record_activity(
            db,
            actor_user_id=existing_admin.id,
            action="seed.admin.update",
            entity_type="user",
            entity_id=str(existing_admin.id),
            metadata_json={"email": existing_admin.email},
        )
        db.commit()
        return

    payload = UserCreate(
        email=settings.SEED_ADMIN_EMAIL,
        password=settings.SEED_ADMIN_PASSWORD,
        full_name=settings.SEED_ADMIN_FULL_NAME,
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
    )
    admin = UserRepository.create_user(
        db,
        payload,
        get_password_hash(payload.password),
    )
    db.flush()
    AuditRepository.record_activity(
        db,
        actor_user_id=admin.id,
        action="seed.admin.create",
        entity_type="user",
        entity_id=str(admin.id),
        metadata_json={"email": admin.email},
    )
    db.commit()


def main() -> None:
    db = SessionLocal()
    try:
        seed_admin(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
