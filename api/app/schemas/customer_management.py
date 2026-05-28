from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.customer_management import AssignmentStatus
from app.models.user import UserStatus


class EmployeeCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)
    status: UserStatus = UserStatus.ACTIVE
    employee_code: str = Field(min_length=1, max_length=50)
    department: str | None = Field(default=None, max_length=120)
    position: str | None = Field(default=None, max_length=120)
    hire_date: date | None = None


class EmployeeUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    status: UserStatus | None = None
    employee_code: str | None = Field(default=None, min_length=1, max_length=50)
    department: str | None = Field(default=None, max_length=120)
    position: str | None = Field(default=None, max_length=120)
    hire_date: date | None = None


class EmployeeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    email: EmailStr
    full_name: str
    status: UserStatus
    employee_code: str
    department: str | None
    position: str | None
    hire_date: date | None
    created_at: datetime
    updated_at: datetime


class CustomerCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)
    status: UserStatus = UserStatus.ACTIVE
    customer_code: str = Field(min_length=1, max_length=50)
    date_of_birth: date | None = None
    address: str | None = None
    identity_number: str | None = Field(default=None, max_length=80)


class CustomerUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    status: UserStatus | None = None
    customer_code: str | None = Field(default=None, min_length=1, max_length=50)
    date_of_birth: date | None = None
    address: str | None = None
    identity_number: str | None = Field(default=None, max_length=80)


class CustomerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    email: EmailStr
    full_name: str
    status: UserStatus
    customer_code: str
    date_of_birth: date | None
    address: str | None
    identity_number: str | None
    created_at: datetime
    updated_at: datetime


class CustomerAssignmentCreate(BaseModel):
    customer_id: int
    employee_id: int
    status: AssignmentStatus = AssignmentStatus.ACTIVE


class CustomerAssignmentUpdate(BaseModel):
    status: AssignmentStatus


class CustomerAssignmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int
    employee_id: int
    status: AssignmentStatus
    customer_name: str
    customer_code: str
    employee_name: str
    employee_code: str
    created_at: datetime
    updated_at: datetime


class FollowUpNoteCreate(BaseModel):
    note: str = Field(min_length=1)
    next_action_at: datetime | None = None


class FollowUpNoteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int
    employee_id: int
    note: str
    next_action_at: datetime | None
    employee_name: str
    customer_name: str
    created_at: datetime
    updated_at: datetime
