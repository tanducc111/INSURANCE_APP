import enum
from decimal import Decimal

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IDMixin, TimestampMixin
from app.models.user import UserRole, enum_values


class InsuranceStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class InsurancePackage(IDMixin, TimestampMixin, Base):
    __tablename__ = "insurance_packages"

    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    package_type: Mapped[str] = mapped_column(String(120), index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    premium_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    coverage_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    duration_months: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[InsuranceStatus] = mapped_column(
        SAEnum(
            InsuranceStatus,
            name="insurance_package_status",
            native_enum=False,
            values_callable=enum_values,
        ),
        default=InsuranceStatus.ACTIVE,
        server_default=InsuranceStatus.ACTIVE.value,
        nullable=False,
        index=True,
    )

    processes = relationship(
        "InsuranceProcess",
        back_populates="package",
        cascade="all, delete-orphan",
    )
    subscriptions = relationship(
        "CustomerInsuranceSubscription",
        back_populates="package",
        cascade="all, delete-orphan",
    )


class InsuranceProcess(IDMixin, TimestampMixin, Base):
    __tablename__ = "insurance_processes"

    package_id: Mapped[int] = mapped_column(
        ForeignKey("insurance_packages.id", ondelete="CASCADE"),
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[InsuranceStatus] = mapped_column(
        SAEnum(
            InsuranceStatus,
            name="insurance_process_status",
            native_enum=False,
            values_callable=enum_values,
        ),
        default=InsuranceStatus.ACTIVE,
        server_default=InsuranceStatus.ACTIVE.value,
        nullable=False,
        index=True,
    )

    package = relationship("InsurancePackage", back_populates="processes")
    steps = relationship(
        "ProcessStep",
        back_populates="process",
        cascade="all, delete-orphan",
        order_by="ProcessStep.step_order",
    )


class ProcessStep(IDMixin, TimestampMixin, Base):
    __tablename__ = "process_steps"

    process_id: Mapped[int] = mapped_column(
        ForeignKey("insurance_processes.id", ondelete="CASCADE"),
        index=True,
    )
    step_order: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    required_role: Mapped[UserRole | None] = mapped_column(
        SAEnum(
            UserRole,
            name="process_step_required_role",
            native_enum=False,
            values_callable=enum_values,
        ),
        nullable=True,
    )

    process = relationship("InsuranceProcess", back_populates="steps")
