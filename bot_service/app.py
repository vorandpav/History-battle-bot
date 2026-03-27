import asyncio
import logging

from aiogram import Bot, Dispatcher

from bot_service.clients import ServiceClients
from bot_service.config import load_settings
from bot_service.handlers import router


async def main() -> None:
    settings = load_settings()
    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()

    clients = ServiceClients(
        answer_service_url=settings.answer_service_url,
        voice_service_url=settings.voice_service_url,
        battle_service_url=settings.battle_service_url,
    )

    dp.include_router(router)
    dp["clients"] = clients
    dp["default_mode"] = settings.default_mode
    dp["default_level"] = settings.default_level

    try:
        await dp.start_polling(bot)
    finally:
        await clients.close()
        await bot.session.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
