from fastapi import APIRouter, Depends, HTTPException, status, Form, Body, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
import urllib.parse
import json

from .schemas import UserProfile, UserResponse, TokenResponse
from .service import AuthService
from ..database import get_async_session
from ..settings.config import settings


router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

# Схема для проверки Bearer-токена
bearer_scheme = HTTPBearer(auto_error=True)


def get_auth_service(session: AsyncSession = Depends(get_async_session)) -> AuthService:
    """Получение экземпляра сервиса авторизации."""
    return AuthService(session)


async def get_current_user(
    auth: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    auth_service: AuthService = Depends(get_auth_service)
) -> UserResponse:
    """
    Получение текущего пользователя из JWT-токена.
    
    Используется как зависимость для защищенных эндпоинтов.
    """
    user = await auth_service.get_current_user_from_token(auth.credentials)
    return user


@router.post("/telegram-login", response_model=TokenResponse)
async def telegram_login(
    init_data: str = Body(..., description="Строка initData из Telegram Web App"),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Авторизация через Telegram Mini App.
    
    Принимает строку initData из Telegram Web App, проверяет подпись и возвращает JWT-токен.
    """
    return await auth_service.authenticate_telegram_user(init_data)


@router.post("/telegram-login-debug", response_model=dict)
async def telegram_login_debug(
    init_data: str = Body(..., description="Строка initData из Telegram Web App для отладки")
):
    """
    Отладочный эндпоинт для авторизации через Telegram Mini App.
    
    Принимает строку initData из Telegram Web App и возвращает декодированные данные без проверки подписи.
    Используйте только для отладки!
    """
    try:
        # Декодируем URL-encoded строку
        init_data_segments = urllib.parse.unquote(init_data).split("&")
        init_data_dict = {}

        for segment in init_data_segments:
            key, value = segment.split("=", 1)
            init_data_dict[key] = value
            
        # Если есть user, декодируем его из JSON
        if "user" in init_data_dict and init_data_dict["user"]:
            init_data_dict["user"] = json.loads(init_data_dict["user"])
            
        return {
            "decoded_data": init_data_dict,
            "message": "Это отладочный эндпоинт. Не используйте его в продакшене!"
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Ошибка при декодировании данных"
        }


@router.get("/me", response_model=UserResponse)
async def get_user_profile(
    current_user: Annotated[UserResponse, Depends(get_current_user)]
):
    """
    Получение профиля текущего пользователя.
    
    Требует авторизации через JWT-токен.
    """
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_user_profile(
    profile: UserProfile,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Обновление профиля текущего пользователя.
    
    Требует авторизации через JWT-токен.
    """
    updated_user = await auth_service.update_user_profile(
        user=current_user,
        phone=profile.phone,
        delivery_address=profile.delivery_address
    )
    return updated_user


@router.post(
    "/test-login", 
    response_model=TokenResponse,
    responses={
        200: {
            "description": "Успешная авторизация",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "token_type": "bearer",
                        "user": {
                            "id": "123456789",
                            "first_name": "Иван",
                            "last_name": "Иванов",
                            "tg_name": "ivanov",
                            "role": "user",
                            "is_admin": False,
                            "phone": None,
                            "default_delivery_address": None,
                            "language_code": None
                        }
                    }
                }
            }
        }
    }
)
async def test_login(
    user_id: str = Form(..., description="ID пользователя в Telegram"),
    first_name: str = Form(..., description="Имя пользователя"),
    last_name: str = Form(None, description="Фамилия пользователя (опционально)"),
    tg_name: str = Form(..., description="Username пользователя в Telegram"),
    is_admin: bool = Form(False, description="Является ли пользователь администратором"),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Тестовая авторизация для Swagger UI.
    
    Создает тестового пользователя и возвращает JWT-токен.
    Используйте только для отладки!
    """
    # Создаем тестового пользователя
    user = await auth_service.create_test_user(
        user_id=user_id,
        first_name=first_name,
        last_name=last_name,
        tg_name=tg_name,
        is_admin=is_admin
    )
    
    # Создаем JWT-токен
    access_token = auth_service.create_access_token({"sub": str(user.id)})
    
    # Формируем ответ
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.from_orm(user)
    )


async def check_admin_access(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
) -> UserResponse:
    """
    Проверка доступа администратора по API ключу.
    
    Используется для защиты API маршрутов, которые вызываются из Telegram бота.
    Проверяет наличие API ключа в заголовке X-API-Key и сравнивает его с ключом из настроек.
    
    Args:
        request: Объект запроса
        auth_service: Сервис авторизации
        
    Returns:
        UserResponse: Объект пользователя-администратора
        
    Raises:
        HTTPException: Если API ключ отсутствует или неверный
    """
    api_key = request.headers.get("X-API-Key")
    if not api_key or api_key != settings.BOT_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для выполнения операции"
        )
    
    # Получаем пользователя-администратора (можно использовать фиксированный ID)
    # В реальном приложении здесь можно было бы получать ID администратора из настроек
    admin_id = settings.ADMIN_USER_ID
    admin = await auth_service.get_current_user(admin_id)
    
    if not admin.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Пользователь не является администратором"
        )
    
    return admin


@router.get("/users/by-username", response_model=UserResponse)
async def get_user_by_username(
    username: str,
    auth_service: AuthService = Depends(get_auth_service),
    admin: UserResponse = Depends(check_admin_access)
):
    """
    Получение информации о пользователе по имени пользователя в Telegram.
    
    Только для администраторов. Требует API-ключ в заголовке X-API-Key.
    """
    # Получаем пользователя по имени пользователя
    user = await auth_service.get_user_by_username(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Пользователь с именем {username} не найден."
        )
    
    return user
