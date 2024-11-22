from aiogram.dispatcher.filters.state import State, StatesGroup

class UserState(StatesGroup):
    send_music = State()