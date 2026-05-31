"""SQLAlchemy model package."""

from app.models.audit import ActivityLog, LoginHistory
from app.models.claim import (
    Claim,
    ClaimAttachment,
    ClaimIncidentType,
    ClaimPriority,
    ClaimStatus,
)
from app.models.communication import (
    Appointment,
    AppointmentStatus,
    ChatMessage,
    ChatRoom,
)
from app.models.customer_management import (
    AssignmentStatus,
    Customer,
    CustomerAssignment,
    Employee,
    FollowUpNote,
)
from app.models.insurance import (
    InsurancePackage,
    InsuranceProcess,
    InsuranceStatus,
    ProcessStep,
)
from app.models.subscription import (
    CustomerInsuranceSubscription,
    PaymentStatus,
    SubscriptionStatus,
)
from app.models.user import User, UserRole, UserStatus

__all__ = [
    "ActivityLog",
    "Appointment",
    "AppointmentStatus",
    "AssignmentStatus",
    "ChatMessage",
    "ChatRoom",
    "Claim",
    "ClaimAttachment",
    "ClaimIncidentType",
    "ClaimPriority",
    "ClaimStatus",
    "Customer",
    "CustomerAssignment",
    "CustomerInsuranceSubscription",
    "Employee",
    "FollowUpNote",
    "InsurancePackage",
    "InsuranceProcess",
    "InsuranceStatus",
    "LoginHistory",
    "PaymentStatus",
    "ProcessStep",
    "SubscriptionStatus",
    "User",
    "UserRole",
    "UserStatus",
]
