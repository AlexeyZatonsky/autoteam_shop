import base64
import hashlib
import hmac
import json
import urllib.parse
import time
from typing import Optional, Dict
from datetime import datetime, timedelta, UTC

from fastapi import HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from .models import Users, UserRole
from .schemas import TelegramUser, InitData, UserProfile, UserResponse, TokenResponse
from ..settings.config import settings


class AuthService:
    """
    Сервис авторизации
    
    Отвечает за:
    - Декодирование и валидацию данных из Telegram Mini App
    - Создание и проверку JWT-токенов
    - Управление пользователями (создание, получение, обновление)
    """
    
    def __init__(self, session: AsyncSession):
        """
        Инициализация сервиса авторизации
        
        Args:
            session: Асинхронная сессия SQLAlchemy
        """
        self.session = session
        self.bot_token = settings.TG_BOT_TOKEN
        self.init_data = None
    
    async def get_or_create_user(self, telegram_data: InitData) -> Users:
        """
        Получает существующего пользователя или создает нового из данных Telegram
        
        Args:
            telegram_data: Данные инициализации из Telegram
            
        Returns:
            Users: Объект пользователя
        """
        user = await self.session.get(Users, str(telegram_data.user.id))
        
        if not user:
            user = Users(
                id=str(telegram_data.user.id),
                first_name=telegram_data.user.first_name,
                last_name=telegram_data.user.last_name,
                tg_name=telegram_data.user.username or telegram_data.user.first_name,
                language_code=telegram_data.user.language_code
            )
            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)
        
        return user
    
    @staticmethod
    def create_access_token(data: dict) -> str:
        """
        Создает JWT-токен
        
        Args:
            data: Данные для включения в токен
            
        Returns:
            str: JWT-токен
        """
        to_encode = data.copy()
        expire = datetime.now(UTC) + timedelta(days=7)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_AUTH, algorithm="HS256")
        return encoded_jwt
    
    async def authenticate_telegram_user(self, init_data_raw: str) -> TokenResponse:
        """
        Аутентифицирует пользователя по данным из Telegram
        
        Args:
            init_data_raw: URL-encoded строка initData из Telegram Web App
            
        Returns:
            TokenResponse: Ответ с токеном и данными пользователя
            
        Raises:
            HTTPException: Если аутентификация не удалась
        """
        try:
            # Декодируем и проверяем данные из Telegram
            init_data = self.decode_init_data(init_data_raw)
            
            # Проверяем подпись
            self.validate_telegram_data(init_data_raw, init_data.hash)
            
            # Получаем или создаем пользователя
            user = await self.get_or_create_user(init_data)
            
            # Создаем JWT-токен
            access_token = self.create_access_token({"sub": str(user.id)})
            
            # Формируем ответ
            return TokenResponse(
                access_token=access_token,
                token_type="bearer",
                user=UserResponse.from_orm(user)
            )
        except HTTPException as e:
            # Пробрасываем HTTP-исключения как есть
            raise e
        except json.JSONDecodeError:
            # Ошибка при декодировании JSON
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON in Telegram data"
            )
        except ValueError as e:
            # Ошибки преобразования типов
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid data format: {str(e)}"
            )
        except Exception as e:
            # Прочие ошибки
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Authentication failed: {str(e)}"
            )
    
    @staticmethod
    def decode_init_data(init_data_raw: str) -> InitData:
        """
        Декодирует данные инициализации из Telegram
        
        Args:
            init_data_raw: URL-encoded строка initData из Telegram Web App
            
        Returns:
            InitData: Декодированные данные
            
        Raises:
            HTTPException: Если данные некорректны
        """
        init_data_segments = urllib.parse.unquote(init_data_raw).split("&")
        init_data_dict = {}

        for segment in init_data_segments:
            key, value = segment.split("=", 1)
            init_data_dict[key] = value

        if "user" not in init_data_dict or init_data_dict["user"] == "":
            raise HTTPException(status_code=401, detail="User is required")

        user_dict = json.loads(init_data_dict["user"])
        user = TelegramUser(
            id=user_dict.get("id"),
            first_name=user_dict.get("first_name"),
            last_name=user_dict.get("last_name", None),
            username=user_dict.get("username", None),
            language_code=user_dict.get("language_code", None),
            added_to_attachment_menu=user_dict.get("added_to_attachment_menu", False),
            allows_write_to_pm=user_dict.get("allows_write_to_pm", False),
            is_premium=user_dict.get("is_premium", False),
            photo_url=user_dict.get("photo_url", None)
        )
        
        # Преобразуем auth_date из строки в целое число
        auth_date = int(init_data_dict.get("auth_date")) if init_data_dict.get("auth_date") else None

        return InitData(
            query_id=init_data_dict.get("query_id"),
            user=user,
            receiver=init_data_dict.get("receiver", None),
            chat=init_data_dict.get("chat", None),
            chat_type=init_data_dict.get("chat_type", None),
            chat_instance=init_data_dict.get("chat_instance", None),
            start_param=init_data_dict.get("start_param", None),
            can_send_after=init_data_dict.get("can_send_after", None),
            auth_date=auth_date,
            hash=init_data_dict.get("hash")
        )
    
    def validate_telegram_data(self, init_data_raw: str, received_hash: str) -> bool:
        """
        Проверяет подпись данных из Telegram
        
        Args:
            init_data_raw: URL-encoded строка initData из Telegram Web App
            received_hash: Хеш, полученный из данных Telegram
            
        Returns:
            bool: True, если подпись верна
            
        Raises:
            HTTPException: Если подпись неверна или данные устарели
        """
        init_data_pairs = urllib.parse.unquote(init_data_raw).split("&")
        
        # Проверка на устаревшие данные (не старше 24 часов)
        auth_date_pair = next((pair for pair in init_data_pairs if pair.startswith("auth_date=")), None)
        if auth_date_pair:
            auth_date = int(auth_date_pair.split("=")[1])
            current_time = int(time.time())
            if current_time - auth_date > 86400:  # 24 часа в секундах
                raise HTTPException(status_code=401, detail="Authorization data is expired")
        
        # Удаляем хеш из списка, так как мы не можем проверить хеш хеша
        hash_pair = next((pair for pair in init_data_pairs if pair.startswith("hash=")), None)
        if hash_pair:
            init_data_pairs.remove(hash_pair)
        data_check_string = "\n".join(sorted(init_data_pairs))  # Сортируем для обеспечения одинакового порядка ключей

        secret_key = hmac.new(b"WebAppData", self.bot_token.encode(), hashlib.sha256).digest()
        data_signature = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

        if not hmac.compare_digest(received_hash, data_signature):
            raise HTTPException(status_code=401, detail="Invalid Telegram data signature")
        
        return True
    
    async def get_current_user(self, user_id: str) -> Users:
        """
        Получает пользователя по ID
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Users: Объект пользователя
            
        Raises:
            HTTPException: Если пользователь не найден
        """
        user = await self.session.get(Users, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
    
    async def get_current_user_from_token(self, token: str) -> Users:
        """
        Получает текущего пользователя из JWT-токена
        
        Args:
            token: JWT-токен
            
        Returns:
            Users: Объект пользователя
            
        Raises:
            HTTPException: Если токен недействителен или пользователь не найден
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, settings.SECRET_AUTH, algorithms=["HS256"])
            user_id = payload.get("sub")
            if user_id is None:
                raise credentials_exception
        except (JWTError, AttributeError):
            raise credentials_exception
            
        return await self.get_current_user(user_id)
    
    async def update_user_profile(
        self,
        user: Users,
        phone: str | None = None,
        delivery_address: str | None = None
    ) -> Users:
        """
        Обновляет профиль пользователя
        
        Args:
            user: Объект пользователя
            phone: Новый телефон (опционально)
            delivery_address: Новый адрес доставки (опционально)
            
        Returns:
            Users: Обновленный объект пользователя
        """
        if phone is not None:
            user.phone = phone
        if delivery_address is not None:
            user.default_delivery_address = delivery_address
        
        await self.session.commit()
        await self.session.refresh(user)
        return user
    
    async def create_test_user(
        self,
        user_id: str,
        first_name: str,
        last_name: str | None = None,
        tg_name: str | None = None,
        is_admin: bool = False
    ) -> Users:
        """
        Создает тестового пользователя для отладки
        
        Args:
            user_id: ID пользователя
            first_name: Имя пользователя
            last_name: Фамилия пользователя (опционально)
            tg_name: Имя пользователя в Telegram (опционально)
            is_admin: Является ли пользователь администратором
            
        Returns:
            Users: Созданный объект пользователя
        """
        # Проверяем, существует ли пользователь
        user = await self.session.get(Users, user_id)
        
        if user:
            # Обновляем существующего пользователя
            user.first_name = first_name
            if last_name is not None:
                user.last_name = last_name
            if tg_name is not None:
                user.tg_name = tg_name
            if is_admin:
                user.role = UserRole.ADMIN
        else:
            # Создаем нового пользователя
            user = Users(
                id=user_id,
                first_name=first_name,
                last_name=last_name,
                tg_name=tg_name or first_name,
                role=UserRole.ADMIN if is_admin else UserRole.USER
            )
            self.session.add(user)
        
        await self.session.commit()
        await self.session.refresh(user)
        
        return user
