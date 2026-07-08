import asyncio
import os
import aiosqlite

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

DB_NAME = "videos.db"

async def create_database():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT UNIQUE,
                message_id INTEGER,
                file_id TEXT
            )
        """)
        await db.commit()

async def save_video(keyword, message_id, file_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            INSERT OR REPLACE INTO videos
            (keyword, message_id, file_id)
            VALUES (?, ?, ?)
            """,
            (keyword, message_id, file_id)
        )
        await db.commit()

@dp.channel_post(F.video)
async def new_video(message: Message):

    if not message.caption:
        print("Caption নেই!")
        return

    keyword = message.caption.strip().lower()

    await save_video(
        keyword,
        message.message_id,
        message.video.file_id
    )

    print(f"Saved: {keyword}")       

async def get_video(keyword):
    async with aiosqlite.connect(DB_NAME) as db:

        cursor = await db.execute(
            """
            SELECT file_id
            FROM videos
            WHERE keyword = ?
            """,
            (keyword,)
        )

        row = await cursor.fetchone()

        if row:
            return row[0]

        return None

@dp.message(CommandStart())
async def start_command(message: Message):
    await message.answer(
        "🎬 Welcome to Kiara Video Bot!\n\n"
        "📌 Copy the exact video name from the channel and send it here.\n\n"
        "The video will be delivered instantly."
    )

@dp.message(F.text)
async def send_video(message: Message):
    keyword = message.text.strip().lower()

    file_id = await get_video(keyword)

    if file_id is None:
        await message.answer(
            "❌ No matching video was found.\n\n"
            "Please go to the channel, copy the exact video name, and paste it here."
        )
        return

    await message.answer_video(file_id)

async def main():
    await create_database()

    me = await bot.get_me()
    print(f"Bot Connected Successfully!")
    print(f"Bot Name: {me.full_name}")
    print(f"Username: @{me.username}")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())