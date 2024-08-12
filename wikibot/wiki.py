import asyncio
import logging
import re
from typing import Tuple
from urllib.parse import unquote

import pymorphy3
import pywikibot

MONTH_MAP = [
    "січня",
    "лютого",
    "березня",
    "квітня",
    "травня",
    "червня",
    "липня",
    "серпня",
    "вересня",
    "жовтня",
    "листопада",
    "грудня",
]

logger = logging.getLogger(__name__)


class WikiManager:
    def __init__(self):
        self.loop = asyncio.get_running_loop()
        self.site = pywikibot.Site(code="uk", fam="wikipedia")
        self.morph = pymorphy3.MorphAnalyzer(lang="uk")

    def _search_page(self, query: str) -> pywikibot.Page | None:
        page = next(
            iter(self.site.search(query, total=1, content=True, namespaces=[0])),
            None,
        )
        return page

    async def search_page(self, query: str) -> pywikibot.Page | None:
        return await self.loop.run_in_executor(None, self._search_page, query)

    def _get_plain_text(self, page: pywikibot.Page) -> str | None:
        params = {
            "action": "query",
            "prop": "extracts",
            "exsentences": 7,
            "explaintext": 1,
            "format": "json",
            "titles": page.title(),
        }
        request = self.site.simple_request(**params)
        response = request.submit()
        try:
            return self.parse_text(next(iter(response["query"]["pages"].values()), None)["extract"])
        except (KeyError, TypeError):
            return None

    async def get_plain_text(self, page: pywikibot.Page):
        return await self.loop.run_in_executor(None, self._get_plain_text, page)

    @staticmethod
    def parse_text(text: str) -> str:
        return re.sub("={2,} ?(.+?)={2,}", r"<b>\1</b>", text)

    async def get_page_summary(self, page: pywikibot.Page | None) -> str | None:
        if page is None:
            return None
        html = await self.get_plain_text(page)
        link = f'<a href="{unquote(page.full_url())}">Читати у Вікіпедії</a>'

        return f"{html}\n\n{link}"

    def _get_random_page(self) -> pywikibot.Page | None:
        generator = self.site.randompages(total=1, redirects=False, namespaces=[0])

        return next(iter(generator), None)

    async def get_random_page(self) -> pywikibot.Page | None:
        return await self.loop.run_in_executor(None, self._get_random_page)

    async def random(self) -> str:
        page = await self.get_random_page()

        return await self.get_page_summary(page)

    def _get_gender(self, page) -> str:
        item = pywikibot.ItemPage.fromPage(page)
        wb_item = next(iter(item.claims["P21"]), None)
        if wb_item.target.title() == "Q6581097":
            return "male"
        elif wb_item.target.title() == "Q6581072":
            return "female"
        return "unknown"

    async def get_gender(self, page) -> str:
        return await self.loop.run_in_executor(None, self._get_gender, page)

    async def get_birthday(self, page):
        return await self.get_wikidata_date(page, "P569")

    async def get_deathday(self, page):
        return await self.get_wikidata_date(page, "P570")

    def _get_coords(self, page: pywikibot.Page) -> Tuple[float, float] | None:
        try:
            item = pywikibot.ItemPage.fromPage(page)
            for wb_item in item.claims["P625"]:
                return wb_item.target.lat, wb_item.target.lon
        except (KeyError, IndexError, AttributeError):
            pass

    async def get_coords(self, page: pywikibot.Page) -> Tuple[float, float] | None:
        return await self.loop.run_in_executor(None, self._get_coords, page)

    def _get_wikidata_date(self, page, prop) -> str | None:
        try:
            item = pywikibot.ItemPage.fromPage(page)
            for wb_item in item.claims[prop]:
                if "Q1985727" in wb_item.target.calendarmodel:
                    return f"{wb_item.target.day} {MONTH_MAP[wb_item.target.month - 1]} {wb_item.target.year}"
        except (KeyError, IndexError):
            return None

    async def get_wikidata_date(self, page, prop) -> str | None:
        return await self.loop.run_in_executor(None, self._get_wikidata_date, page, prop)

    def _get_page_image_info(self, page: pywikibot.Page) -> Tuple[str | None, str | None, str | None]:
        item = pywikibot.ItemPage.fromPage(page)
        photo_bytes = None
        image_description = None
        category = None

        if item is None:
            return None, None, None

        wb_items = item.claims.get("P18")
        if wb_items:
            wb_item = wb_items[0]
            photo_bytes = wb_item.target.get_file_url(url_width=800)
            image_description = wb_item.target.latest_file_info.descriptionurl
        wb_category = item.claims.get("P373")
        if wb_category:
            category = wb_category[0].target
        return photo_bytes, image_description, category

    async def get_images_genitive(self, text: str) -> Tuple[str | None, str | None, str | None]:
        page = await self.genitive_search(text)
        if page is None:
            return None, None, None
        return await self.loop.run_in_executor(None, self._get_page_image_info, page)

    async def genitive_transform(self, text: str) -> str:
        word_list = text.split()
        transformed_word_list = []
        for word in word_list:
            transformed_word = word
            for w in reversed(self.morph.parse(word)):
                if w.tag and w.tag.case == "gent":
                    transformed_word = w.normal_form
                    break
            transformed_word_list.append(transformed_word.capitalize() if word.istitle() else transformed_word)
        transformed_text = " ".join(transformed_word_list)
        logger.debug(f"Transforming {text} to {transformed_text}")
        return transformed_text

    async def genitive_search(self, text: str) -> pywikibot.Page | None:
        text = await self.genitive_transform(text)
        page = await self.search_page(text)
        if page:
            return page
        logger.info("Page not found on Wikipedia")

    async def search(self, text: str) -> str | None:
        page = await self.search_page(text)
        return await self.get_page_summary(page)
