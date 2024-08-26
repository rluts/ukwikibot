import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from telegram.ext import Application

from wikibot.bot import app

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("pymorphy3").setLevel(logging.WARNING)
logging.getLogger("hpack").setLevel(logging.WARNING)
logging.basicConfig(
    level=logging.DEBUG,
)


async def start(application: Application) -> Application:
    await application.initialize()
    await application.updater.start_polling()
    await application.start()
    return application


async def stop(application: Application) -> None:
    await application.updater.stop()
    await application.stop()
    await application.shutdown()


async def run_polling(application: Application) -> None:
    try:
        application = await start(application)
        while application.running:
            await asyncio.sleep(5)
        logging.error("Unexpected stopping the bot")
    except Exception:  # noqa
        logging.exception(f"Cannot run the bot")
    finally:
        await stop(application)


if __name__ == "__main__":
    asyncio.run(run_polling(app))
