from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.subscription import PaymentStatus, SubscriptionStatus
from app.schemas.customer_management import EmployeeRead


class CustomerInsuranceSubscriptionBase(BaseModel):
    customer_id: int
    package_id: int
    start_date: date
    end_date: date
    status: SubscriptionStatus = SubscriptionStatus.PENDING
    payment_status: PaymentStatus = PaymentStatus.UNPAID
    policy_number: str = Field(min_length=1, max_length=80)
    premium_amount: Decimal = Field(ge=0)


class CustomerInsuranceSubscriptionCreate(CustomerInsuranceSubscriptionBase):
    pass


class CustomerInsuranceSubscriptionUpdate(BaseModel):
    customer_id: int | None = None
    package_id: int | None = None
    start_date: date | None = None
    end_date: date | None = None
    status: SubscriptionStatus | None = None
    payment_status: PaymentStatus | None = None
    policy_number: str | None = Field(default=None, min_length=1, max_length=80)
    premium_amount: Decimal | None = Field(default=None, ge=0)


class CustomerInsuranceSubscriptionRead(CustomerInsuranceSubscriptionBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_name: str
    customer_code: str
    package_name: str
    package_code: str
    created_at: datetime
    updated_at: datetime


class ChartDataPoint(BaseModel):
    label: str
    value: int


class AdminDashboardStats(BaseModel):
    total_customers: int
    total_employees: int
    total_packages: int
    active_subscriptions: int
    pending_subscriptions: int
    subscription_status_chart: list[ChartDataPoint]
    package_registration_chart: list[ChartDataPoint]


class EmployeeDashboardStats(BaseModel):
    assigned_customers_count: int
    active_subscriptions_count: int
    pending_follow_ups: int


class CustomerDashboardStats(BaseModel):
    active_packages: int
    expired_packages: int
    assigned_employee: EmployeeRead | None
    latest_subscriptions: list[CustomerInsuranceSubscriptionRead]
