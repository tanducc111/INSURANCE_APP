from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.core.auth import require_roles
from app.db.session import get_db
from app.models.claim import Claim, ClaimIncidentType, ClaimPriority, ClaimStatus
from app.models.user import User, UserRole
from app.schemas.claim import (
    ClaimAssignmentUpdate,
    ClaimAttachmentRead,
    ClaimCreate,
    ClaimRead,
    ClaimReviewNoteUpdate,
    ClaimStatusUpdate,
)
from app.services.claim_service import ClaimService

router = APIRouter(tags=["claims"])


@router.post(
    "/customer/claims",
    response_model=ClaimRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_customer_claim(
    payload: ClaimCreate,
    db: Session = Depends(get_db),
    current_customer: User = Depends(require_roles(UserRole.CUSTOMER)),
) -> Claim:
    return ClaimService.create_customer_claim(
        db,
        payload=payload,
        actor=current_customer,
    )


@router.get("/customer/claims", response_model=list[ClaimRead])
async def list_customer_claims(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    status_filter: ClaimStatus | None = Query(default=None, alias="status"),
    incident_type: ClaimIncidentType | None = Query(default=None),
    priority: ClaimPriority | None = Query(default=None),
    db: Session = Depends(get_db),
    current_customer: User = Depends(require_roles(UserRole.CUSTOMER)),
) -> list[Claim]:
    return ClaimService.list_customer_claims(
        db,
        actor=current_customer,
        skip=skip,
        limit=limit,
        status_filter=status_filter,
        incident_type=incident_type,
        priority=priority,
    )


@router.get("/customer/claims/{claim_id}", response_model=ClaimRead)
async def get_customer_claim(
    claim_id: int,
    db: Session = Depends(get_db),
    current_customer: User = Depends(require_roles(UserRole.CUSTOMER)),
) -> Claim:
    return ClaimService.get_customer_claim(
        db,
        claim_id=claim_id,
        actor=current_customer,
    )


@router.post(
    "/customer/claims/{claim_id}/attachments",
    response_model=list[ClaimAttachmentRead],
    status_code=status.HTTP_201_CREATED,
)
async def upload_customer_claim_attachments(
    claim_id: int,
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_customer: User = Depends(require_roles(UserRole.CUSTOMER)),
):
    return await ClaimService.upload_customer_attachments(
        db,
        claim_id=claim_id,
        files=files,
        actor=current_customer,
    )


@router.get("/claims/{claim_id}/attachments", response_model=list[ClaimAttachmentRead])
async def list_claim_attachments(
    claim_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.EMPLOYEE, UserRole.CUSTOMER)
    ),
):
    return ClaimService.list_claim_attachments(
        db,
        claim_id=claim_id,
        actor=current_user,
    )


@router.delete(
    "/customer/claims/{claim_id}/attachments/{attachment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_customer_claim_attachment(
    claim_id: int,
    attachment_id: int,
    db: Session = Depends(get_db),
    current_customer: User = Depends(require_roles(UserRole.CUSTOMER)),
) -> None:
    ClaimService.delete_customer_attachment(
        db,
        claim_id=claim_id,
        attachment_id=attachment_id,
        actor=current_customer,
    )


@router.get("/employee/claims", response_model=list[ClaimRead])
async def list_employee_claims(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    search: str | None = Query(default=None, max_length=255),
    status_filter: ClaimStatus | None = Query(default=None, alias="status"),
    incident_type: ClaimIncidentType | None = Query(default=None),
    priority: ClaimPriority | None = Query(default=None),
    db: Session = Depends(get_db),
    current_employee: User = Depends(require_roles(UserRole.EMPLOYEE)),
) -> list[Claim]:
    return ClaimService.list_employee_claims(
        db,
        actor=current_employee,
        skip=skip,
        limit=limit,
        search=search,
        status_filter=status_filter,
        incident_type=incident_type,
        priority=priority,
    )


@router.get("/employee/claims/{claim_id}", response_model=ClaimRead)
async def get_employee_claim(
    claim_id: int,
    db: Session = Depends(get_db),
    current_employee: User = Depends(require_roles(UserRole.EMPLOYEE)),
) -> Claim:
    return ClaimService.get_employee_claim(
        db,
        claim_id=claim_id,
        actor=current_employee,
    )


@router.patch("/employee/claims/{claim_id}/status", response_model=ClaimRead)
async def update_employee_claim_status(
    claim_id: int,
    payload: ClaimStatusUpdate,
    db: Session = Depends(get_db),
    current_employee: User = Depends(require_roles(UserRole.EMPLOYEE)),
) -> Claim:
    return ClaimService.update_employee_claim_status(
        db,
        claim_id=claim_id,
        payload=payload,
        actor=current_employee,
    )


@router.patch("/employee/claims/{claim_id}/review-note", response_model=ClaimRead)
async def add_employee_review_note(
    claim_id: int,
    payload: ClaimReviewNoteUpdate,
    db: Session = Depends(get_db),
    current_employee: User = Depends(require_roles(UserRole.EMPLOYEE)),
) -> Claim:
    return ClaimService.add_employee_review_note(
        db,
        claim_id=claim_id,
        payload=payload,
        actor=current_employee,
    )


@router.get("/admin/claims", response_model=list[ClaimRead])
async def list_admin_claims(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    search: str | None = Query(default=None, max_length=255),
    status_filter: ClaimStatus | None = Query(default=None, alias="status"),
    incident_type: ClaimIncidentType | None = Query(default=None),
    priority: ClaimPriority | None = Query(default=None),
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles(UserRole.ADMIN)),
) -> list[Claim]:
    _ = current_admin
    return ClaimService.list_admin_claims(
        db,
        skip=skip,
        limit=limit,
        search=search,
        status_filter=status_filter,
        incident_type=incident_type,
        priority=priority,
    )


@router.get("/admin/claims/{claim_id}", response_model=ClaimRead)
async def get_admin_claim(
    claim_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles(UserRole.ADMIN)),
) -> Claim:
    _ = current_admin
    return ClaimService.get_admin_claim(db, claim_id=claim_id)


@router.patch("/admin/claims/{claim_id}/assignment", response_model=ClaimRead)
async def assign_claim(
    claim_id: int,
    payload: ClaimAssignmentUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles(UserRole.ADMIN)),
) -> Claim:
    return ClaimService.assign_claim(
        db,
        claim_id=claim_id,
        payload=payload,
        actor=current_admin,
    )


@router.patch("/admin/claims/{claim_id}/status", response_model=ClaimRead)
async def update_admin_claim_status(
    claim_id: int,
    payload: ClaimStatusUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles(UserRole.ADMIN)),
) -> Claim:
    return ClaimService.update_admin_claim_status(
        db,
        claim_id=claim_id,
        payload=payload,
        actor=current_admin,
    )
