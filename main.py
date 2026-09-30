import asyncio, logging, os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand
from database.db import init_db
from handlers.user import router as user_router
from handlers.admin import router as admin_router

load_dotenv()
TOKEN=os.getenv("BOT_TOKEN")
if not TOKEN: raise RuntimeError("BOT_TOKEN .env faylda yo'q.")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[logging.FileHandler("bot.log",encoding="utf-8"),logging.StreamHandler()]
)

async def main():
    await init_db()
    bot=Bot(TOKEN,default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp=Dispatcher()
    dp.include_router(admin_router)
    dp.include_router(user_router)
    await bot.set_my_commands([
        BotCommand(command="start",description="Bosh menyu"),
        BotCommand(command="search",description="Kitob qidirish"),
        BotCommand(command="admin",description="Admin panel"),
        BotCommand(command="add_book",description="Kitob qo'shish"),
        BotCommand(command="edit_book",description="Kitob tahrirlash"),
    ])
    await dp.start_polling(bot)

if __name__=="__main__":
    asyncio.run(main())
