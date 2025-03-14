from pydantic import BaseModel, Field
from .models import UserRole


class TelegramUser(BaseModel):
    id: int
    first_name: str
    last_name: str | None = None
    username: str | None = None
    language_code: str | None = None
    photo_url: str | None = None
    added_to_attachment_menu: bool = False
    allows_write_to_pm: bool = False
    is_premium: bool = False


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
    id: str
    first_name: str
    last_name: str | None = None
    tg_name: str
    role: UserRole
    phone: str | None = None
    default_delivery_address: str | None = None
    language_code: str | None = None

    class Config:
        from_attributes = True
        
    @classmethod
    def from_orm(cls, obj):
        user_dict = {
            "id": obj.id,
            "first_name": obj.first_name,
            "last_name": obj.last_name,
            "tg_name": obj.tg_name,
            "role": obj.role,
            "phone": obj.phone,
            "default_delivery_address": obj.default_delivery_address,
            "language_code": obj.language_code
        }
        return cls(**user_dict)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse 


class InitData(BaseModel):
    query_id: str | None = None
    user: TelegramUser
    receiver: str | None = None
    chat: str | None = None
    chat_type: str | None = None
    chat_instance: str | None = None
    start_param: str | None = None
    can_send_after: str | None = None
    auth_date: int
    hash: str 