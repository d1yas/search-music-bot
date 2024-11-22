from aiogram.types import ReplyKeyboardMarkup,KeyboardButton

choose_button = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🔎 Musiqa nomi bilan qidirish.")
        ],
        [
            KeyboardButton(text="📝 Tekstli dokumentli orqali qidirish.")
        ]
    ], resize_keyboard=True
)