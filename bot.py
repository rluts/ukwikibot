import logging
import os

import telebot

from parser import MessageParser, MessageTypes

bot = telebot.TeleBot(os.environ.get('TELEGRAM_TOKEN', None))

logging.basicConfig(format=u'%(levelname)-8s [%(asctime)s] %(message)s',
                    level=logging.INFO, filename=u'tgbotlog.log')


@bot.message_handler(content_types=["text"])
def parse_messages(message):
    try:
        parser = MessageParser(message.text)
        responses, message_type = parser.get_response()
        if message_type == MessageTypes.COORDS:
            lat, long = responses
            bot.send_location(message.chat.id, lat, long)
        elif message_type == MessageTypes.IMAGE:
            with open(responses, 'rb') as f:
                bot.send_photo(message.chat.id, f)
        elif message_type == MessageTypes.TEXT:

            if isinstance(responses, str):
                responses = [responses]
            for text in responses:
                bot.send_message(message.chat.id, text, parse_mode='HTML')
    except Exception as e:
        logging.error("Can not sent message: {}".format(e))


if __name__ == '__main__':
    bot.polling(none_stop=True)
