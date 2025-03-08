from aiogram.fsm.state import State, StatesGroup


class CategoryStates(StatesGroup):
    """Состояния для создания категории"""
    waiting_for_name = State()
    waiting_for_delete_confirmation = State()


class ProductStates(StatesGroup):
    """Состояния для создания продукта"""
    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_price = State()
    waiting_for_categories = State()
    waiting_for_images = State()


class OrderStates(StatesGroup):
    """Состояния для работы с заказами"""
    waiting_for_order_id = State()
    waiting_for_user_id = State()
    waiting_for_status = State() 