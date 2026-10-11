import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from bot.config import BOT_TOKEN, WEBHOOK_URL, WEBHOOK_PATH, WEBAPP_HOST, WEBAPP_PORT
from bot.handlers import get_handlers_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def on_startup(bot: Bot):
    if WEBHOOK_URL:
        await bot.set_webhook(WEBHOOK_URL)
        logger.info(f"Webhook o‘rnatildi: {WEBHOOK_URL}")
    else:
        logger.info("Polling rejimida ishlayapti")

async def on_shutdown(bot: Bot):
    if WEBHOOK_URL:
        await bot.delete_webhook()
    await bot.session.close()

def main():
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    # Handlerlarni ulaymiz
    dp.include_router(get_handlers_router())

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # ========== PORT (Webhook) rejimi ==========
    if WEBHOOK_URL:
        app = web.Application()
        webhook_requests_handler = SimpleRequestHandler(
            dispatcher=dp,
            bot=bot,
        )
        webhook_requests_handler.register(app, path=WEBHOOK_PATH)
        setup_application(app, dp, bot=bot)

        logger.info(f"Webhook server ishga tushmoqda: {WEBAPP_HOST}:{WEBAPP_PORT}")
        web.run_app(app, host=WEBAPP_HOST, port=WEBAPP_PORT)

    # ========== Oddiy Polling rejimi ==========
    else:
        asyncio.run(dp.start_polling(bot))

if __name__ == "__main__":
    main()