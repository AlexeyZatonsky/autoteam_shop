from aiogram.fsm.state import State, StatesGroup


class OrderStates(StatesGroup):
    """Состояния для управления заказами"""
    # Поиск заказов
    waiting_for_order_id = State()
    waiting_for_username = State()
    waiting_for_date_range = State()
    
    # Изменение заказа
    waiting_for_status = State()
    waiting_for_payment_status = State()
    waiting_for_comment = State()
    
    # Подтверждения
    waiting_for_cancel_confirmation = State()
    waiting_for_delete_confirmation = State()
    waiting_for_delete_completed_confirmation = State() 