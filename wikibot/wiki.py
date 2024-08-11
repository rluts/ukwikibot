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

    def _get_images_genitive(self, page: pywikibot.Page) -> Tuple[str | None, str | None]:
        try:
            item = pywikibot.ItemPage.fromPage(page)
            wb_item = next(iter(item.claims["P18"]), None)
            if wb_item:
                wb_category = next(iter(item.claims["P373"]), None)

                return wb_item.target.get_file_url(url_width=800), wb_category and wb_category.target
        except (AttributeError, KeyError, IndexError, ValueError):
            return None, None

    async def get_images_genitive(self, text: str) -> Tuple[str | None, str | None]:
        page = await self.genitive_search(text)
        if page is None:
            return None, None
        return await self.loop.run_in_executor(None, self._get_images_genitive, page)

    async def genitive_search(self, text: str) -> pywikibot.Page | None:
        morph = pymorphy3.MorphAnalyzer(lang="uk")
        for word in reversed(morph.parse(text)):
            logger.debug(f"Transforming {text} to {word.normal_form}")
            page = await self.search_page(word.normal_form)
            if page:
                return page
            logger.info("Page not found on Wikipedia")

    async def search(self, text: str) -> str | None:
        page = await self.search_page(text)
        return await self.get_page_summary(page)
