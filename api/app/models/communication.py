import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IDMixin, TimestampMixin
from app.models.user import enum_values


class AppointmentStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    RESCHEDULED = "rescheduled"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class ChatRoom(IDMixin, TimestampMixin, Base):
    __tablename__ = "chat_rooms"
    __table_args__ = (
        UniqueConstraint(
            "customer_id",
            "employee_id",
            name="uq_chat_rooms_customer_id_employee_id",
        ),
    )

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"),
        index=True,
    )
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"),
        index=True,
    )

    customer = relationship("Customer", back_populates="chat_rooms")
    employee = relationship("Employee", back_populates="chat_rooms")
    messages = relationship(
        "ChatMessage",
        back_populates="room",
        cascade="all, delete-orphan",
    )

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


class ChatMessage(IDMixin, TimestampMixin, Base):
    __tablename__ = "chat_messages"

    room_id: Mapped[int] = mapped_column(
        ForeignKey("chat_rooms.id", ondelete="CASCADE"),
        index=True,
    )
    sender_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    room = relationship("ChatRoom", back_populates="messages")
    sender = relationship("User")

    @property
    def sender_name(self) -> str:
        return self.sender.full_name

    @property
    def sender_role(self) -> str:
        return self.sender.role.value


class Appointment(IDMixin, TimestampMixin, Base):
    __tablename__ = "appointments"

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"),
        index=True,
    )
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"),
        index=True,
    )
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[AppointmentStatus] = mapped_column(
        SAEnum(
            AppointmentStatus,
            name="appointment_status",
            native_enum=False,
            values_callable=enum_values,
        ),
        default=AppointmentStatus.PENDING,
        server_default=AppointmentStatus.PENDING.value,
        nullable=False,
        index=True,
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    customer = relationship("Customer", back_populates="appointments")
    employee = relationship("Employee", back_populates="appointments")

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
