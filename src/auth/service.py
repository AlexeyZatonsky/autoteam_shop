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
            # Декодируем данные из Telegram
            init_data = self.decode_init_data(init_data_raw)
            
            # Проверяем подпись (используем либо hash, либо signature)
            signature = init_data.signature or init_data.hash
            self.validate_telegram_data(init_data_raw, signature)
            
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

        try:
            user_dict = json.loads(init_data_dict["user"])
            # Обработка пустой строки в last_name
            if "last_name" in user_dict and user_dict["last_name"] == "":
                user_dict["last_name"] = None
                
            user = TelegramUser(
                id=user_dict.get("id"),
                first_name=user_dict.get("first_name"),
                last_name=user_dict.get("last_name"),
                username=user_dict.get("username"),
                language_code=user_dict.get("language_code"),
                is_premium=user_dict.get("is_premium", False),
                allows_write_to_pm=user_dict.get("allows_write_to_pm", False),
                photo_url=user_dict.get("photo_url")
            )
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid JSON in user data: {str(e)}"
            )
        
        # Преобразуем auth_date из строки в целое число
        try:
            auth_date = int(init_data_dict.get("auth_date", 0))
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid auth_date format"
            )

        return InitData(
            query_id=init_data_dict.get("query_id"),
            user=user,
            receiver=init_data_dict.get("receiver"),
            chat=init_data_dict.get("chat"),
            chat_type=init_data_dict.get("chat_type"),
            chat_instance=init_data_dict.get("chat_instance"),
            start_param=init_data_dict.get("start_param"),
            can_send_after=init_data_dict.get("can_send_after"),
            auth_date=auth_date,
            signature=init_data_dict.get("signature"),
            hash=init_data_dict.get("hash")
        )
    
    def validate_telegram_data(self, init_data_raw: str, received_hash: str | None = None) -> bool:
        """
        Проверяет подпись данных из Telegram
        
        Args:
            init_data_raw: URL-encoded строка initData из Telegram Web App
            received_hash: Хеш или подпись, полученные из данных Telegram
            
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
        
        # Удаляем хеш и подпись из списка
        hash_pair = next((pair for pair in init_data_pairs if pair.startswith("hash=")), None)
        signature_pair = next((pair for pair in init_data_pairs if pair.startswith("signature=")), None)
        
        if hash_pair:
            init_data_pairs.remove(hash_pair)
        if signature_pair:
            init_data_pairs.remove(signature_pair)
            received_hash = signature_pair.split("=")[1]  # Используем подпись вместо хеша
            
        if not received_hash:
            raise HTTPException(status_code=401, detail="No hash or signature provided")
            
        data_check_string = "\n".join(sorted(init_data_pairs))

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
    
    # async def create_test_user(
    #     self,
    #     user_id: str,
    #     first_name: str,
    #     last_name: str | None = None,
    #     tg_name: str | None = None,
    #     is_admin: bool = False
    # ) -> Users:
    #     """
    #     Создает тестового пользователя для отладки
        
    #     Args:
    #         user_id: ID пользователя
    #         first_name: Имя пользователя
    #         last_name: Фамилия пользователя (опционально)
    #         tg_name: Имя пользователя в Telegram (опционально)
    #         is_admin: Является ли пользователь администратором
            
    #     Returns:
    #         Users: Созданный объект пользователя
    #     """
    #     # Проверяем, существует ли пользователь
    #     user = await self.session.get(Users, user_id)
        
    #     if user:
    #         # Обновляем существующего пользователя
    #         user.first_name = first_name
    #         if last_name is not None:
    #             user.last_name = last_name
    #         if tg_name is not None:
    #             user.tg_name = tg_name
    #         if is_admin:
    #             user.role = UserRole.ADMIN
    #     else:
    #         # Создаем нового пользователя
    #         user = Users(
    #             id=user_id,
    #             first_name=first_name,
    #             last_name=last_name,
    #             tg_name=tg_name or first_name,
    #             role=UserRole.ADMIN if is_admin else UserRole.USER
    #         )
    #         self.session.add(user)
        
    #     await self.session.commit()
    #     await self.session.refresh(user)
        
    #     return user

    async def get_user_by_username(self, username: str) -> Optional[UserResponse]:
        """
        Получает пользователя по имени пользователя в Telegram
        
        Args:
            username: Имя пользователя в Telegram (без @)
            
        Returns:
            Optional[UserResponse]: Объект пользователя или None, если пользователь не найден
        """
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        
        # Выполняем запрос к базе данных
        query = select(Users).where(Users.tg_name == username)
        result = await self.session.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        
        # Получаем статистику заказов пользователя
        from sqlalchemy import func, select
        from ..orders.models import Order
        
        # Получаем количество заказов
        orders_count_query = select(func.count(Order.id)).where(Order.user_id == user.id)
        orders_count_result = await self.session.execute(orders_count_query)
        orders_count = orders_count_result.scalar_one() or 0
        
        # Получаем общую сумму заказов
        total_spent_query = select(func.sum(Order.total_amount)).where(Order.user_id == user.id)
        total_spent_result = await self.session.execute(total_spent_query)
        total_spent = total_spent_result.scalar_one() or 0
        
        # Создаем объект ответа
        user_response = UserResponse.model_validate(user)
        
        # Добавляем статистику заказов
        user_response_dict = user_response.model_dump()
        user_response_dict["orders_count"] = orders_count
        user_response_dict["total_spent"] = float(total_spent)
        
        return UserResponse.model_validate(user_response_dict)
