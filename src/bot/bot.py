from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
import aiohttp
import asyncio
from typing import Any, Dict

from ..settings.config import settings


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

    async def is_admin(self, user_id: int) -> bool:
        """Проверка, является ли пользователь админом"""
        return user_id in settings.admin_ids

    async def start_handler(self, message: types.Message):
        """Обработчик команды /start"""
        if not await self.is_admin(message.from_user.id):
            await message.answer("У вас нет доступа к этой команде.")
            return

        builder = InlineKeyboardBuilder()
        # Управление продуктами
        builder.button(text="Добавить продукт", callback_data="product:add")
        builder.button(text="Удалить продукт", callback_data="product:delete")
        builder.button(text="Выгрузить список продуктов", callback_data="product:list")
        
        # Управление заказами
        builder.button(text="Выгрузить список заказов", callback_data="order:list")
        builder.button(text="Получить заказ по ID", callback_data="order:get_by_id")
        builder.button(text="Получить заказы по user_id", callback_data="order:get_by_user")
        builder.button(text="Изменить статус заказа", callback_data="order:change_status")
        
        # Управление категориями
        builder.button(text="Выгрузить список категорий", callback_data="category:list")
        builder.button(text="Добавить категорию", callback_data="category:add")
        
        # Настройка отображения кнопок (по одной в ряд)
        builder.adjust(1)
        
        await message.answer(
            "Админ-меню:",
            reply_markup=builder.as_markup()
        )

    async def callback_handler(self, callback: types.CallbackQuery):
        """Обработчик callback-запросов"""
        if not await self.is_admin(callback.from_user.id):
            await callback.answer("Нет доступа", show_alert=True)
            return

        action, operation = callback.data.split(":")
        
        if action == "product":
            if operation == "add":
                await callback.message.answer(
                    "Отправьте данные продукта в формате: Имя, Описание, Цена, Категория ID"
                )
            elif operation == "delete":
                await callback.message.answer("Отправьте ID продукта для удаления")
            elif operation == "list":
                await self.handle_products_list(callback)
                
        elif action == "order":
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
                
        elif action == "category":
            if operation == "list":
                await self.handle_categories_list(callback)
            elif operation == "add":
                await callback.message.answer("Отправьте название новой категории")

        await callback.answer()

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

    async def handle_categories_list(self, callback: types.CallbackQuery):
        """Обработка запроса списка категорий"""
        try:
            categories = await self.make_request("GET", "/api/categories/")
            text = "📁 Список категорий:\n\n"
            
            for category in categories:
                text += f"• {category['name']} (ID: {category['id']})\n"
            
            await callback.message.answer(text)
        except Exception as e:
            await callback.message.answer(f"❌ Ошибка при получении списка категорий: {str(e)}")

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