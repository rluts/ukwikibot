import asyncio
import logging
import logging.config

import yaml
from telegram.ext import Application

from wikibot.bot import setup_bot


def setup_logging() -> None:
    with open("logging.yaml", "r") as f:
        config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)


async def start(application: Application) -> Application:
    await application.initialize()
    await application.updater.start_polling()
    await application.start()
    return application


async def stop(application: Application) -> None:
    await application.updater.stop()
    await application.stop()
    await application.shutdown()


async def run_polling() -> None:
    application = await setup_bot()
    try:
        application = await start(application)
        while application.running:
            await asyncio.sleep(5)
        logging.error("Unexpected stopping the bot")
    except Exception:  # noqa
        logging.exception("Cannot run the bot")
    finally:
        await stop(application)


if __name__ == "__main__":
    setup_logging()
    asyncio.run(run_polling())
