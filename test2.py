import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import InputFile
from aiogram.utils import executor
from yt_dlp import YoutubeDL
from config import API_TOKEN


bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

def download_audio(query: str) -> str:
    save_path = "downloads"
    if not os.path.exists(save_path):
        os.makedirs(save_path)

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": f"{save_path}/%(title)s.%(ext)s",
        "prefer_ffmpeg": False,
        "postprocessor_args": [],
        "final_ext": "mp3",
    }

    with YoutubeDL(ydl_opts) as ydl:
        result = ydl.extract_info(f"ytsearch:{query}", download=True)
        if "entries" in result:
            result = result["entries"][0]
        downloaded_path = ydl.prepare_filename(result)
        mp3_path = downloaded_path.rsplit(".", 1)[0] + ".mp3"
        os.rename(downloaded_path, mp3_path)
        return mp3_path


@dp.message_handler(commands=["start"])
async def start_command(message: types.Message):
    await message.reply("Salom! Menga qo'shiq nomini yuboring men sizga topib beraman 🎵")

@dp.message_handler()
async def search_and_send_audio(message: types.Message):
    query = message.text.strip()
    await message.reply("🔍 Men musiqa qidiryapman, biroz kuting...")

    try:
        audio_path = download_audio(query)
        await message.reply("🎶 Topdim! Yuborilmoqda...")
        audio_file = InputFile(audio_path)
        await bot.send_audio(chat_id=message.chat.id, audio=audio_file)
        os.remove(audio_path)
    except Exception as e:
        await message.reply(f"❌ Musiqani topilmadi yoki yuklab boʻlmadi: {e}")


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
