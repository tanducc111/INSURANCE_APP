from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.user import UserRole, UserStatus


class UserBase(BaseModel):
    email: str = Field(
        min_length=3,
        max_length=255,
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
    )
    full_name: str = Field(min_length=1, max_length=255)
    role: UserRole


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)
    status: UserStatus = UserStatus.ACTIVE


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: UserStatus
    created_at: datetime
    updated_at: datetime


class PasswordResetRequest(BaseModel):
    new_password: str = Field(min_length=8, max_length=128)


class UserStatusUpdate(BaseModel):
    status: UserStatus
