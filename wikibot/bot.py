import logging
from functools import partial
from typing import List, Tuple

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler

from wikibot.config import config
from wikibot.parser import MessageParser, MessageTypes

logger = logging.getLogger(__name__)


async def parse_command(message_parser: MessageParser, update: Update, _: ContextTypes.DEFAULT_TYPE):
    command = update.message.text.lstrip("/").rstrip("@ukwikibot")
    logger.debug(f"{update.message.text} command")
    if message := await message_parser.get_command_response(command):
        await update.message.reply_text(message, parse_mode=ParseMode.HTML)


async def parse_messages(message_parser: MessageParser, update: Update, _: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message or not update.message.text:
            return
        messages, message_type = await message_parser.get_response(update.message.text)
        if not message_type:
            return
        messages = filter(lambda m: m, messages)
        if message_type == MessageTypes.COORDS:
            await send_coords(update, messages)
        elif message_type == MessageTypes.IMAGE:
            await send_image(update, messages)
        elif message_type == MessageTypes.TEXT:
            await send_text(update, messages)
    except Exception:  # noqa
        logger.exception("Can parse message")


async def send_text(update: Update, messages: List[str]):
    for text in messages:
        logger.debug(f"Text answer: {text}. Text request: {update.message.text}")
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def send_coords(update: Update, messages: List[Tuple[float, float]]):
    for latitude, longitude in messages:
        logger.debug(f"Coords: {latitude} {longitude}. Text: {update.message.text}")
        await update.message.reply_location(latitude, longitude)


async def send_image(update: Update, messages: List[Tuple[bytes | None, str | None]]):
    for image, description_message in messages:
        if image:
            logger.debug(f"Sending image. Text: {update.message.text}")
            await update.message.reply_photo(photo=image)
        if description_message:
            logger.debug(f"Image: {description_message}. Text: {update.message.text}")
            await update.message.reply_text(
                description_message,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
            )


async def setup_bot() -> Application:
    app = ApplicationBuilder().token(config.telegram_token).build()
    parser = MessageParser()
    for cmd in MessageParser.COMMANDS.keys():
        app.add_handler(CommandHandler(command=cmd, callback=partial(parse_command, parser), block=False))
    app.add_handler(MessageHandler(filters=None, callback=partial(parse_messages, parser), block=False))
    return app
