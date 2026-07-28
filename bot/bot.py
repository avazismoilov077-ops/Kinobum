import asyncio
import threading
import os
from dotenv import load_dotenv

load_dotenv()

from flask import Flask
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN, FLASK_PORT
from database import init_db, async_session
from handlers import get_main_router
from middlewares import SubscriptionMiddleware, LoggingMiddleware
from utils.logger import logger

# ─── Flask (health check) ──────────────────────────────────────────────────────

flask_app = Flask(__name__)

@flask_app.route("/health")
def health():
    return "Bot is running", 200

@flask_app.route("/")
def index():
    return "🎬 Kino Bot is alive!", 200

def run_flask():
    flask_app.run(host="0.0.0.0", port=FLASK_PORT, debug=False, use_reloader=False)


# ─── Aiogram ───────────────────────────────────────────────────────────────────

async def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN topilmadi! .env faylini tekshiring.")
        return

    # Database init
    await init_db()
    logger.info("Database tayyor ✅")

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Middleware
    dp.message.middleware(LoggingMiddleware())
    dp.message.middleware(SubscriptionMiddleware())

    # Session middleware
    @dp.update.middleware()
    async def session_middleware(handler, event, data):
        async with async_session() as session:
            data["session"] = session
            return await handler(event, data)

    # Routerlarni ulash
    dp.include_router(get_main_router())

    logger.info("Bot ishga tushmoqda... 🚀")

    # Flask ni alohida thread da ishlatish
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info(f"Flask server port {FLASK_PORT} da ishga tushdi ✅")

    # Bot polling
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()
        logger.info("Bot to'xtatildi.")


if __name__ == "__main__":
    asyncio.run(main())
