import re
import uuid

from pydantic import BaseModel, EmailStr, Field, model_validator

MOBILE_BD_PATTERN = re.compile(r"^(?:\+8801|01)[3-9]\d{8}$")


def normalize_bd_mobile(value: str) -> str:
    digits = value.strip()
    if digits.startswith("01"):
        digits = "+880" + digits[1:]
    return digits


def normalize_identifier(identifier: str) -> str:
    """Login/forgot-password accept email or mobile in either the local
    (`01...`) or stored (`+8801...`) form — normalize before querying so
    lookups match what registration actually stored."""
    identifier = identifier.strip()
    if MOBILE_BD_PATTERN.match(identifier):
        return normalize_bd_mobile(identifier)
    return identifier


def validate_password_strength(password: str) -> str:
    """NFR-SEC-004: minimum complexity requirements."""
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long.")
    if not re.search(r"[A-Za-z]", password):
        raise ValueError("Password must contain at least one letter.")
    if not re.search(r"\d", password):
        raise ValueError("Password must contain at least one digit.")
    return password


class RegisterRequest(BaseModel):
    email: EmailStr | None = None
    mobile_number: str | None = None
    password: str
    full_name: str = Field(min_length=1, max_length=150)

    @model_validator(mode="after")
    def check_identifier_and_password(self) -> "RegisterRequest":
        if not self.email and not self.mobile_number:
            raise ValueError("Either email or mobile_number is required.")
        if self.mobile_number and not MOBILE_BD_PATTERN.match(self.mobile_number):
            raise ValueError("mobile_number must be a valid Bangladeshi mobile number.")
        if self.mobile_number:
            self.mobile_number = normalize_bd_mobile(self.mobile_number)
        validate_password_strength(self.password)
        return self


class LoginRequest(BaseModel):
    identifier: str
    password: str


class CustomerSummary(BaseModel):
    id: uuid.UUID
    email: str | None
    mobile_number: str | None
    full_name: str

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    customer: CustomerSummary
    access_token: str
    refresh_token: str


class RefreshRequest(BaseModel):
    refresh_token: str


class AccessTokenResponse(BaseModel):
    access_token: str
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    identifier: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

    @model_validator(mode="after")
    def check_password(self) -> "ResetPasswordRequest":
        validate_password_strength(self.new_password)
        return self


class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str


class AdminSummary(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    roles: list[str]

    model_config = {"from_attributes": True}


class AdminTokenResponse(BaseModel):
    admin: AdminSummary
    access_token: str
    refresh_token: str
