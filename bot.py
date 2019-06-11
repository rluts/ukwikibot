# -*- coding: utf-8 -*-
import config
import wikipedia
import telebot
import re
import logging
import time

bot = telebot.TeleBot(config.token)
wikipedia.set_lang('uk')

logging.basicConfig(format = u'%(levelname)-8s [%(asctime)s] %(message)s: /wiki message',
                    level = logging.DEBUG, filename = u'tgbotlog.log')

        
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
        r = re.search(r"\[\[(.+)\]\]", message.text)
        if r:
            bot.send_message(message.chat.id, "https://uk.wikipedia.org/wiki/" + r.group(1).replace(' ', '_'))
    except Exception as e:
        logging.error("Can not sent parsing link message".format(e))
    try:
        r = re.search(r"([шщШЩ]о таке |[Хх]то такий |[Хх]то так[аіе] )(.+)\??", message.text)
        if "rluts" in r.group(2).lower():
            bot.send_message(message.chat.id, 'RLuts — це мій творець. Якщо ви хочете розширити '
                                              'мій функціонал і у вас є гарні ідеї або ж виправити '
                                              'в мені якусь помилку — пишіть йому: @rluts')
        elif r:
            bot.send_message(message.chat.id, wikipedia.summary(r.group(2), sentences=5)
                             .replace("\n==", "\n<b>").replace("==\n", "</b>\n"), parse_mode='HTML')
    except Exception as e:
        logging.error("Can not sent message: {}".format(e))


if __name__ == '__main__':
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            logging.error("Unknown error: {}".format(e))
