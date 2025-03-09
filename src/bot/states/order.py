from aiogram.fsm.state import State, StatesGroup


class OrderStates(StatesGroup):
    """Состояния для управления заказами"""
    waiting_for_order_id = State()
    waiting_for_user_id = State()
    waiting_for_status = State()
    waiting_for_comment = State()
    waiting_for_cancel_confirmation = State() 