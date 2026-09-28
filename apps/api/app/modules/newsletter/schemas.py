from pydantic import BaseModel, EmailStr


class SubscribeRequest(BaseModel):
    email: EmailStr


class SubscribeResponse(BaseModel):
    email: str
    is_active: bool
