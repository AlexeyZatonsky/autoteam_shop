from aiogram.fsm.state import State, StatesGroup


class ProductStates(StatesGroup):
    """Состояния для работы с продуктами"""
    
    # Состояния для создания продукта
    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_category = State()
    waiting_for_price = State()
    waiting_for_photo = State()
    
    # Состояния для редактирования
    editing_name = State()
    editing_description = State()
    editing_price = State()
    editing_photos = State()
    editing_categories = State()
    
    # Состояния для поиска
    waiting_for_search = State()