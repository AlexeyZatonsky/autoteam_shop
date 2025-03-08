from datetime import datetime, timedelta
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt

from .models import Users, UserRole
from .schemas import TelegramAuthData
from .utils import validate_telegram_authorization
from ..settings.config import settings


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create_user(
        self,
        telegram_data: TelegramAuthData
    ) -> Users:
        """Get existing user or create new one from Telegram data."""
        user = await self.session.get(Users, telegram_data.user.id)
        
        if not user:
            user = Users(
                id=telegram_data.user.id,
                name=telegram_data.user.first_name,
                tg_name=telegram_data.user.username or telegram_data.user.first_name,
                language_code=telegram_data.user.language_code,
                role=UserRole.USER
            )
            self.session.add(user)
            await self.session.commit()
        else:
            # Обновляем данные пользователя, если они изменились
            user.name = telegram_data.user.first_name
            user.tg_name = telegram_data.user.username or telegram_data.user.first_name
            user.language_code = telegram_data.user.language_code
            await self.session.commit()
        
        return user

    @staticmethod
    def create_access_token(data: dict) -> str:
        """Create JWT token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=7)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_AUTH, algorithm="HS256")
        return encoded_jwt

    async def authenticate_telegram_user(self, auth_string: str):
        """Authenticate user with Telegram data."""
        auth_data = validate_telegram_authorization(auth_string)
        if not auth_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication data"
            )
        
        user = await self.get_or_create_user(auth_data)
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is inactive"
            )
        
        access_token = self.create_access_token(
            data={
                "sub": str(user.id),
                "role": user.role
            }
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "name": user.name,
                "tg_name": user.tg_name,
                "role": user.role,
                "is_admin": user.is_admin()
            }
        }

    async def get_current_user(self, user_id: int) -> Users:
        """Get user by ID."""
        user = await self.session.get(Users, user_id)
        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user

    async def update_user_profile(
        self,
        user: Users,
        phone: str | None = None,
        delivery_address: str | None = None
    ) -> Users:
        """Update user profile information."""
        if phone is not None:
            user.phone = phone
        if delivery_address is not None:
            user.default_delivery_address = delivery_address
            
        await self.session.commit()
        return user

