from aiogram.dispatcher.filters.state import State, StatesGroup

class UserState(StatesGroup):
    send_music_to_txt = State()
    search_music_name = State()