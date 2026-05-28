from typing import Any

from sqlalchemy.orm import Session

from app.models.audit import ActivityLog, LoginHistory


class AuditRepository:
    @staticmethod
    def record_login(
        db: Session,
        *,
        email: str,
        success: bool,
        user_id: int | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> LoginHistory:
        entry = LoginHistory(
            user_id=user_id,
            email=email.lower(),
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
        )
        db.add(entry)
        return entry

    @staticmethod
    def record_activity(
        db: Session,
        *,
        action: str,
        entity_type: str,
        actor_user_id: int | None = None,
        entity_id: str | None = None,
        metadata_json: dict[str, Any] | None = None,
    ) -> ActivityLog:
        entry = ActivityLog(
            actor_user_id=actor_user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            metadata_json=metadata_json,
        )
        db.add(entry)
        return entry
