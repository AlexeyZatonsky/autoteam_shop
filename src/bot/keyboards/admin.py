from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура администратора"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📦 Управление товарами", callback_data="menu:products"),
                InlineKeyboardButton(text="📁 Управление категориями", callback_data="menu:categories")
            ],
            [
                InlineKeyboardButton(text="📋 Управление заказами", callback_data="menu:orders")
            ]
        ]
    ) 