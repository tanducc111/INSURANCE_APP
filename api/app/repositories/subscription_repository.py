from datetime import UTC, datetime

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, joinedload

from app.models.customer_management import (
    AssignmentStatus,
    Customer,
    CustomerAssignment,
    Employee,
    FollowUpNote,
)
from app.models.insurance import InsurancePackage
from app.models.subscription import (
    CustomerInsuranceSubscription,
    PaymentStatus,
    SubscriptionStatus,
)
from app.models.user import User
from app.schemas.subscription import CustomerInsuranceSubscriptionCreate


def _subscription_options():
    return (
        joinedload(CustomerInsuranceSubscription.customer).joinedload(Customer.user),
        joinedload(CustomerInsuranceSubscription.package),
    )


class SubscriptionRepository:
    @staticmethod
    def get_by_id(
        db: Session,
        subscription_id: int,
    ) -> CustomerInsuranceSubscription | None:
        return db.scalar(
            select(CustomerInsuranceSubscription)
            .options(*_subscription_options())
            .where(CustomerInsuranceSubscription.id == subscription_id)
        )

    @staticmethod
    def get_by_policy_number(
        db: Session,
        policy_number: str,
    ) -> CustomerInsuranceSubscription | None:
        return db.scalar(
            select(CustomerInsuranceSubscription).where(
                func.lower(CustomerInsuranceSubscription.policy_number)
                == policy_number.lower()
            )
        )

    @staticmethod
    def list_subscriptions(
        db: Session,
        *,
        skip: int = 0,
        limit: int = 50,
        search: str | None = None,
        status_filter: SubscriptionStatus | None = None,
        payment_status: PaymentStatus | None = None,
        customer_id: int | None = None,
        customer_ids: list[int] | None = None,
    ) -> list[CustomerInsuranceSubscription]:
        query: Select[tuple[CustomerInsuranceSubscription]] = (
            select(CustomerInsuranceSubscription)
            .options(*_subscription_options())
            .join(CustomerInsuranceSubscription.customer)
            .join(CustomerInsuranceSubscription.package)
            .join(Customer.user)
            .order_by(CustomerInsuranceSubscription.created_at.desc())
        )
        if customer_id is not None:
            query = query.where(CustomerInsuranceSubscription.customer_id == customer_id)
        if customer_ids is not None:
            if not customer_ids:
                return []
            query = query.where(CustomerInsuranceSubscription.customer_id.in_(customer_ids))
        if status_filter:
            query = query.where(CustomerInsuranceSubscription.status == status_filter)
        if payment_status:
            query = query.where(
                CustomerInsuranceSubscription.payment_status == payment_status
            )
        if search:
            pattern = f"%{search.lower()}%"
            query = query.where(
                func.lower(CustomerInsuranceSubscription.policy_number).like(pattern)
                | func.lower(Customer.customer_code).like(pattern)
                | func.lower(User.full_name).like(pattern)
                | func.lower(InsurancePackage.name).like(pattern)
                | func.lower(InsurancePackage.code).like(pattern)
            )
        return list(db.scalars(query.offset(skip).limit(limit)))

    @staticmethod
    def create_subscription(
        db: Session,
        payload: CustomerInsuranceSubscriptionCreate,
    ) -> CustomerInsuranceSubscription:
        subscription = CustomerInsuranceSubscription(**payload.model_dump())
        db.add(subscription)
        return subscription


class DashboardRepository:
    @staticmethod
    def count_customers(db: Session) -> int:
        return db.scalar(select(func.count(Customer.id))) or 0

    @staticmethod
    def count_employees(db: Session) -> int:
        return db.scalar(select(func.count(Employee.id))) or 0

    @staticmethod
    def count_packages(db: Session) -> int:
        return db.scalar(select(func.count(InsurancePackage.id))) or 0

    @staticmethod
    def count_subscriptions(
        db: Session,
        status_filter: SubscriptionStatus,
        customer_ids: list[int] | None = None,
    ) -> int:
        query = select(func.count(CustomerInsuranceSubscription.id)).where(
            CustomerInsuranceSubscription.status == status_filter
        )
        if customer_ids is not None:
            if not customer_ids:
                return 0
            query = query.where(CustomerInsuranceSubscription.customer_id.in_(customer_ids))
        return db.scalar(query) or 0

    @staticmethod
    def subscription_status_chart(db: Session) -> list[tuple[str, int]]:
        rows = db.execute(
            select(
                CustomerInsuranceSubscription.status,
                func.count(CustomerInsuranceSubscription.id),
            )
            .group_by(CustomerInsuranceSubscription.status)
            .order_by(CustomerInsuranceSubscription.status)
        ).all()
        return [(status.value, count) for status, count in rows]

    @staticmethod
    def package_registration_chart(db: Session) -> list[tuple[str, int]]:
        rows = db.execute(
            select(
                InsurancePackage.name,
                func.count(CustomerInsuranceSubscription.id),
            )
            .select_from(CustomerInsuranceSubscription)
            .join(CustomerInsuranceSubscription.package)
            .group_by(InsurancePackage.name)
            .order_by(func.count(CustomerInsuranceSubscription.id).desc())
            .limit(10)
        ).all()
        return [(name, count) for name, count in rows]

    @staticmethod
    def assigned_customer_ids(db: Session, employee_id: int) -> list[int]:
        return list(
            db.scalars(
                select(CustomerAssignment.customer_id).where(
                    CustomerAssignment.employee_id == employee_id,
                    CustomerAssignment.status == AssignmentStatus.ACTIVE,
                )
            )
        )

    @staticmethod
    def pending_follow_ups(db: Session, employee_id: int) -> int:
        now = datetime.now(UTC)
        return (
            db.scalar(
                select(func.count(FollowUpNote.id)).where(
                    FollowUpNote.employee_id == employee_id,
                    FollowUpNote.next_action_at.is_not(None),
                    FollowUpNote.next_action_at <= now,
                )
            )
            or 0
        )
