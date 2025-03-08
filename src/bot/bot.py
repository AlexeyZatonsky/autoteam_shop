from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
import asyncio

from ..settings.config import settings
from .keyboards import get_main_menu
from .api_client import APIClient
from .handlers.category import router as category_router
from .handlers.product import router as product_router
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
        self.dp.callback_query.register(self.menu_callback_handler, lambda c: c.data.startswith("menu:"))

        # Регистрируем роутеры
        self.dp.include_router(category_router)
        self.dp.include_router(product_router)
        self.dp.include_router(order_router)

        # Добавляем middleware для проверки админа
        self.dp.message.middleware(self.admin_middleware)
        self.dp.callback_query.middleware(self.admin_middleware)

        # Внедряем API клиент
        self.dp["api_client"] = self.api_client

    async def admin_middleware(self, handler, event, data):
        """Middleware для проверки прав администратора"""
        user_id = event.from_user.id
        if user_id not in settings.admin_ids:
            if isinstance(event, types.CallbackQuery):
                await event.answer("У вас нет доступа к этой команде.", show_alert=True)
            else:
                await event.answer("У вас нет доступа к этой команде.")
            return
        return await handler(event, data)

    async def start_handler(self, message: types.Message):
        """Обработчик команды /start"""
        await message.answer(
            "Админ-меню:",
            reply_markup=get_main_menu()
        )

    async def menu_callback_handler(self, callback: types.CallbackQuery):
        """Обработчик возврата в главное меню"""
        await callback.message.edit_text(
            "Админ-меню:",
            reply_markup=get_main_menu()
        )
        await callback.answer()

    async def start(self):
        """Запуск бота"""
        await self.dp.start_polling(self.bot)


def run_bot():
    """Функция для запуска бота"""
    bot = AutoteamBot()
    asyncio.run(bot.start()) 