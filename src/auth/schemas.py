from pydantic import BaseModel, Field
from .models import UserRole


class TelegramUser(BaseModel):
    id: int
    first_name: str
    last_name: str | None = ""
    username: str | None = None
    language_code: str | None = None
    photo_url: str | None = None
    added_to_attachment_menu: bool | None = None
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
    signature: str | None = None
    hash: str | None = None

    @classmethod
    def from_orm(cls, obj):
        user_dict = {
            "query_id": obj.query_id,
            "user": obj.user,
            "receiver": obj.receiver,
            "chat": obj.chat,
            "chat_type": obj.chat_type,
            "chat_instance": obj.chat_instance,
            "start_param": obj.start_param,
            "can_send_after": obj.can_send_after,
            "auth_date": obj.auth_date,
            "signature": obj.signature,
            "hash": obj.hash
        }
        return cls(**user_dict) 