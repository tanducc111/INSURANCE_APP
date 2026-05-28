import enum
from datetime import date
from decimal import Decimal

from sqlalchemy import Date, Enum as SAEnum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IDMixin, TimestampMixin
from app.models.user import enum_values


class SubscriptionStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class PaymentStatus(str, enum.Enum):
    UNPAID = "unpaid"
    PAID = "paid"
    OVERDUE = "overdue"


class CustomerInsuranceSubscription(IDMixin, TimestampMixin, Base):
    __tablename__ = "customer_insurance_subscriptions"

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"),
        index=True,
    )
    package_id: Mapped[int] = mapped_column(
        ForeignKey("insurance_packages.id", ondelete="CASCADE"),
        index=True,
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[SubscriptionStatus] = mapped_column(
        SAEnum(
            SubscriptionStatus,
            name="subscription_status",
            native_enum=False,
            values_callable=enum_values,
        ),
        default=SubscriptionStatus.PENDING,
        server_default=SubscriptionStatus.PENDING.value,
        nullable=False,
        index=True,
    )
    payment_status: Mapped[PaymentStatus] = mapped_column(
        SAEnum(
            PaymentStatus,
            name="subscription_payment_status",
            native_enum=False,
            values_callable=enum_values,
        ),
        default=PaymentStatus.UNPAID,
        server_default=PaymentStatus.UNPAID.value,
        nullable=False,
        index=True,
    )
    policy_number: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    premium_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    customer = relationship("Customer", back_populates="subscriptions")
    package = relationship("InsurancePackage", back_populates="subscriptions")

    @property
    def customer_name(self) -> str:
        return self.customer.full_name

    @property
    def customer_code(self) -> str:
        return self.customer.customer_code

    @property
    def package_name(self) -> str:
        return self.package.name

    @property
    def package_code(self) -> str:
        return self.package.code
