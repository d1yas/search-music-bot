import logging
import os
import zipfile
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.types import Message
from aiogram.utils import executor
from yt_dlp import YoutubeDL
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware

from keyboard.default.buttons import choose_button
from state import UserState
from aiogram.types import ReplyKeyboardMarkup,KeyboardButton

storage = MemoryStorage()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

bot = Bot(token='7846426508:AAGyv47GaBX2p85RqCpBjaDhDvfJTAD2KRU')
dp = Dispatcher(bot,storage=storage)

SAVE_FOLDER = "downloaded_music"
if not os.path.exists(SAVE_FOLDER):
    os.makedirs(SAVE_FOLDER)

def clear_downloads():
    for foldername, subfolders, filenames in os.walk(SAVE_FOLDER):
        for filename in filenames:
            os.remove(os.path.join(foldername, filename))
            pass
        pass

@dp.message_handler(commands=['start'],state="*")
async def welcome(message: Message, state: FSMContext):
    salom = f"""
Assalomu Aleykum @{message.from_user.username}!
    """
    clear_downloads()
    await message.answer(salom,reply_markup=choose_button)
    await UserState.choose_button.set()

    # await UserState.send_music.set()

@dp.message_handler(state=UserState.choose_button)
async def choose(message: Message, state: FSMContext):
    user_message = message.text
    print(user_message)

    if user_message == "🔎 Musiqa nomi bilan qidirish.":
        await message.answer("Muzikani nomini yuboring: ")
        UserState.search_name.set()
    elif user_message == "📝 Tekstli dokumentli orqali qidirish.":
        await message.answer(
            "📝 Teksti document (.txt) tashang musiqalar nomlari bor(Har bir musiqa nomi :/ boshlanishi shart !!! )")
        UserState.search_to_txt.set()


@dp.message_handler(state=UserState.search_name)
async def search_music(message: Message, state: FSMContext):
    query = message.text
    ydl_opts = {
        'quiet': True,
        'format': 'bestaudio/best',
        'noplaylist': True
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            search_results = ydl.extract_info(f"ytsearch:{query}", download=False)

            if 'entries' in search_results and len(search_results['entries']) > 0:
                info = search_results['entries'][0]
                title = info['title']
                url = info['webpage_url']
                await message.answer(f"Topildi: {title}\nUrl: {url}")
            else:
                await message.answer("Musiqa topilmadi, nomini togilab koring")
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await message.answer("error.")


@dp.message_handler(content_types=types.ContentType.DOCUMENT)
async def handle_text_file(message: types.Message, state: FSMContext):
    if message.document.mime_type == "text/plain":
        file_id = message.document.file_id
        file = await bot.get_file(file_id)

        file_path = file.file_path
        downloaded_file = await bot.download_file(file_path)

        content = downloaded_file.read().decode("utf-8")
        lines = content.splitlines()

        found_music = []
        for line in lines:
            if line.startswith(":/"):
                music_name = line[2:].strip()
                if music_name:
                    found_music.append(music_name)

        if found_music:
            await message.reply(f"Sizning tashang .txt file dan {len(found_music)} musiqa toplidi\nHozi qidirilmoqda...")

            for music_name in found_music:
                await search_and_download_music(message, music_name)

            zip_path = await create_zip_archive()
            await send_zip(message, zip_path)
            await message.answer("Hamma Musiqalar topildi va arxiv qilinib tashlandi")

        else:
            await message.reply("Fileda ':/' yoq! ")
    else:
        await message.reply("Iltimos .txt file yuboring")
        await state.finish()


async def search_and_download_music(message: Message, query: str):
    ydl_opts = {
        'quiet': True,
        'format': 'bestaudio/best',
        'noplaylist': True,
        'outtmpl': f'{SAVE_FOLDER}/%(title)s.%(ext)s',
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            search_results = ydl.extract_info(f"ytsearch:{query}", download=True)

            if 'entries' in search_results and len(search_results['entries']) > 0:
                info = search_results['entries'][0]
                title = info['title']

                file_path = f"{SAVE_FOLDER}/{title}.{info['ext']}"
                new_file_path = file_path.rsplit('.', 1)[0] + ".mp3"

                if os.path.exists(file_path):
                    os.rename(file_path, new_file_path)

                await message.answer(f"Yuklandi: {title}.mp3")
            else:
                await message.reply(f"Musiqa topilmadi: {query}")
    except Exception as e:
        logger.error(f"Musiqa yuklashda hato  '{query}': {e}")
        await message.answer(f"Musiqa yuklashda hato : {query}")

async def create_zip_archive():
    zip_filename = f"{SAVE_FOLDER}.zip"
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for foldername, subfolders, filenames in os.walk(SAVE_FOLDER):
            for filename in filenames:
                file_path = os.path.join(foldername, filename)
                zipf.write(file_path, os.path.relpath(file_path, SAVE_FOLDER))
    return zip_filename

async def send_zip(message: Message, zip_path: str):
    with open(zip_path, "rb") as zip_file:
        await message.answer_document(zip_file)



@dp.message_handler(commands="music")
async def one_music(message: Message):
    try:
        with open("downloaded_music/Mr Lambo - Mango (Official Video).mp3", "rb") as audio_file:
            await message.answer_audio(audio=audio_file)
    except FileNotFoundError:
        await message.answer("File Topilmadi.")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
