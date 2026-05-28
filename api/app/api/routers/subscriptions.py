from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.auth import require_roles
from app.db.session import get_db
from app.models.subscription import (
    CustomerInsuranceSubscription,
    PaymentStatus,
    SubscriptionStatus,
)
from app.models.user import User, UserRole
from app.schemas.subscription import (
    AdminDashboardStats,
    CustomerDashboardStats,
    CustomerInsuranceSubscriptionCreate,
    CustomerInsuranceSubscriptionRead,
    CustomerInsuranceSubscriptionUpdate,
    EmployeeDashboardStats,
)
from app.services.subscription_service import DashboardService, SubscriptionService

router = APIRouter(tags=["subscriptions"])


@router.get(
    "/admin/subscriptions",
    response_model=list[CustomerInsuranceSubscriptionRead],
)
async def list_admin_subscriptions(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    search: str | None = Query(default=None, max_length=255),
    status_filter: SubscriptionStatus | None = Query(default=None, alias="status"),
    payment_status: PaymentStatus | None = Query(default=None),
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles(UserRole.ADMIN)),
) -> list[CustomerInsuranceSubscription]:
    _ = current_admin
    return SubscriptionService.list_admin_subscriptions(
        db,
        skip=skip,
        limit=limit,
        search=search,
        status_filter=status_filter,
        payment_status=payment_status,
    )


@router.post(
    "/admin/subscriptions",
    response_model=CustomerInsuranceSubscriptionRead,
    status_code=201,
)
async def create_admin_subscription(
    payload: CustomerInsuranceSubscriptionCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles(UserRole.ADMIN)),
) -> CustomerInsuranceSubscription:
    return SubscriptionService.create_subscription(
        db,
        payload=payload,
        actor=current_admin,
    )


@router.patch(
    "/admin/subscriptions/{subscription_id}",
    response_model=CustomerInsuranceSubscriptionRead,
)
async def update_admin_subscription(
    subscription_id: int,
    payload: CustomerInsuranceSubscriptionUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles(UserRole.ADMIN)),
) -> CustomerInsuranceSubscription:
    return SubscriptionService.update_subscription(
        db,
        subscription_id=subscription_id,
        payload=payload,
        actor=current_admin,
    )


@router.get(
    "/customer/subscriptions",
    response_model=list[CustomerInsuranceSubscriptionRead],
)
async def list_customer_subscriptions(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_customer: User = Depends(require_roles(UserRole.CUSTOMER)),
) -> list[CustomerInsuranceSubscription]:
    return SubscriptionService.list_customer_subscriptions(
        db,
        user=current_customer,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/employee/customers/{customer_id}/subscriptions",
    response_model=list[CustomerInsuranceSubscriptionRead],
)
async def list_employee_customer_subscriptions(
    customer_id: int,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_employee: User = Depends(require_roles(UserRole.EMPLOYEE)),
) -> list[CustomerInsuranceSubscription]:
    return SubscriptionService.list_employee_customer_subscriptions(
        db,
        customer_id=customer_id,
        user=current_employee,
        skip=skip,
        limit=limit,
    )


@router.get("/dashboard/admin", response_model=AdminDashboardStats)
async def get_admin_dashboard(
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles(UserRole.ADMIN)),
) -> AdminDashboardStats:
    _ = current_admin
    return DashboardService.get_admin_dashboard(db)


@router.get("/dashboard/employee", response_model=EmployeeDashboardStats)
async def get_employee_dashboard(
    db: Session = Depends(get_db),
    current_employee: User = Depends(require_roles(UserRole.EMPLOYEE)),
) -> EmployeeDashboardStats:
    return DashboardService.get_employee_dashboard(db, user=current_employee)


@router.get("/dashboard/customer", response_model=CustomerDashboardStats)
async def get_customer_dashboard(
    db: Session = Depends(get_db),
    current_customer: User = Depends(require_roles(UserRole.CUSTOMER)),
) -> CustomerDashboardStats:
    return DashboardService.get_customer_dashboard(db, user=current_customer)
