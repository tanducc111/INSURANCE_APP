from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.communication import AppointmentStatus


class ChatRoomRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int
    employee_id: int
    customer_name: str
    customer_code: str
    employee_name: str
    employee_code: str
    created_at: datetime
    updated_at: datetime


class ChatMessageCreate(BaseModel):
    content: str = Field(min_length=1)


class ChatMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    room_id: int
    sender_user_id: int
    sender_name: str
    sender_role: str
    content: str
    is_read: bool
    created_at: datetime
    updated_at: datetime


class AppointmentCreate(BaseModel):
    scheduled_at: datetime
    duration_minutes: int = Field(ge=15, le=480)
    note: str | None = None


class AppointmentUpdate(BaseModel):
    scheduled_at: datetime | None = None
    duration_minutes: int | None = Field(default=None, ge=15, le=480)
    status: AppointmentStatus | None = None
    note: str | None = None


class AppointmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int
    employee_id: int
    scheduled_at: datetime
    duration_minutes: int
    status: AppointmentStatus
    note: str | None
    customer_name: str
    customer_code: str
    employee_name: str
    employee_code: str
    created_at: datetime
    updated_at: datetime
