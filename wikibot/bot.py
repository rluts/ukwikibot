import logging
import os
from functools import partial
from typing import List, Tuple

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler

from wikibot.parser import MessageParser, MessageTypes

logger = logging.getLogger(__name__)


token = os.getenv("TELEGRAM_TOKEN", None)
if token is None:
    raise ValueError("Missing TELEGRAM_TOKEN environment variable.")

app = ApplicationBuilder().token(token).build()


async def parse_command(command: str, update: Update, _: ContextTypes.DEFAULT_TYPE):
    parser = MessageParser(command)
    if message := await parser.get_command_response():
        await update.message.reply_text(message, parse_mode=ParseMode.HTML)


async def parse_messages(update: Update, _: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message or not update.message.text:
            return
        parser = MessageParser(update.message.text)
        messages, message_type = await parser.get_response()
        if not message_type:
            return
        messages = filter(lambda m: m, messages)
        if message_type == MessageTypes.COORDS and len(messages) > 0:
            await send_coords(update, messages)
        elif message_type == MessageTypes.IMAGE:
            await send_image(update, messages)
        elif message_type == MessageTypes.TEXT:
            await send_text(update, messages)
    except Exception:  # noqa
        logger.exception("Can parse message")


async def send_text(update: Update, messages: List[str]):
    for text in messages:
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def send_coords(update: Update, messages: List[Tuple[float, float]]):
    for latitude, longitude in messages:
        await update.message.reply_location(latitude, longitude)


async def send_image(update: Update, messages: List[Tuple[bytes | None, str | None]]):
    for image, description_message in messages:
        if image:
            await update.message.reply_photo(photo=image)
        if description_message:
            await update.message.reply_text(
                description_message,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
            )


for cmd in MessageParser.COMMANDS.keys():
    app.add_handler(CommandHandler(command=cmd, callback=partial(parse_command, cmd), block=False))
app.add_handler(MessageHandler(filters=None, callback=parse_messages, block=False))
