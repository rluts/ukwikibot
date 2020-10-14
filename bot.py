import logging
import os

import telebot

from parser import MessageParser

bot = telebot.TeleBot(os.environ.get('TELEGRAM_TOKEN', None))

logging.basicConfig(format=u'%(levelname)-8s [%(asctime)s] %(message)s',
                    level=logging.INFO, filename=u'tgbotlog.log')


@bot.message_handler(content_types=["text"])
def parse_messages(message):
    try:
        parser = MessageParser(message.text)
        responses = parser.get_response()
        if isinstance(responses, tuple) and (isinstance(responses[0], float) or isinstance(responses[0], int)):
            lat, long = responses
            bot.send_location(message.chat.id, lat, long)
            return
        elif isinstance(responses, str):
            responses = [responses]
        for text in responses:
            bot.send_message(message.chat.id, text, parse_mode='HTML')
    except Exception as e:
        logging.error("Can not sent message: {}".format(e))


if __name__ == '__main__':
    bot.polling(none_stop=True)
