import enum
from datetime import date

from sqlalchemy import Date, Enum as SAEnum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IDMixin, TimestampMixin
from app.models.user import enum_values


class ClaimIncidentType(str, enum.Enum):
    ACCIDENT = "accident"
    HOSPITAL = "hospital"
    DAMAGE = "damage"
    OTHER = "other"


class ClaimStatus(str, enum.Enum):
    PENDING = "pending"
    REVIEWING = "reviewing"
    NEED_MORE_DOCUMENTS = "need_more_documents"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"


class ClaimPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Claim(IDMixin, TimestampMixin, Base):
    __tablename__ = "claims"

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"),
        index=True,
    )
    subscription_id: Mapped[int] = mapped_column(
        ForeignKey("customer_insurance_subscriptions.id", ondelete="CASCADE"),
        index=True,
    )
    assigned_employee_id: Mapped[int | None] = mapped_column(
        ForeignKey("employees.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    incident_type: Mapped[ClaimIncidentType] = mapped_column(
        SAEnum(
            ClaimIncidentType,
            name="claim_incident_type",
            native_enum=False,
            values_callable=enum_values,
        ),
        nullable=False,
        index=True,
    )
    incident_date: Mapped[date] = mapped_column(Date, nullable=False)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[ClaimStatus] = mapped_column(
        SAEnum(
            ClaimStatus,
            name="claim_status",
            native_enum=False,
            values_callable=enum_values,
        ),
        default=ClaimStatus.PENDING,
        server_default=ClaimStatus.PENDING.value,
        nullable=False,
        index=True,
    )
    priority: Mapped[ClaimPriority] = mapped_column(
        SAEnum(
            ClaimPriority,
            name="claim_priority",
            native_enum=False,
            values_callable=enum_values,
        ),
        default=ClaimPriority.MEDIUM,
        server_default=ClaimPriority.MEDIUM.value,
        nullable=False,
        index=True,
    )
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    customer = relationship("Customer", back_populates="claims")
    subscription = relationship(
        "CustomerInsuranceSubscription",
        back_populates="claims",
    )
    assigned_employee = relationship("Employee", back_populates="assigned_claims")
    attachments = relationship(
        "ClaimAttachment",
        back_populates="claim",
        cascade="all, delete-orphan",
    )

    @property
    def customer_name(self) -> str:
        return self.customer.full_name

    @property
    def customer_code(self) -> str:
        return self.customer.customer_code

    @property
    def policy_number(self) -> str:
        return self.subscription.policy_number

    @property
    def package_name(self) -> str:
        return self.subscription.package_name

    @property
    def assigned_employee_name(self) -> str | None:
        return self.assigned_employee.full_name if self.assigned_employee else None

    @property
    def assigned_employee_code(self) -> str | None:
        return self.assigned_employee.employee_code if self.assigned_employee else None


class ClaimAttachment(IDMixin, TimestampMixin, Base):
    __tablename__ = "claim_attachments"

    claim_id: Mapped[int] = mapped_column(
        ForeignKey("claims.id", ondelete="CASCADE"),
        index=True,
    )
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)

    claim = relationship("Claim", back_populates="attachments")
