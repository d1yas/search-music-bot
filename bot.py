import logging
import os
import zipfile
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.types import Message
from aiogram.utils import executor
from yt_dlp import YoutubeDL
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from state import UserState
from aiogram.types import InputFile
from keyboard.default.buttons import choose_button
from config import API_TOKEN

storage = MemoryStorage()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

bot = Bot(token=API_TOKEN)
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

def download_audio(query: str) -> str:
    save_path = "music_name_download"
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


@dp.message_handler(commands=['start'],state="*")
async def start(message: types.Message):
    await message.reply(f"Assalomu Aleykum @{message.from_user.username}!",reply_markup=choose_button)


@dp.message_handler(text="🔎 Musiqa nomi bilan qidirish.",state="*")
async def search_to_name(message: Message, state: FSMContext):
    await message.answer("Muzika nomini yuboring! ")
    await UserState.search_music_name.set()


@dp.message_handler(text="📝 Tekstli dokumentli orqali qidirish.", state="*")
async def txt(message: Message, state: FSMContext):
    txt_search = f"""
    Teksti document (.txt) tashang musiqalar nomlari bor(Har bir musiqa nomi :/ boshlanishi shart !!! (Limit 15ta muzika bolsin) )
        """
    clear_downloads()
    await message.answer(txt_search)
    await UserState.send_music_to_txt.set()


@dp.message_handler(content_types=types.ContentType.DOCUMENT, state=UserState.send_music_to_txt)
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
        


@dp.message_handler(state=UserState.search_music_name)
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



if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
