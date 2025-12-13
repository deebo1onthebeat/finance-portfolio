from aiogram.fsm.state import State, StatesGroup

class RegisterState(StatesGroup):
    waiting_for_email = State()
    waiting_for_password = State()

class LoginState(StatesGroup):
    waiting_for_email = State()
    waiting_for_password = State()

class CategoryState(StatesGroup):
    waiting_for_name = State()

class TransactionState(StatesGroup):
    waiting_for_amount = State()
    waiting_for_category = State()
    waiting_for_description = State()

class CategoryEditState(StatesGroup):
    waiting_for_new_name = State()
    waiting_for_confirmation = State()
