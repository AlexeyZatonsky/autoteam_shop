from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession

from .utils import validate_telegram_authorization
from .schemas import TelegramAuthData, UserProfile, UserResponse, TokenResponse
from .models import Users
from .service import AuthService
from ..database import get_async_session
from ..settings.config import settings


router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


async def get_or_create_user(
    telegram_data: TelegramAuthData,
    session: AsyncSession
) -> Users:
    """Get existing user or create new one from Telegram data."""
    user = await session.get(Users, telegram_data.user.id)
    
    if not user:
        user = Users(
            id=telegram_data.user.id,
            name=telegram_data.user.first_name,
            tg_name=telegram_data.user.username or telegram_data.user.first_name
        )
        session.add(user)
        await session.commit()
    
    return user


def create_access_token(data: dict) -> str:
    """Create JWT token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=7)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_AUTH, algorithm="HS256")
    return encoded_jwt


def get_auth_service(session: AsyncSession = Depends(get_async_session)) -> AuthService:
    return AuthService(session)


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    auth_service: AuthService = Depends(get_auth_service)
) -> Users:
    """Get current user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_AUTH, algorithms=["HS256"])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    return await auth_service.get_current_user(int(user_id))


@router.post("/telegram-login", response_model=TokenResponse)
async def telegram_login(
    auth_string: str,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Login with Telegram data."""
    return await auth_service.authenticate_telegram_user(auth_string)


@router.get("/me", response_model=UserResponse)
async def get_user_profile(
    current_user: Annotated[Users, Depends(get_current_user)]
):
    """Get current user profile."""
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_user_profile(
    profile: UserProfile,
    current_user: Annotated[Users, Depends(get_current_user)],
    auth_service: AuthService = Depends(get_auth_service)
):
    """Update user profile."""
    return await auth_service.update_user_profile(
        user=current_user,
        phone=profile.phone,
        delivery_address=profile.delivery_address
    ) 