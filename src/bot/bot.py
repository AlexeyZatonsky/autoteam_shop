from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, StateFilter
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import aiohttp
import asyncio
from typing import Any, Dict

from ..settings.config import settings
from .states import CategoryStates
from .keyboards import get_main_menu
from .handlers.category import handle_category_action, process_category_name


class AutoteamBot:
    def __init__(self):
        self.bot = Bot(token=settings.TG_BOT_TOKEN)
        self.dp = Dispatcher()
        self.api_url = settings.API_URL
        self.setup_handlers()

    def setup_handlers(self):
        """Настройка обработчиков команд бота"""
        self.dp.message.register(self.start_handler, Command("start"))
        self.dp.callback_query.register(self.callback_handler)
        # Регистрируем обработчик для создания категории
        self.dp.message.register(
            self.process_category_name,
            StateFilter(CategoryStates.waiting_for_name)
        )

    async def is_admin(self, user_id: int) -> bool:
        """Проверка, является ли пользователь админом"""
        return user_id in settings.admin_ids

    async def get_categories_keyboard(self) -> types.InlineKeyboardMarkup:
        """Получение клавиатуры со списком категорий"""
        categories = await self.make_request("GET", "/api/categories")
        builder = InlineKeyboardBuilder()
        
        for category in categories:
            builder.button(
                text=f"📁 {category['name']}", 
                callback_data=f"category:view:{category['name']}"
            )
        
        builder.button(
            text="➕ Добавить категорию",
            callback_data="category:add"
        )
        builder.adjust(1)
        return builder.as_markup()

    async def start_handler(self, message: types.Message):
        """Обработчик команды /start"""
        if not await self.is_admin(message.from_user.id):
            await message.answer("У вас нет доступа к этой команде.")
            return

        await message.answer(
            "Админ-меню:",
            reply_markup=get_main_menu()
        )

    async def handle_category_action(self, callback: types.CallbackQuery, operation: str, args: list, state: FSMContext):
        """Обработка действий с категориями"""
        if operation == "manage":
            # Показываем меню управления категориями
            builder = InlineKeyboardBuilder()
            builder.button(text="Список категорий", callback_data="category:list")
            builder.button(text="Добавить категорию", callback_data="category:add")
            builder.button(text="Назад в меню", callback_data="menu:main")
            builder.adjust(1)
            
            await callback.message.edit_text(
                "Управление категориями:",
                reply_markup=builder.as_markup()
            )
            
        elif operation == "list":
            # Получаем список категорий
            categories = await self.make_request("GET", "/api/categories")
            text = "📁 Список категорий:\n\n"
            
            for category in categories:
                text += f"• {category['name']}\n"
            
            builder = InlineKeyboardBuilder()
            builder.button(text="◀️ Назад", callback_data="category:manage")
            builder.button(text="➕ Добавить категорию", callback_data="category:add")
            
            await callback.message.edit_text(
                text,
                reply_markup=builder.as_markup()
            )
            
        elif operation == "add":
            # Устанавливаем состояние ожидания имени категории
            await state.set_state(CategoryStates.waiting_for_name)
            builder = InlineKeyboardBuilder()
            builder.button(text="❌ Отмена", callback_data="category:cancel")
            
            await callback.message.edit_text(
                "Отправьте название новой категории:",
                reply_markup=builder.as_markup()
            )
            
        elif operation == "cancel":
            # Отмена создания категории
            await state.clear()
            await self.handle_category_action(callback, "manage", [], state)
            
        elif operation == "delete":
            if not args:
                await callback.answer("Ошибка: не указано имя категории")
                return
                
            category_name = args[0]
            try:
                await self.make_request("DELETE", f"/api/categories/{category_name}")
                await callback.answer("✅ Категория успешно удалена!")
                await self.handle_category_action(callback, "list", [], state)
            except Exception as e:
                await callback.message.edit_text(
                    f"❌ Ошибка при удалении категории: {str(e)}"
                )

    async def process_category_name(self, message: types.Message, state: FSMContext):
        """Обработчик создания категории"""
        await process_category_name(message, state, self.make_request)

    async def callback_handler(self, callback: types.CallbackQuery, state: FSMContext):
        """Обработчик callback-запросов"""
        if not await self.is_admin(callback.from_user.id):
            await callback.answer("Нет доступа", show_alert=True)
            return

        action, operation, *args = callback.data.split(":")
        
        if action == "category":
            await handle_category_action(callback.message, operation, args, state, self.make_request)
        elif action == "product":
            await self.handle_product_action(callback, operation)
        elif action == "order":
            await self.handle_order_action(callback, operation)
        elif action == "menu" and operation == "main":
            await callback.message.edit_text(
                "Админ-меню:",
                reply_markup=get_main_menu()
            )

        await callback.answer()

    async def handle_product_action(self, callback: types.CallbackQuery, operation: str):
        """Обработка действий с продуктами"""
        if operation == "add":
            await callback.message.answer(
                "Отправьте данные продукта в формате: Имя, Описание, Цена, Категория ID"
            )
        elif operation == "delete":
            await callback.message.answer("Отправьте ID продукта для удаления")
        elif operation == "list":
            await self.handle_products_list(callback)

    async def handle_order_action(self, callback: types.CallbackQuery, operation: str):
        """Обработка действий с заказами"""
        if operation == "list":
            await self.handle_orders_list(callback)
        elif operation == "get_by_id":
            await callback.message.answer("Отправьте ID заказа")
        elif operation == "get_by_user":
            await callback.message.answer("Отправьте ID пользователя")
        elif operation == "change_status":
            await callback.message.answer(
                "Отправьте данные в формате: ID_заказа статус\n"
                "Например: 123 processing"
            )

    async def handle_products_list(self, callback: types.CallbackQuery):
        """Обработка запроса списка продуктов"""
        try:
            products = await self.make_request("GET", "/api/products/")
            text = "📦 Список продуктов:\n\n"
            
            for product in products:
                text += f"• {product['name']} - {product['price']}₽\n"
            
            await callback.message.answer(text)
        except Exception as e:
            await callback.message.answer(f"❌ Ошибка при получении списка продуктов: {str(e)}")

    async def handle_orders_list(self, callback: types.CallbackQuery):
        """Обработка запроса списка заказов"""
        try:
            orders = await self.make_request("GET", "/api/orders/")
            text = "📥 Список заказов:\n\n"
            
            for order in orders:
                text += (f"Заказ #{order['id']}\n"
                        f"Сумма: {order['total_amount']}₽\n"
                        f"Статус: {order['status']}\n\n")
            
            await callback.message.answer(text)
        except Exception as e:
            await callback.message.answer(f"❌ Ошибка при получении списка заказов: {str(e)}")

    async def make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Выполнение запроса к API"""
        async with aiohttp.ClientSession() as session:
            url = f"{self.api_url}{endpoint}"
            async with session.request(method, url, **kwargs) as response:
                if response.status >= 400:
                    error_text = await response.text()
                    raise Exception(f"API error: {response.status} - {error_text}")
                return await response.json()

    async def start(self):
        """Запуск бота"""
        await self.dp.start_polling(self.bot)


def run_bot():
    """Функция для запуска бота"""
    bot = AutoteamBot()
    asyncio.run(bot.start()) 