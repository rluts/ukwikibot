import os
import re
import shutil
from enum import Enum
from urllib.parse import unquote

import requests

from wiki import WikipediaParser


class MessageTypes(Enum):
    TEXT = 'text'
    COORDS = 'coords'
    IMAGE = 'image'


class Messages(Enum):
    WIKI = ('wiki', MessageTypes.TEXT)
    UKWIKIBOT = ('ukwikibot', MessageTypes.TEXT)
    WHATIS = ('whatis', MessageTypes.TEXT)
    LINK = ('link', MessageTypes.TEXT)
    RANDOM = ('random', MessageTypes.TEXT)
    HELP = ('help', MessageTypes.TEXT)
    BIRTHDAY = ('birthday', MessageTypes.TEXT)
    DEATHDAY = ('deathday', MessageTypes.TEXT)
    COORDS = ('coords', MessageTypes.COORDS)
    IMAGE = ('image', MessageTypes.IMAGE)


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
Ви: Де розташований Київ?
WikiBot: (мапа з координатами)
Ви: Знайди фото Києва?
WikiBot: (фото)

Ви: [[Вікіпедія]]
WikiBot: https://uk.wikipedia.org/wiki/Вікіпедія

Ви: /wiki
WikiBot: https://uk.wikipedia.org"""


class MessageParser:
    def __init__(self, message):
        self.message = message

    def get_matches(self):
        if re.search(r"!вікі|!wiki", self.message, re.I) or self.message.lower().strip() == '/wiki':
            return Messages.WIKI, None
        elif "@ukwikibot" in self.message.lower():
            return Messages.UKWIKIBOT, None
        elif matches := re.findall(r"\[\[(.+?)]]", self.message):
            return Messages.LINK, matches
        elif matches := re.findall(r'(?:[шщШЩ]о таке |[Хх]то такий |[Хх]то так[аіе] )(.+)\??', self.message):
            return Messages.WHATIS, matches
        elif matches := re.findall(re.compile(r'(?:коли народи(?:вся|лась) |дата народження )(.+)\??',
                                              flags=re.IGNORECASE),
                                   self.message):
            return Messages.BIRTHDAY, matches
        elif matches := re.findall(re.compile(r'(?:коли помер |дата смерті )(.+)\??', flags=re.IGNORECASE),
                                   self.message):
            return Messages.DEATHDAY, matches
        elif matches := re.findall(re.compile(r'знайди (?:фото |зображення )(.+)\??', flags=re.IGNORECASE),
                                   self.message):
            return Messages.IMAGE, matches
        elif matches := re.findall(re.compile(r'(?:де розташован(?:ий|а|е|і) |де знаходиться'
                                              r'|координати )(.+)\??', flags=re.IGNORECASE),
                                   self.message):
            return Messages.COORDS, matches
        elif self.message.lower().strip() == '/random':
            return Messages.RANDOM, None
        elif self.message.lower().strip() in ('/start', '/help'):
            return Messages.HELP, None

    def get_wiki_message(self, *args):
        return "https://uk.wikipedia.org"

    def get_ukwikibot_message(self, *args):
        return "Га?"

    def get_image_message(self, matches):
        if matches:
            match = matches[0]
            parser = WikipediaParser()
            image_url = parser.get_images_genitive(match)
            if image_url:
                r = requests.get(image_url, stream=True)
                if r.status_code == 200:
                    r.raw.decode_content = True
                    filename = os.path.join('tmp', image_url.split('/')[-1])
                    # Open a local file with wb ( write binary ) permission.
                    with open(filename, 'wb') as f:
                        shutil.copyfileobj(r.raw, f)
                    return filename

    def get_birthday_message(self, matches):
        if matches:
            match = matches[0]
            parser = WikipediaParser()
            page = parser.search_page(match)
            gender = parser.get_gender(page)
            date = parser.get_birthday(page)
            w = 'народилась' if gender == 'female' else 'народився'
            if date:
                return f'{page.title()} {w} {date}'

    def get_coords_message(self, matches):
        if matches:
            match = matches[0]
            parser = WikipediaParser()
            page = parser.search_page(match)
            return parser.get_coords(page)

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
        message_group, matches = self.get_matches()
        message_name, message_type = message_group.value
        func = getattr(self, f'get_{message_name}_message')

        return func(matches), message_type
