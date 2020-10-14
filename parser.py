import re
from enum import Enum
from urllib.parse import unquote

import requests

from wiki import WikipediaParser


class MessageTypes(Enum):
    WIKI = 'wiki'
    UKWIKIBOT = 'ukwikibot'
    WHATIS = 'whatis'
    LINK = 'link'
    RANDOM = 'random'
    HELP = 'help'
    BIRTHDAY = 'birthday'
    DEATHDAY = 'deathday'


HELP_TEXT = """Привіт! Я WikiBot, автоматичний робот, який допоможе вам знайти потрібну \
інформацію в українській Вікіпедії.
Приклади команд:
Ви: Що таке Вікіпедія?
WikiBot: Вікіпе́дія (англ. Wikipedia, МФА: [ˌwɪkɪˈpiːdɪə]) — загальнодоступна вільна багатомовна онлайн-енциклопедія, \
якою опікується неприбуткова організація «Фонд Вікімедіа».
Будь-хто, у кого є доступ до читання Вікіпедії, також може редагувати практично всі її статті.
Ви: дата народження джорджа буша старшого
WikiBot: Джордж Герберт Вокер Буш народився 12 червня 1924
Ви: Коли помер Майкл Джексон?
WikiBot: Джордж Герберт Вокер Буш народився 12 червня 1924

Ви: [[Вікіпедія]]
WikiBot: https://uk.wikipedia.org/wiki/Вікіпедія

Ви: /wiki
WikiBot: https://uk.wikipedia.org"""


class MessageParser:
    def __init__(self, message):
        self.message = message

    def get_matches(self):
        if re.search(r"!вікі|!wiki", self.message, re.I) or self.message.lower().strip() == '/wiki':
            return MessageTypes.WIKI, None
        elif "@ukwikibot" in self.message.lower():
            return MessageTypes.UKWIKIBOT, None
        elif matches := re.findall(r"\[\[(.+?)]]", self.message):
            return MessageTypes.LINK, matches
        elif matches := re.findall(r'(?:[шщШЩ]о таке |[Хх]то такий |[Хх]то так[аіе] )(.+)\??', self.message):
            return MessageTypes.WHATIS, matches
        elif matches := re.findall(re.compile(r'(?:коли народився |дата народження )(.+)\??', flags=re.IGNORECASE),
                                   self.message):
            return MessageTypes.BIRTHDAY, matches
        elif matches := re.findall(re.compile(r'(?:коли помер |дата смерті )(.+)\??', flags=re.IGNORECASE),
                                   self.message):
            return MessageTypes.DEATHDAY, matches
        elif self.message.lower().strip() == '/random':
            return MessageTypes.RANDOM, None
        elif self.message.lower().strip() in ('/start', '/help'):
            return MessageTypes.HELP, None

    def get_wiki_message(self, *args):
        return "https://uk.wikipedia.org"

    def get_ukwikibot_message(self, *args):
        return "Га?"

    def get_birthday_message(self, matches):
        if matches:
            match = matches[0]
            parser = WikipediaParser()
            page = parser.search_page(match)
            date = parser.get_birthday(page)
            if date:
                return f'{page.title()} народився {date}'

    def get_deathday_message(self, matches):
        if matches:
            match = matches[0]
            parser = WikipediaParser()
            page = parser.search_page(match)
            date = parser.get_deathday(page)
            if date:
                return f'{page.title()} помер {date}'

    def get_link_message(self, matches):
        for url in matches:
            response = requests.get("https://uk.wikipedia.org/wiki/" + url.replace(' ', '_'))
            if response.status_code == 200:
                url = unquote(response.url)
                yield url

    def get_random_message(self, *args):
        wiki = WikipediaParser()
        return wiki.random()

    def get_help_message(self, *args):
        return HELP_TEXT

    def get_whatis_message(self, matches):
        parser = WikipediaParser()
        for query in matches:
            yield parser.search(query)

    def get_response(self):
        message_type, matches = self.get_matches()
        func = getattr(self, f'get_{message_type.value}_message')

        return func(matches)
