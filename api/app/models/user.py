import enum

from sqlalchemy import Enum as SAEnum
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IDMixin, TimestampMixin


def enum_values(enum_class: type[enum.Enum]) -> list[str]:
    return [item.value for item in enum_class]


class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    EMPLOYEE = "EMPLOYEE"
    CUSTOMER = "CUSTOMER"


class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class User(IDMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SAEnum(
            UserRole,
            name="user_role",
            native_enum=False,
            values_callable=enum_values,
        ),
        nullable=False,
    )
    status: Mapped[UserStatus] = mapped_column(
        SAEnum(
            UserStatus,
            name="user_status",
            native_enum=False,
            values_callable=enum_values,
        ),
        default=UserStatus.ACTIVE,
        server_default=UserStatus.ACTIVE.value,
        nullable=False,
    )

    login_history = relationship("LoginHistory", back_populates="user")
    activity_logs = relationship("ActivityLog", back_populates="actor")
    employee_profile = relationship(
        "Employee",
        back_populates="user",
        uselist=False,
    )
    customer_profile = relationship(
        "Customer",
        back_populates="user",
        uselist=False,
    )
