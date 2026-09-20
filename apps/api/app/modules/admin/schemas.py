import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, EmailStr, Field, model_validator

from app.modules.auth.schemas import validate_password_strength


class CreateStaffRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str = Field(min_length=1, max_length=150)
    role_names: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def check_password(self) -> "CreateStaffRequest":
        validate_password_strength(self.password)
        return self


class AssignRolesRequest(BaseModel):
    role_names: list[str] = Field(min_length=1)


class StaffSummary(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    status: str
    roles: list[str]

    model_config = {"from_attributes": True}


class PermissionResponse(BaseModel):
    code: str
    description: str | None

    model_config = {"from_attributes": True}


class RoleResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    permissions: list[str]

    model_config = {"from_attributes": True}


class AuditLogEntry(BaseModel):
    id: uuid.UUID
    actor_type: str
    actor_id: uuid.UUID | None
    action: str
    entity_type: str
    entity_id: uuid.UUID
    before: dict[str, Any] | None
    after: dict[str, Any] | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ShippingRateResponse(BaseModel):
    id: uuid.UUID
    zone: str
    method: str
    base_rate: Decimal
    base_weight_grams: int
    per_kg_rate: Decimal
    is_active: bool

    model_config = {"from_attributes": True}


class UpdateShippingRateRequest(BaseModel):
    base_rate: Decimal | None = Field(default=None, gt=0)
    base_weight_grams: int | None = Field(default=None, gt=0)
    per_kg_rate: Decimal | None = Field(default=None, ge=0)
    is_active: bool | None = None
