import logging
import os

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler

from wikibot.parser import MessageParser, MessageTypes

logger = logging.getLogger(__name__)


token = os.getenv("TELEGRAM_TOKEN", None)
if token is None:
    raise ValueError("Missing TELEGRAM_TOKEN environment variable.")

app = ApplicationBuilder().token(token).build()


async def parse_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message or not update.message.text:
            return
        parser = MessageParser(update.message.text)
        parsed = await parser.get_response()
        if not parsed:
            return
        responses, message_group = parsed
        _, message_type = message_group.value
        if message_type == MessageTypes.COORDS and len(responses) > 0:
            for lat, lon in responses:
                await context.bot.send_location(update.message.chat_id, lat, lon)
        elif message_type == MessageTypes.IMAGE:
            for image, commons_category in responses:
                message = await context.bot.send_photo(update.message.chat_id, photo=image)
                if commons_category:
                    await message.reply_text(
                        f"Дивіться також фото в категорії "
                        f'<a href="https://commons.wikimedia.org/wiki/Category:{commons_category}">'
                        f"«{commons_category}»"
                        f"</a> на Вікісховищі",
                        parse_mode=ParseMode.HTML,
                    )
        elif message_type == MessageTypes.TEXT:
            for text in responses:
                await context.bot.send_message(update.message.chat_id, text, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error("Can not sent message: {}".format(e))


app.add_handler(MessageHandler(filters=None, callback=parse_messages, block=False))
