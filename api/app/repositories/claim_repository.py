from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, joinedload

from app.models.claim import (
    Claim,
    ClaimAttachment,
    ClaimIncidentType,
    ClaimPriority,
    ClaimStatus,
)
from app.models.customer_management import Customer, Employee
from app.models.insurance import InsurancePackage
from app.models.subscription import CustomerInsuranceSubscription
from app.models.user import User
from app.schemas.claim import ClaimCreate


def _claim_options():
    return (
        joinedload(Claim.customer).joinedload(Customer.user),
        joinedload(Claim.subscription).joinedload(
            CustomerInsuranceSubscription.package
        ),
        joinedload(Claim.assigned_employee).joinedload(Employee.user),
        joinedload(Claim.attachments),
    )


class ClaimRepository:
    @staticmethod
    def get_by_id(db: Session, claim_id: int) -> Claim | None:
        return (
            db.scalars(
                select(Claim).options(*_claim_options()).where(Claim.id == claim_id)
            )
            .unique()
            .first()
        )

    @staticmethod
    def list_claims(
        db: Session,
        *,
        skip: int = 0,
        limit: int = 50,
        search: str | None = None,
        status_filter: ClaimStatus | None = None,
        incident_type: ClaimIncidentType | None = None,
        priority: ClaimPriority | None = None,
        customer_id: int | None = None,
        customer_ids: list[int] | None = None,
    ) -> list[Claim]:
        query: Select[tuple[Claim]] = (
            select(Claim)
            .options(*_claim_options())
            .join(Claim.customer)
            .join(Customer.user)
            .join(Claim.subscription)
            .join(CustomerInsuranceSubscription.package)
            .order_by(Claim.created_at.desc())
        )
        if customer_id is not None:
            query = query.where(Claim.customer_id == customer_id)
        if customer_ids is not None:
            if not customer_ids:
                return []
            query = query.where(Claim.customer_id.in_(customer_ids))
        if status_filter:
            query = query.where(Claim.status == status_filter)
        if incident_type:
            query = query.where(Claim.incident_type == incident_type)
        if priority:
            query = query.where(Claim.priority == priority)
        if search:
            pattern = f"%{search.lower()}%"
            query = query.where(
                func.lower(Claim.title).like(pattern)
                | func.lower(Claim.location).like(pattern)
                | func.lower(Customer.customer_code).like(pattern)
                | func.lower(User.full_name).like(pattern)
                | func.lower(CustomerInsuranceSubscription.policy_number).like(pattern)
                | func.lower(InsurancePackage.name).like(pattern)
            )
        return list(db.scalars(query.offset(skip).limit(limit)).unique())

    @staticmethod
    def create_claim(
        db: Session,
        *,
        customer_id: int,
        assigned_employee_id: int | None,
        payload: ClaimCreate,
    ) -> Claim:
        claim = Claim(
            customer_id=customer_id,
            subscription_id=payload.subscription_id,
            assigned_employee_id=assigned_employee_id,
            title=payload.title,
            description=payload.description,
            incident_type=payload.incident_type,
            incident_date=payload.incident_date,
            location=payload.location,
            priority=payload.priority,
        )
        db.add(claim)
        db.flush()
        for attachment_payload in payload.attachments:
            db.add(
                ClaimAttachment(
                    claim_id=claim.id,
                    **attachment_payload.model_dump(),
                )
            )
        return claim


class ClaimDashboardRepository:
    @staticmethod
    def count_claims(
        db: Session,
        *,
        status_filter: ClaimStatus | None = None,
        customer_ids: list[int] | None = None,
    ) -> int:
        query = select(func.count(Claim.id))
        if status_filter:
            query = query.where(Claim.status == status_filter)
        if customer_ids is not None:
            if not customer_ids:
                return 0
            query = query.where(Claim.customer_id.in_(customer_ids))
        return db.scalar(query) or 0

    @staticmethod
    def count_open_claims(
        db: Session,
        *,
        customer_ids: list[int] | None = None,
    ) -> int:
        query = select(func.count(Claim.id)).where(
            Claim.status.in_(
                [
                    ClaimStatus.PENDING,
                    ClaimStatus.REVIEWING,
                    ClaimStatus.NEED_MORE_DOCUMENTS,
                ]
            )
        )
        if customer_ids is not None:
            if not customer_ids:
                return 0
            query = query.where(Claim.customer_id.in_(customer_ids))
        return db.scalar(query) or 0
