from aiogram.fsm.state import State, StatesGroup


class CategoryStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_image = State()
    waiting_for_delete_confirmation = State()
    waiting_for_new_name = State()
    waiting_for_new_image = State() 