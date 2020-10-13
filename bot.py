import os
import urllib

import requests

import wikipedia
import telebot
import re
import logging
import pywikibot

from wiki import WikipediaParser

bot = telebot.TeleBot(os.environ.get('TELEGRAM_TOKEN', None))
wikipedia.set_lang('uk')

logging.basicConfig(format=u'%(levelname)-8s [%(asctime)s] %(message)s',
                    level=logging.INFO, filename=u'tgbotlog.log')

        
@bot.message_handler(commands=['start', 'help'])
def staart_messages(message):
    try:
        bot.send_message(message.chat.id, """Привіт! Я WikiBot, автоматичний робот, який допоможе вам знайти потрібну інформацію в українській Вікіпедії.
Приклади команд:
Ви: Що таке Вікіпедія?
WikiBot: Вікіпе́дія (англ. Wikipedia, МФА: [ˌwɪkɪˈpiːdɪə]) — загальнодоступна вільна багатомовна онлайн-енциклопедія, якою опікується неприбуткова організація «Фонд Вікімедіа».
Будь-хто, у кого є доступ до читання Вікіпедії, також може редагувати практично всі її статті.

Ви: [[Вікіпедія]]
WikiBot: https://uk.wikipedia.org/wiki/Вікіпедія

Ви: /wiki
WikiBot: https://uk.wikipedia.org""", parse_mode='HTML')
    except Exception as e:
        logging.error("Can not sent start message: {}".format(e))


@bot.message_handler(commands=['wiki'])
def wiki_message(message):
    try:
        bot.send_message(message.chat.id, "https://uk.wikipedia.org") 
    except Exception as e:
        logging.error("Can not sent link message: {}".format(e))


@bot.message_handler(commands=['random'])
def wiki_message(message):
    try:
        bot.send_message(message.chat.id, wikipedia.summary(wikipedia.random(1), sentences=5).replace("\n==", "\n<b>").replace("==\n", "</b>\n"), parse_mode='HTML')
    except Exception as e:
        logging.error("Can not sent random message: {}".format(e))


@bot.message_handler(content_types=["text"])
def parse_messages(message):
    try:
        if re.search(r"!вікі|!wiki", message.text, re.I):
            bot.send_message(message.chat.id, "https://uk.wikipedia.org")
        if "@ukwikibot" in message.text.lower():
            bot.send_message(message.chat.id, "Га?")
        r = re.findall(r"\[\[(.+?)]]", message.text)
        if r:
            for url in r:
                response = requests.get("https://uk.wikipedia.org/wiki/" + url.replace(' ', '_'))
                if response.status_code == 200:
                    url = urllib.parse.unquote(response.url)
                    bot.send_message(message.chat.id, url)
    except Exception as e:
        logging.error("Can not sent parsing link message".format(e))
    try:
        r = re.search(r"([шщШЩ]о таке |[Хх]то такий |[Хх]то так[аіе] )(.+)\??", message.text)
        if "rluts" in r.group(2).lower():
            bot.send_message(message.chat.id, 'RLuts — це мій творець. Якщо ви хочете розширити '
                                              'мій функціонал і у вас є гарні ідеї або ж виправити '
                                              'в мені якусь помилку — пишіть йому: @rluts')
        elif r:
            query = r.group(2)
            parser = WikipediaParser()
            text = parser.search_and_parse(query)
            if text:
                bot.send_message(message.chat.id, text, parse_mode='HTML')
    except Exception as e:
        logging.error("Can not sent message: {}".format(e))


if __name__ == '__main__':
    bot.polling(none_stop=True)
