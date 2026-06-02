from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.claim import Claim, ClaimIncidentType, ClaimPriority, ClaimStatus
from app.models.user import User, UserRole
from app.repositories.audit_repository import AuditRepository
from app.repositories.claim_repository import ClaimAttachmentRepository, ClaimRepository
from app.repositories.customer_management_repository import (
    AssignmentRepository,
    CustomerRepository,
    EmployeeRepository,
)
from app.repositories.subscription_repository import SubscriptionRepository
from app.schemas.claim import (
    ClaimAssignmentUpdate,
    ClaimCreate,
    ClaimReviewNoteUpdate,
    ClaimStatusUpdate,
)
from app.utils.file_storage import (
    remove_stored_upload,
    store_uploads,
    validate_uploads,
)


ALLOWED_ATTACHMENT_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "application/pdf": ".pdf",
}


def _get_customer_for_user(db: Session, user: User):
    customer = CustomerRepository.get_by_user_id(db, user.id)
    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy hồ sơ khách hàng",
        )
    return customer


def _get_employee_for_user(db: Session, user: User):
    employee = EmployeeRepository.get_by_user_id(db, user.id)
    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy hồ sơ nhân viên",
        )
    return employee


def _ensure_employee_can_access_claim(db: Session, user: User, claim: Claim):
    employee = _get_employee_for_user(db, user)
    active_assignment = AssignmentRepository.get_active_for_customer(
        db,
        claim.customer_id,
    )
    if active_assignment is None or active_assignment.employee_id != employee.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Khách hàng của hồ sơ này chưa được phân công cho nhân viên hiện tại",
        )
    return employee


def _ensure_actor_can_view_claim(db: Session, user: User, claim: Claim) -> None:
    if user.role == UserRole.ADMIN:
        return
    if user.role == UserRole.CUSTOMER:
        customer = _get_customer_for_user(db, user)
        if claim.customer_id == customer.id:
            return
    if user.role == UserRole.EMPLOYEE:
        _ensure_employee_can_access_claim(db, user, claim)
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Bạn không có quyền xem chứng từ của hồ sơ này",
    )


class ClaimService:
    @staticmethod
    def create_customer_claim(
        db: Session,
        *,
        payload: ClaimCreate,
        actor: User,
    ) -> Claim:
        customer = _get_customer_for_user(db, actor)
        subscription = SubscriptionRepository.get_by_id(db, payload.subscription_id)
        if subscription is None or subscription.customer_id != customer.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy hợp đồng bảo hiểm",
            )

        assignment = AssignmentRepository.get_active_for_customer(db, customer.id)
        assigned_employee_id = assignment.employee_id if assignment else None
        claim = ClaimRepository.create_claim(
            db,
            customer_id=customer.id,
            assigned_employee_id=assigned_employee_id,
            payload=payload,
        )
        AuditRepository.record_activity(
            db,
            actor_user_id=actor.id,
            action="customer.claim.create",
            entity_type="claim",
            entity_id=str(claim.id),
            metadata_json={"subscription_id": claim.subscription_id},
        )
        db.commit()
        db.refresh(claim)
        return claim

    @staticmethod
    def list_customer_claims(
        db: Session,
        *,
        actor: User,
        skip: int = 0,
        limit: int = 50,
        status_filter: ClaimStatus | None = None,
        incident_type: ClaimIncidentType | None = None,
        priority: ClaimPriority | None = None,
    ) -> list[Claim]:
        customer = _get_customer_for_user(db, actor)
        return ClaimRepository.list_claims(
            db,
            customer_id=customer.id,
            skip=skip,
            limit=min(limit, 100),
            status_filter=status_filter,
            incident_type=incident_type,
            priority=priority,
        )

    @staticmethod
    def get_customer_claim(db: Session, *, claim_id: int, actor: User) -> Claim:
        customer = _get_customer_for_user(db, actor)
        claim = ClaimRepository.get_by_id(db, claim_id)
        if claim is None or claim.customer_id != customer.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy hồ sơ bồi thường",
            )
        return claim

    @staticmethod
    def list_employee_claims(
        db: Session,
        *,
        actor: User,
        skip: int = 0,
        limit: int = 50,
        search: str | None = None,
        status_filter: ClaimStatus | None = None,
        incident_type: ClaimIncidentType | None = None,
        priority: ClaimPriority | None = None,
    ) -> list[Claim]:
        employee = _get_employee_for_user(db, actor)
        assignments = AssignmentRepository.list_active_for_employee(
            db,
            employee.id,
            limit=100,
        )
        return ClaimRepository.list_claims(
            db,
            customer_ids=[assignment.customer_id for assignment in assignments],
            skip=skip,
            limit=min(limit, 100),
            search=search,
            status_filter=status_filter,
            incident_type=incident_type,
            priority=priority,
        )

    @staticmethod
    def get_employee_claim(db: Session, *, claim_id: int, actor: User) -> Claim:
        claim = ClaimRepository.get_by_id(db, claim_id)
        if claim is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy hồ sơ bồi thường",
            )
        _ensure_employee_can_access_claim(db, actor, claim)
        return claim

    @staticmethod
    def update_employee_claim_status(
        db: Session,
        *,
        claim_id: int,
        payload: ClaimStatusUpdate,
        actor: User,
    ) -> Claim:
        claim = ClaimService.get_employee_claim(db, claim_id=claim_id, actor=actor)
        employee = _ensure_employee_can_access_claim(db, actor, claim)
        claim.status = payload.status
        if claim.assigned_employee_id is None:
            claim.assigned_employee_id = employee.id
        AuditRepository.record_activity(
            db,
            actor_user_id=actor.id,
            action="employee.claim.update_status",
            entity_type="claim",
            entity_id=str(claim.id),
            metadata_json={"status": claim.status.value},
        )
        db.commit()
        db.refresh(claim)
        return claim

    @staticmethod
    def add_employee_review_note(
        db: Session,
        *,
        claim_id: int,
        payload: ClaimReviewNoteUpdate,
        actor: User,
    ) -> Claim:
        claim = ClaimService.get_employee_claim(db, claim_id=claim_id, actor=actor)
        employee = _ensure_employee_can_access_claim(db, actor, claim)
        claim.review_note = payload.review_note
        if claim.assigned_employee_id is None:
            claim.assigned_employee_id = employee.id
        AuditRepository.record_activity(
            db,
            actor_user_id=actor.id,
            action="employee.claim.review_note",
            entity_type="claim",
            entity_id=str(claim.id),
        )
        db.commit()
        db.refresh(claim)
        return claim

    @staticmethod
    def list_admin_claims(
        db: Session,
        *,
        skip: int = 0,
        limit: int = 50,
        search: str | None = None,
        status_filter: ClaimStatus | None = None,
        incident_type: ClaimIncidentType | None = None,
        priority: ClaimPriority | None = None,
    ) -> list[Claim]:
        return ClaimRepository.list_claims(
            db,
            skip=skip,
            limit=min(limit, 100),
            search=search,
            status_filter=status_filter,
            incident_type=incident_type,
            priority=priority,
        )

    @staticmethod
    def get_admin_claim(db: Session, *, claim_id: int) -> Claim:
        claim = ClaimRepository.get_by_id(db, claim_id)
        if claim is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy hồ sơ bồi thường",
            )
        return claim

    @staticmethod
    def assign_claim(
        db: Session,
        *,
        claim_id: int,
        payload: ClaimAssignmentUpdate,
        actor: User,
    ) -> Claim:
        claim = ClaimService.get_admin_claim(db, claim_id=claim_id)
        if payload.assigned_employee_id is not None:
            employee = EmployeeRepository.get_by_id(db, payload.assigned_employee_id)
            if employee is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Không tìm thấy nhân viên",
                )
        claim.assigned_employee_id = payload.assigned_employee_id
        AuditRepository.record_activity(
            db,
            actor_user_id=actor.id,
            action="admin.claim.assign",
            entity_type="claim",
            entity_id=str(claim.id),
            metadata_json={"assigned_employee_id": payload.assigned_employee_id},
        )
        db.commit()
        db.refresh(claim)
        return claim

    @staticmethod
    def update_admin_claim_status(
        db: Session,
        *,
        claim_id: int,
        payload: ClaimStatusUpdate,
        actor: User,
    ) -> Claim:
        claim = ClaimService.get_admin_claim(db, claim_id=claim_id)
        claim.status = payload.status
        AuditRepository.record_activity(
            db,
            actor_user_id=actor.id,
            action="admin.claim.update_status",
            entity_type="claim",
            entity_id=str(claim.id),
            metadata_json={"status": claim.status.value},
        )
        db.commit()
        db.refresh(claim)
        return claim

    @staticmethod
    async def upload_customer_attachments(
        db: Session,
        *,
        claim_id: int,
        files: list[UploadFile],
        actor: User,
    ):
        claim = ClaimService.get_customer_claim(db, claim_id=claim_id, actor=actor)
        validated_files = await validate_uploads(
            files,
            allowed_types=ALLOWED_ATTACHMENT_TYPES,
            max_bytes=settings.CLAIM_UPLOAD_MAX_BYTES,
            empty_message="Vui lòng chọn ít nhất một tệp đính kèm.",
            unsupported_message=(
                "Định dạng tệp không được hỗ trợ. "
                "Vui lòng tải lên JPG, PNG, WEBP hoặc PDF."
            ),
            oversized_message="Tệp quá lớn. Vui lòng tải lên tệp nhỏ hơn 5MB.",
        )
        stored_files = store_uploads(
            validated_files,
            upload_dir=settings.CLAIM_UPLOAD_DIR,
            public_prefix="/uploads/claims",
            name_prefix=str(claim.id),
            allowed_types=ALLOWED_ATTACHMENT_TYPES,
        )

        created_attachments = [
            ClaimAttachmentRepository.create_attachment(
                db,
                claim_id=claim.id,
                file_name=stored_file.original_name,
                file_url=stored_file.file_url,
                mime_type=stored_file.mime_type,
                file_size=stored_file.file_size,
            )
            for stored_file in stored_files
        ]

        AuditRepository.record_activity(
            db,
            actor_user_id=actor.id,
            action="customer.claim.attachments.upload",
            entity_type="claim",
            entity_id=str(claim.id),
            metadata_json={"count": len(created_attachments)},
        )
        db.commit()
        for attachment in created_attachments:
            db.refresh(attachment)
        return created_attachments

    @staticmethod
    def list_claim_attachments(
        db: Session,
        *,
        claim_id: int,
        actor: User,
    ):
        claim = ClaimRepository.get_by_id(db, claim_id)
        if claim is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy hồ sơ bồi thường",
            )
        _ensure_actor_can_view_claim(db, actor, claim)
        return ClaimAttachmentRepository.list_for_claim(db, claim_id)

    @staticmethod
    def delete_customer_attachment(
        db: Session,
        *,
        claim_id: int,
        attachment_id: int,
        actor: User,
    ) -> None:
        claim = ClaimService.get_customer_claim(db, claim_id=claim_id, actor=actor)
        if claim.status not in {
            ClaimStatus.PENDING,
            ClaimStatus.NEED_MORE_DOCUMENTS,
        }:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Chỉ có thể xóa tệp khi hồ sơ đang chờ xử lý "
                    "hoặc cần bổ sung hồ sơ."
                ),
            )

        attachment = ClaimAttachmentRepository.get_by_id(db, attachment_id)
        if attachment is None or attachment.claim_id != claim.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy tệp đính kèm",
            )

        remove_stored_upload(
            file_url=attachment.file_url,
            upload_dir=settings.CLAIM_UPLOAD_DIR,
        )
        ClaimAttachmentRepository.delete_attachment(db, attachment)
        AuditRepository.record_activity(
            db,
            actor_user_id=actor.id,
            action="customer.claim.attachments.delete",
            entity_type="claim_attachment",
            entity_id=str(attachment.id),
            metadata_json={"claim_id": claim.id},
        )
        db.commit()
