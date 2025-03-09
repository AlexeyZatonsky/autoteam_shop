from aiogram.fsm.state import State, StatesGroup


class ProductStates(StatesGroup):
    """Состояния для управления продуктами"""
    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_category = State()
    waiting_for_price = State()
    waiting_for_photo = State()
    waiting_for_images = State()
    waiting_for_categories = State()
    waiting_for_delete_confirmation = State() 