from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest
import asyncio

from ..settings.config import settings
from .keyboards.menu import get_main_menu, get_products_menu
from .api_client import APIClient
from .handlers.category import router as category_router
from .handlers import (
    product_create_router,
    product_view_router,
    product_edit_router,
    product_list_router
)
from .handlers.order import router as order_router


class AutoteamBot:
    def __init__(self):
        self.bot = Bot(token=settings.TG_BOT_TOKEN)
        self.dp = Dispatcher()
        self.api_client = APIClient(settings.API_URL)
        self.setup_handlers()

    def setup_handlers(self):
        """Настройка обработчиков команд бота"""
        # Регистрируем базовые обработчики
        self.dp.message.register(self.start_handler, Command("start"))
        self.dp.callback_query.register(self.menu_callback_handler, F.data.startswith("menu:"))

        # Регистрируем роутеры
        self.dp.include_router(category_router)
        
        # Регистрируем роутеры продуктов
        self.dp.include_router(product_create_router)
        self.dp.include_router(product_view_router)
        self.dp.include_router(product_edit_router)
        self.dp.include_router(product_list_router)
        
        self.dp.include_router(order_router)

        # Добавляем middleware для проверки админа
        self.dp.message.middleware(self.admin_middleware)
        self.dp.callback_query.middleware(self.admin_middleware)

        # Внедряем API клиент
        self.dp["api_client"] = self.api_client

    async def admin_middleware(self, handler, event, data):
        """Middleware для проверки прав администратора"""
        # Временно разрешаем доступ всем пользователям
        
        user_id = event.from_user.id
        if user_id not in settings.admin_ids:
            if isinstance(event, Message):
                await event.answer("У вас нет доступа к этой команде.")
            elif isinstance(event, CallbackQuery):
                await event.answer("У вас нет доступа к этой функции.", show_alert=True)
            return
        return await handler(event, data)

    async def start_handler(self, message: Message):
        """Обработчик команды /start"""
        keyboard = get_main_menu()
        await message.answer(
            "Добро пожаловать в панель администратора магазина Autoteam!",
            reply_markup=keyboard
        )

    async def menu_callback_handler(self, callback: CallbackQuery):
        """Обработчик нажатий на кнопки главного меню"""
        try:
            await callback.answer()
            action = callback.data.split(":")[1]
            
            if action == "main":
                keyboard = get_main_menu()
                await callback.message.edit_text(
                    "Админ-меню:",
                    reply_markup=keyboard
                )
            elif action == "products":
                keyboard = get_products_menu()
                await callback.message.edit_text(
                    "Управление товарами:",
                    reply_markup=keyboard
                )
        except TelegramBadRequest as e:
            if "query is too old" in str(e):
                keyboard = get_main_menu()
                await callback.message.answer(
                    "Админ-меню:",
                    reply_markup=keyboard
                )
            else:
                raise

    async def start(self):
        """Запуск бота"""
        await self.dp.start_polling(self.bot)


def run_bot():
    """Функция для запуска бота"""
    bot = AutoteamBot()
    asyncio.run(bot.start()) 