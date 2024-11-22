from aiogram.dispatcher.filters.state import State, StatesGroup

class UserState(StatesGroup):
    choose_button = State()
    search_to_txt = State()
    search_name = State()

