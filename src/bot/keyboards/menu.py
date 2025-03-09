from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_main_menu() -> InlineKeyboardMarkup:
    """Основное меню бота (админ-панель)"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📦 Добавить продукт", callback_data="product:add")
            ],
            [
                InlineKeyboardButton(text="🗑 Удалить продукт", callback_data="product:delete")
            ],
            [
                InlineKeyboardButton(text="📋 Выгрузить список продуктов", callback_data="product:list")
            ],
            [
                InlineKeyboardButton(text="📥 Выгрузить список заказов", callback_data="order:list")
            ],
            [
                InlineKeyboardButton(text="🔍 Получить заказ по ID", callback_data="order:get_by_id")
            ],
            [
                InlineKeyboardButton(text="👤 Получить заказы по user_id", callback_data="order:get_by_user")
            ],
            [
                InlineKeyboardButton(text="✏️ Изменить статус заказа", callback_data="order:change_status")
            ],
            [
                InlineKeyboardButton(text="📁 Управление категориями", callback_data="category:manage")
            ]
        ]
    ) 