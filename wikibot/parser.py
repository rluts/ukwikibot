import logging
import re
from enum import Enum
from typing import Any, List, Tuple
from urllib.parse import unquote

from httpx import AsyncClient

from wikibot.wiki import WikiManager

logger = logging.getLogger(__name__)


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
    FIELD_OF_WORK = ("field_of_work", MessageTypes.TEXT)
    EDUCATION = ("education", MessageTypes.TEXT)


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
        (Messages.WHATIS, r"(?:[шщ]о таке |хто такий |хто так[аіе] )([\w,\s]+)\??"),
        (Messages.LINK, r"\[\[(.+?)]]"),
        (Messages.BIRTHDAY, r"(?:коли народи(?:вся|лась) |дата народження )([\w,\s]+)\??"),
        (Messages.DEATHDAY, r"(?:коли помер(?:ла)? |дата смерті )(.+)\??"),
        (Messages.FIELD_OF_WORK, r"@ukwikibot.*(?:спеціалізація |сфера роботи )(.+)\??"),
        (Messages.COORDS, r"(?:де розташован(?:ий|а|е|і) |де знаходиться )(.+)\??"),
        (Messages.COORDS_GEN, r"координати (.+)\??"),
        (Messages.IMAGE, r"(?:знайди|покажи) (?:фото |зображення )(.+)\??"),
        (Messages.UKWIKIBOT, r"@ukwikibot"),
    ]

    COMMANDS = {
        "help": Messages.HELP,
        "start": Messages.HELP,
        "random": Messages.RANDOM,
        "wiki": Messages.WIKI,
    }

    CONTAINS = {
        "@ukwikibot": Messages.UKWIKIBOT,
    }

    def __init__(self) -> None:
        self.wiki_manager = WikiManager()
        self.wiki_manager.login()
        self.regex_match = [
            (message_group, re.compile(regex, re.IGNORECASE)) for message_group, regex in self.REGEXES_MATCH
        ]

    async def get_matches(self, message: str) -> Tuple[Messages, List[str] | None]:
        for message_type, pattern in self.regex_match:
            if matches := re.findall(pattern, message):
                return message_type, matches
        for key, value in self.CONTAINS.items():
            if key in message:
                return value, None

    async def get_ukwikibot_message(self, *args):
        yield "Га?"

    async def get_random_command(self):
        return await self.wiki_manager.random()

    async def get_help_command(self):
        return HELP_TEXT

    async def get_wiki_command(self):
        return "https://uk.wikipedia.org/"

    async def get_image_message(self, matches):
        for match in matches:
            image_url, description_url, commons_category = await self.wiki_manager.get_images_genitive(match)
            description_message = ""
            content = None
            if image_url and description_url:
                description_message += f'<a href="{description_url}">Автор та ліцензія.</a> Дивіться також'
                async with AsyncClient() as client:
                    response = await client.get(image_url)
                    if response.status_code == 200 and response.headers.get("content-type") == "image/jpeg":
                        content = response.content
            if commons_category:
                description_message = (
                    f"{description_message or 'Основне фото не знайдено. Дивіться'} фото в категорії "
                    f'<a href="https://commons.wikimedia.org/wiki/Category:{commons_category}">'
                    f"«{commons_category}»"
                    f"</a> на Вікісховищі"
                )
            yield content, description_message or None

    async def get_birthday_message(self, matches):
        for match in matches:
            page = await self.wiki_manager.search_page(match)
            gender = await self.wiki_manager.get_gender(page)
            date = await self.wiki_manager.get_birthday(page)
            w = "народилась" if gender == "female" else "народився"
            if date:
                yield f"{page.title()} {w} {date}"

    async def get_coords_gen_message(self, matches):
        for match in matches:
            page = await self.wiki_manager.genitive_search(match)
            yield await self.wiki_manager.get_coords(page)

    async def get_coords_message(self, matches):
        for match in matches:
            page = await self.wiki_manager.search_page(match)
            yield await self.wiki_manager.get_coords(page)

    async def get_deathday_message(self, matches):
        for match in matches:
            page = await self.wiki_manager.search_page(match)
            gender = await self.wiki_manager.get_gender(page)
            date = await self.wiki_manager.get_deathday(page)
            if date:
                yield f"{page.title()} помер{'ла' if gender == 'female' else ''} {date}"

    async def get_link_message(self, matches):
        async with AsyncClient(http2=True) as client:
            for url in matches:
                url = f"https://uk.wikipedia.org/wiki/{url.replace(' ', '_')}"
                response = await client.get(url, follow_redirects=True, timeout=10)
                if response.status_code != 404:
                    yield unquote(str(response.url))
                else:
                    logger.info(f"Error while fetching {url}. Status code: {response.status_code}")

    async def get_whatis_message(self, matches):
        for query in matches:
            yield await self.wiki_manager.search(query)

    async def get_field_of_work_message(self, matches):
        for query in matches:
            value = await self.wiki_manager.get_field_of_work(page=query)
            logger.debug(f"{query} - {value}")
            if value:
                yield value

    async def get_command_response(self, message: str) -> str:
        message_name, message_type = self.COMMANDS[message].value
        func = getattr(self, f"get_{message_name}_command")
        return await func()

    async def get_response(self, message: str) -> Tuple[List[Any] | None, MessageTypes | None]:
        response = await self.get_matches(message)
        if not response:
            return None, None
        message_group, matches = response
        message_name, message_type = message_group.value
        func = getattr(self, f"get_{message_name}_message")
        responses = []
        async for match in func(matches):
            responses.append(match)

        return responses, message_type
