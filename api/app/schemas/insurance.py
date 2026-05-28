from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.insurance import InsuranceStatus
from app.models.user import UserRole


class InsurancePackageBase(BaseModel):
    code: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=255)
    package_type: str = Field(min_length=1, max_length=120)
    description: str | None = None
    premium_amount: Decimal = Field(ge=0)
    coverage_amount: Decimal = Field(ge=0)
    duration_months: int = Field(ge=1)
    status: InsuranceStatus = InsuranceStatus.ACTIVE


class InsurancePackageCreate(InsurancePackageBase):
    pass


class InsurancePackageUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=50)
    name: str | None = Field(default=None, min_length=1, max_length=255)
    package_type: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None
    premium_amount: Decimal | None = Field(default=None, ge=0)
    coverage_amount: Decimal | None = Field(default=None, ge=0)
    duration_months: int | None = Field(default=None, ge=1)
    status: InsuranceStatus | None = None


class InsurancePackageRead(InsurancePackageBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class InsuranceProcessBase(BaseModel):
    package_id: int
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    status: InsuranceStatus = InsuranceStatus.ACTIVE


class InsuranceProcessCreate(InsuranceProcessBase):
    pass


class InsuranceProcessUpdate(BaseModel):
    package_id: int | None = None
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    status: InsuranceStatus | None = None


class InsuranceProcessRead(InsuranceProcessBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class ProcessStepBase(BaseModel):
    step_order: int = Field(ge=1)
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    required_role: UserRole | None = None


class ProcessStepCreate(ProcessStepBase):
    pass


class ProcessStepUpdate(BaseModel):
    step_order: int | None = Field(default=None, ge=1)
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    required_role: UserRole | None = None


class ProcessStepRead(ProcessStepBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    process_id: int
    created_at: datetime
    updated_at: datetime
