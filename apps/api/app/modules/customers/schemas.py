import uuid

from pydantic import BaseModel, Field


class CustomerProfile(BaseModel):
    id: uuid.UUID
    email: str | None
    mobile_number: str | None
    full_name: str
    preferred_language: str
    status: str

    model_config = {"from_attributes": True}


class UpdateCustomerProfileRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=150)
    preferred_language: str | None = Field(default=None, pattern="^(en|bn)$")


class AddressBase(BaseModel):
    label: str | None = None
    recipient_name: str = Field(min_length=1, max_length=150)
    phone: str = Field(min_length=1, max_length=20)
    address_line1: str = Field(min_length=1, max_length=255)
    address_line2: str | None = None
    city: str = Field(min_length=1, max_length=100)
    district: str = Field(min_length=1, max_length=100)
    postal_code: str | None = None
    country: str = Field(default="BD", max_length=2)
    address_type: str = Field(default="shipping", pattern="^(shipping|billing|both)$")
    is_default: bool = False


class CreateAddressRequest(AddressBase):
    pass


class UpdateAddressRequest(BaseModel):
    label: str | None = None
    recipient_name: str | None = Field(default=None, min_length=1, max_length=150)
    phone: str | None = Field(default=None, min_length=1, max_length=20)
    address_line1: str | None = Field(default=None, min_length=1, max_length=255)
    address_line2: str | None = None
    city: str | None = Field(default=None, min_length=1, max_length=100)
    district: str | None = Field(default=None, min_length=1, max_length=100)
    postal_code: str | None = None
    country: str | None = Field(default=None, max_length=2)
    address_type: str | None = Field(default=None, pattern="^(shipping|billing|both)$")
    is_default: bool | None = None


class AddressResponse(AddressBase):
    id: uuid.UUID
    customer_id: uuid.UUID

    model_config = {"from_attributes": True}


class AdminUpdateCustomerStatusRequest(BaseModel):
    status: str = Field(pattern="^(active|inactive|suspended)$")


class PaginationMeta(BaseModel):
    page: int
    limit: int
    total: int
    total_pages: int


class CustomerListResponse(BaseModel):
    items: list[CustomerProfile]
    meta: PaginationMeta
