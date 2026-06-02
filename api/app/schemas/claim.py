from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.claim import ClaimIncidentType, ClaimPriority, ClaimStatus


class ClaimAttachmentCreate(BaseModel):
    file_name: str = Field(min_length=1, max_length=255)
    file_url: str = Field(min_length=1, max_length=500)
    mime_type: str | None = Field(default=None, max_length=120)
    file_size: int | None = None


class ClaimAttachmentRead(ClaimAttachmentCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    claim_id: int
    created_at: datetime
    updated_at: datetime


class ClaimCreate(BaseModel):
    subscription_id: int
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)
    incident_type: ClaimIncidentType
    incident_date: date
    location: str | None = Field(default=None, max_length=255)
    priority: ClaimPriority = ClaimPriority.MEDIUM
    attachments: list[ClaimAttachmentCreate] = Field(default_factory=list)


class ClaimStatusUpdate(BaseModel):
    status: ClaimStatus


class ClaimAssignmentUpdate(BaseModel):
    assigned_employee_id: int | None = None


class ClaimReviewNoteUpdate(BaseModel):
    review_note: str = Field(min_length=1)


class ClaimRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int
    subscription_id: int
    assigned_employee_id: int | None
    title: str
    description: str
    incident_type: ClaimIncidentType
    incident_date: date
    location: str | None
    status: ClaimStatus
    priority: ClaimPriority
    review_note: str | None
    customer_name: str
    customer_code: str
    policy_number: str
    package_name: str
    assigned_employee_name: str | None
    assigned_employee_code: str | None
    attachments: list[ClaimAttachmentRead]
    created_at: datetime
    updated_at: datetime
