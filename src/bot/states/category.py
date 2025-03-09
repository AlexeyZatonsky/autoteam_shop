from aiogram.fsm.state import State, StatesGroup


class CategoryStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_delete_confirmation = State() 