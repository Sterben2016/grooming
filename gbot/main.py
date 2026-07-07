import asyncio
import logging

from aiohttp import web

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from gbot.config import BOT_TOKEN, PORT
from gbot.database.db import init_db
from gbot.handlers import admin, client, registration

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def handle_ping(request: web.Request) -> web.Response:
    return web.Response(text="Grooming bot is alive 🐾")


async def start_web_server() -> None:
    app = web.Application()
    app.router.add_get("/", handle_ping)
    app.router.add_get("/ping", handle_ping)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=PORT)
    await site.start()
    logger.info(f"Keep-alive web server started on port {PORT}")


async def start_bot() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not set. Add it to your environment variables.")

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(admin.router)
    dp.include_router(registration.router)
    dp.include_router(client.router)

    await init_db()

    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Bot polling started")
    await dp.start_polling(bot)


async def main() -> None:
    await asyncio.gather(start_web_server(), start_bot())


if __name__ == "__main__":
    asyncio.run(main())
