from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, verify_password
from app.models.user import UserStatus
from app.repositories.audit_repository import AuditRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, TokenResponse


class AuthService:
    @staticmethod
    def login(db: Session, payload: LoginRequest, request: Request) -> TokenResponse:
        user = UserRepository.get_by_email(db, payload.email)
        is_valid_user = (
            user is not None
            and user.status == UserStatus.ACTIVE
            and verify_password(payload.password, user.password_hash)
        )

        AuditRepository.record_login(
            db,
            email=payload.email,
            success=is_valid_user,
            user_id=user.id if user else None,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        db.commit()

        if not is_valid_user or user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )

        token = create_access_token(
            subject=str(user.id),
            claims={"role": user.role.value},
        )
        return TokenResponse(access_token=token, user=user)
