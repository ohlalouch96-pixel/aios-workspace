import asyncio, os, sys
from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path(__file__).resolve().parent.parent / ".env")
from aiogram import Bot

async def send(message):
    bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
    try:
        await bot.send_message(
            chat_id=int(os.getenv("TELEGRAM_GROUP_ID")),
            text=message,
        )
        print("Verstuurd!")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    msg = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Test bericht"
    asyncio.run(send(msg))
