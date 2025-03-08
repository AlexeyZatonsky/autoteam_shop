from pydantic import BaseModel, Field
from .models import UserRole


class TelegramUser(BaseModel):
    id: int
    first_name: str
    last_name: str | None = None
    username: str | None = None
    language_code: str | None = None
    allows_write_to_pm: bool | None = None


class TelegramAuthData(BaseModel):
    user: TelegramUser
    auth_date: int
    hash: str
    chat_instance: str | None = None
    chat_type: str | None = None


class UserProfile(BaseModel):
    phone: str | None = None
    delivery_address: str | None = None


class UserResponse(BaseModel):
    id: int
    name: str
    tg_name: str
    role: UserRole
    is_admin: bool
    phone: str | None = None
    default_delivery_address: str | None = None
    language_code: str | None = None

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse 