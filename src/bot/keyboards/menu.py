from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_main_menu() -> InlineKeyboardMarkup:
    """Основное меню бота (админ-панель)"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📦 Управление товарами", callback_data="menu:products")
            ],
            [
                InlineKeyboardButton(text="📁 Управление категориями", callback_data="category:manage")
            ],
            [
                InlineKeyboardButton(text="📋 Управление заказами", callback_data="order:manage")
            ]
        ]
    )


def get_products_menu() -> InlineKeyboardMarkup:
    """Меню управления товарами"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📦 Добавить продукт", callback_data="product:create")
            ],
            [
                InlineKeyboardButton(text="🗑 Удалить продукт", callback_data="product:delete")
            ],
            [
                InlineKeyboardButton(text="📋 Выгрузить список продуктов", callback_data="product:list")
            ],
            [
                InlineKeyboardButton(text="🔙 Назад", callback_data="menu:main")
            ]
        ]
    ) 