from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, TEXT, UUID, Enum as SQLAlchemyEnum
from ..database import Base
import uuid
import enum


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"


class Users(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)  # Используем ID из Telegram
    name = Column(String, nullable=False)
    tg_name = Column(String, nullable=False)
    phone = Column(String, nullable=True)  # Для сохранения контактного телефона
    role = Column(SQLAlchemyEnum(UserRole), nullable=False, default=UserRole.USER)
    is_active = Column(Boolean, default=True, nullable=False)
    language_code = Column(String(10), nullable=True)  # Язык пользователя из Telegram
    
    # Дополнительные поля для доставки
    default_delivery_address = Column(TEXT, nullable=True)  # Сохраняем адрес доставки
    
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN
