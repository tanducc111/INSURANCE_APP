import enum
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum as SAEnum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IDMixin, TimestampMixin
from app.models.user import UserStatus, enum_values


class AssignmentStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class Employee(IDMixin, TimestampMixin, Base):
    __tablename__ = "employees"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
    )
    employee_code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    department: Mapped[str | None] = mapped_column(String(120), nullable=True)
    position: Mapped[str | None] = mapped_column(String(120), nullable=True)
    hire_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    user = relationship("User", back_populates="employee_profile")
    customer_assignments = relationship(
        "CustomerAssignment",
        back_populates="employee",
        cascade="all, delete-orphan",
    )
    follow_up_notes = relationship("FollowUpNote", back_populates="employee")

    @property
    def email(self) -> str:
        return self.user.email

    @property
    def full_name(self) -> str:
        return self.user.full_name

    @property
    def status(self) -> UserStatus:
        return self.user.status


class Customer(IDMixin, TimestampMixin, Base):
    __tablename__ = "customers"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
    )
    customer_code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    identity_number: Mapped[str | None] = mapped_column(
        String(80),
        unique=True,
        index=True,
        nullable=True,
    )

    user = relationship("User", back_populates="customer_profile")
    customer_assignments = relationship(
        "CustomerAssignment",
        back_populates="customer",
        cascade="all, delete-orphan",
    )
    follow_up_notes = relationship("FollowUpNote", back_populates="customer")

    @property
    def email(self) -> str:
        return self.user.email

    @property
    def full_name(self) -> str:
        return self.user.full_name

    @property
    def status(self) -> UserStatus:
        return self.user.status


class CustomerAssignment(IDMixin, TimestampMixin, Base):
    __tablename__ = "customer_assignments"

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"),
        index=True,
    )
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"),
        index=True,
    )
    status: Mapped[AssignmentStatus] = mapped_column(
        SAEnum(
            AssignmentStatus,
            name="customer_assignment_status",
            native_enum=False,
            values_callable=enum_values,
        ),
        default=AssignmentStatus.ACTIVE,
        server_default=AssignmentStatus.ACTIVE.value,
        nullable=False,
        index=True,
    )

    customer = relationship("Customer", back_populates="customer_assignments")
    employee = relationship("Employee", back_populates="customer_assignments")

    @property
    def customer_name(self) -> str:
        return self.customer.full_name

    @property
    def customer_code(self) -> str:
        return self.customer.customer_code

    @property
    def employee_name(self) -> str:
        return self.employee.full_name

    @property
    def employee_code(self) -> str:
        return self.employee.employee_code


class FollowUpNote(IDMixin, TimestampMixin, Base):
    __tablename__ = "follow_up_notes"

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"),
        index=True,
    )
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"),
        index=True,
    )
    note: Mapped[str] = mapped_column(Text, nullable=False)
    next_action_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    customer = relationship("Customer", back_populates="follow_up_notes")
    employee = relationship("Employee", back_populates="follow_up_notes")

    @property
    def employee_name(self) -> str:
        return self.employee.full_name

    @property
    def customer_name(self) -> str:
        return self.customer.full_name
