from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.customer_management import Employee
from app.models.subscription import CustomerInsuranceSubscription, SubscriptionStatus
from app.models.user import User
from app.repositories.audit_repository import AuditRepository
from app.repositories.customer_management_repository import (
    AssignmentRepository,
    CustomerRepository,
    EmployeeRepository,
)
from app.repositories.insurance_repository import InsurancePackageRepository
from app.repositories.subscription_repository import (
    DashboardRepository,
    SubscriptionRepository,
)
from app.schemas.subscription import (
    AdminDashboardStats,
    ChartDataPoint,
    CustomerDashboardStats,
    CustomerInsuranceSubscriptionCreate,
    CustomerInsuranceSubscriptionUpdate,
    EmployeeDashboardStats,
)


def _get_employee_profile(db: Session, user: User) -> Employee:
    employee = EmployeeRepository.get_by_user_id(db, user.id)
    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee profile not found",
        )
    return employee


class SubscriptionService:
    @staticmethod
    def list_admin_subscriptions(
        db: Session,
        *,
        skip: int = 0,
        limit: int = 50,
        search: str | None = None,
        status_filter=None,
        payment_status=None,
    ) -> list[CustomerInsuranceSubscription]:
        return SubscriptionRepository.list_subscriptions(
            db,
            skip=skip,
            limit=min(limit, 100),
            search=search,
            status_filter=status_filter,
            payment_status=payment_status,
        )

    @staticmethod
    def create_subscription(
        db: Session,
        *,
        payload: CustomerInsuranceSubscriptionCreate,
        actor: User,
    ) -> CustomerInsuranceSubscription:
        customer = CustomerRepository.get_by_id(db, payload.customer_id)
        package = InsurancePackageRepository.get_by_id(db, payload.package_id)
        if customer is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found",
            )
        if package is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Insurance package not found",
            )
        if payload.end_date < payload.start_date:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="End date must be after start date",
            )
        if SubscriptionRepository.get_by_policy_number(db, payload.policy_number):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Policy number already exists",
            )

        subscription = SubscriptionRepository.create_subscription(db, payload)
        db.flush()
        AuditRepository.record_activity(
            db,
            actor_user_id=actor.id,
            action="admin.subscription.create",
            entity_type="customer_insurance_subscription",
            entity_id=str(subscription.id),
            metadata_json={
                "customer_id": subscription.customer_id,
                "package_id": subscription.package_id,
                "policy_number": subscription.policy_number,
            },
        )
        db.commit()
        db.refresh(subscription)
        return subscription

    @staticmethod
    def update_subscription(
        db: Session,
        *,
        subscription_id: int,
        payload: CustomerInsuranceSubscriptionUpdate,
        actor: User,
    ) -> CustomerInsuranceSubscription:
        subscription = SubscriptionRepository.get_by_id(db, subscription_id)
        if subscription is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found",
            )

        update_data = payload.model_dump(exclude_unset=True)
        if "customer_id" in update_data and not CustomerRepository.get_by_id(
            db,
            update_data["customer_id"],
        ):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found",
            )
        if "package_id" in update_data and not InsurancePackageRepository.get_by_id(
            db,
            update_data["package_id"],
        ):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Insurance package not found",
            )
        if "policy_number" in update_data:
            existing_subscription = SubscriptionRepository.get_by_policy_number(
                db,
                update_data["policy_number"],
            )
            if existing_subscription and existing_subscription.id != subscription.id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Policy number already exists",
                )

        start_date = update_data.get("start_date", subscription.start_date)
        end_date = update_data.get("end_date", subscription.end_date)
        if end_date < start_date:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="End date must be after start date",
            )

        for field, value in update_data.items():
            setattr(subscription, field, value)

        AuditRepository.record_activity(
            db,
            actor_user_id=actor.id,
            action="admin.subscription.update",
            entity_type="customer_insurance_subscription",
            entity_id=str(subscription.id),
            metadata_json={"fields": sorted(update_data.keys())},
        )
        db.commit()
        db.refresh(subscription)
        return subscription

    @staticmethod
    def list_customer_subscriptions(
        db: Session,
        *,
        user: User,
        skip: int = 0,
        limit: int = 50,
    ) -> list[CustomerInsuranceSubscription]:
        customer = CustomerRepository.get_by_user_id(db, user.id)
        if customer is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer profile not found",
            )
        return SubscriptionRepository.list_subscriptions(
            db,
            customer_id=customer.id,
            skip=skip,
            limit=min(limit, 100),
        )

    @staticmethod
    def list_employee_customer_subscriptions(
        db: Session,
        *,
        customer_id: int,
        user: User,
        skip: int = 0,
        limit: int = 50,
    ) -> list[CustomerInsuranceSubscription]:
        employee = _get_employee_profile(db, user)
        assignment = AssignmentRepository.get_active_for_customer(db, customer_id)
        if assignment is None or assignment.employee_id != employee.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Customer is not assigned to this employee",
            )
        return SubscriptionRepository.list_subscriptions(
            db,
            customer_id=customer_id,
            skip=skip,
            limit=min(limit, 100),
        )


class DashboardService:
    @staticmethod
    def get_admin_dashboard(db: Session) -> AdminDashboardStats:
        status_chart = [
            ChartDataPoint(label=label, value=value)
            for label, value in DashboardRepository.subscription_status_chart(db)
        ]
        package_chart = [
            ChartDataPoint(label=label, value=value)
            for label, value in DashboardRepository.package_registration_chart(db)
        ]
        return AdminDashboardStats(
            total_customers=DashboardRepository.count_customers(db),
            total_employees=DashboardRepository.count_employees(db),
            total_packages=DashboardRepository.count_packages(db),
            active_subscriptions=DashboardRepository.count_subscriptions(
                db,
                SubscriptionStatus.ACTIVE,
            ),
            pending_subscriptions=DashboardRepository.count_subscriptions(
                db,
                SubscriptionStatus.PENDING,
            ),
            subscription_status_chart=status_chart,
            package_registration_chart=package_chart,
        )

    @staticmethod
    def get_employee_dashboard(db: Session, *, user: User) -> EmployeeDashboardStats:
        employee = _get_employee_profile(db, user)
        customer_ids = DashboardRepository.assigned_customer_ids(db, employee.id)
        return EmployeeDashboardStats(
            assigned_customers_count=len(customer_ids),
            active_subscriptions_count=DashboardRepository.count_subscriptions(
                db,
                SubscriptionStatus.ACTIVE,
                customer_ids=customer_ids,
            ),
            pending_follow_ups=DashboardRepository.pending_follow_ups(db, employee.id),
        )

    @staticmethod
    def get_customer_dashboard(db: Session, *, user: User) -> CustomerDashboardStats:
        customer = CustomerRepository.get_by_user_id(db, user.id)
        if customer is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer profile not found",
            )
        subscriptions = SubscriptionRepository.list_subscriptions(
            db,
            customer_id=customer.id,
            limit=5,
        )
        assignment = AssignmentRepository.get_active_for_customer(db, customer.id)
        return CustomerDashboardStats(
            active_packages=DashboardRepository.count_subscriptions(
                db,
                SubscriptionStatus.ACTIVE,
                customer_ids=[customer.id],
            ),
            expired_packages=DashboardRepository.count_subscriptions(
                db,
                SubscriptionStatus.EXPIRED,
                customer_ids=[customer.id],
            ),
            assigned_employee=assignment.employee if assignment else None,
            latest_subscriptions=subscriptions,
        )
