import re
from enum import Enum
from typing import Any, List, Tuple
from urllib.parse import unquote

from httpx import AsyncClient

from wikibot.wiki import WikiManager


class MessageTypes(Enum):
    TEXT = "text"
    COORDS = "coords"
    IMAGE = "image"


class Messages(Enum):
    WIKI = ("wiki", MessageTypes.TEXT)
    UKWIKIBOT = ("ukwikibot", MessageTypes.TEXT)
    WHATIS = ("whatis", MessageTypes.TEXT)
    LINK = ("link", MessageTypes.TEXT)
    RANDOM = ("random", MessageTypes.TEXT)
    HELP = ("help", MessageTypes.TEXT)
    BIRTHDAY = ("birthday", MessageTypes.TEXT)
    DEATHDAY = ("deathday", MessageTypes.TEXT)
    COORDS = ("coords", MessageTypes.COORDS)
    COORDS_GEN = ("coords_gen", MessageTypes.COORDS)
    IMAGE = ("image", MessageTypes.IMAGE)


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
WikiBot: Майкл Джексон помер 25 червня 2009
Ви: Де розташований Київ? [також реагує на: Координати Кмєва]
WikiBot: (мапа з координатами)
Ви: Знайди фото Києва
WikiBot: (фото)
WikiBot: Дивіться також фото в категорії «Kyiv» на Вікісховищі
Ви: [[Вікіпедія]]
WikiBot: https://uk.wikipedia.org/wiki/Вікіпедія
Ви: /wiki
WikiBot: https://uk.wikipedia.org"""


class Matcher(Enum):
    contains = "contains"
    re_match = "match"
    equal = "equal"


class MessageParser:
    REGEXES_MATCH = [
        (Messages.UKWIKIBOT, re.compile(r"@ukwikibot")),
        (Messages.WHATIS, re.compile(r"(?:[шщ]о таке |хто такий |хто так[аіе] )([\w,\s]+)\??")),
        (Messages.LINK, re.compile(r"\[\[(.+?)]]")),
        (Messages.BIRTHDAY, re.compile(r"(?:коли народи(?:вся|лась) |дата народження )([\w,\s]+)\??")),
        (Messages.DEATHDAY, re.compile(r"(?:коли помер(?:ла)? |дата смерті )(.+)\??")),
        (Messages.COORDS, re.compile(r"(?:де розташован(?:ий|а|е|і) |де знаходиться )(.+)\??")),
        (Messages.COORDS_GEN, re.compile(r"координати (.+)\??")),
        (Messages.IMAGE, re.compile(r"(?:знайди|покажи) (?:фото |зображення )(.+)\??")),
    ]

    COMMANDS = {
        "help": Messages.HELP,
        "start": Messages.HELP,
        "random": Messages.RANDOM,
        "wiki": Messages.WIKI,
    }

    CONTAINS = {
        "@ukwikibot": Messages.UKWIKIBOT,
        "!wiki": Messages.WIKI,
        "!вікі": Messages.WIKI,
    }

    def __init__(self, message: str):
        self.message = message.lower()
        self.wiki_manager = WikiManager()

    async def get_matches(self) -> Tuple[Messages, List[str] | None]:
        for message_type, pattern in self.REGEXES_MATCH:
            if matches := re.findall(pattern, self.message):
                return message_type, matches
        if self.message.startswith("/") and self.message[1:] in self.COMMANDS:
            return self.COMMANDS[self.message[1:]], None
        for key, value in self.CONTAINS.items():
            if key in self.message:
                return value, None

    async def get_wiki_message(self, *args):
        yield "https://uk.wikipedia.org"

    async def get_ukwikibot_message(self, *args):
        yield "Га?"

    async def get_image_message(self, matches):
        if matches:
            match = matches[0]
            image_url, description_url, commons_category = await self.wiki_manager.get_images_genitive(match)
            if image_url:
                async with AsyncClient() as client:
                    response = await client.get(image_url)
                    if response.status_code == 200 and response.headers.get("content-type") == "image/jpeg":
                        yield response.content, description_url, commons_category

    async def get_birthday_message(self, matches):
        if matches:
            match = matches[0]
            page = await self.wiki_manager.search_page(match)
            gender = await self.wiki_manager.get_gender(page)
            date = await self.wiki_manager.get_birthday(page)
            w = "народилась" if gender == "female" else "народився"
            if date:
                yield f"{page.title()} {w} {date}"

    async def get_coords_gen_message(self, matches):
        if matches:
            match = matches[0]
            page = await self.wiki_manager.genitive_search(match)
            yield await self.wiki_manager.get_coords(page)

    async def get_coords_message(self, matches):
        if matches:
            match = matches[0]
            page = await self.wiki_manager.search_page(match)
            yield await self.wiki_manager.get_coords(page)

    async def get_deathday_message(self, matches):
        if matches:
            match = matches[0]
            page = await self.wiki_manager.search_page(match)
            gender = await self.wiki_manager.get_gender(page)
            date = await self.wiki_manager.get_deathday(page)
            if date:
                yield f"{page.title()} помер{'ла' if gender == 'female' else ''} {date}"

    async def get_link_message(self, matches):
        async with AsyncClient(http2=True) as client:
            for url in matches:
                url = f"https://uk.wikipedia.org/wiki/{url.replace(' ', '_')}"
                response = await client.get(url, follow_redirects=True)
                if response.status_code == 200:
                    yield unquote(str(response.url))

    async def get_random_message(self, *args):
        yield await self.wiki_manager.random()

    async def get_help_message(self, *args):
        yield HELP_TEXT

    async def get_whatis_message(self, matches):
        for query in matches:
            yield await self.wiki_manager.search(query)

    async def get_response(self) -> Tuple[List[Any], Messages] | None:
        response = await self.get_matches()
        if not response:
            return None
        message_group, matches = response
        message_name, message_type = message_group.value
        func = getattr(self, f"get_{message_name}_message")
        responses = []
        async for match in func(matches):
            responses.append(match)

        return responses, message_group
