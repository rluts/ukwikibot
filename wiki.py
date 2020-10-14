import re
from urllib.parse import unquote

import pymorphy2
import pywikibot

MONTH_MAP = [
    'січня', 'лютого', 'березня', 'квітня', 'травня', 'червня', 'липня', 'серпня', 'вересня',
    'жовтня', 'листопада', 'грудня'
]


class WikipediaParser:
    def __init__(self):
        self.site = pywikibot.Site(code='uk', fam='wikipedia')

    def search_page(self, query: str):
        page = next(iter(
            self.site.search(
                query,
                where='title',
                total=1,
                content=True,
                namespaces=[0]
            )), None)

        return page

    def get_plain_text(self, page: pywikibot.Page):
        params = {
            'action': 'query',
            'prop': 'extracts',
            'exsentences': 7,
            'explaintext': 1,
            'format': 'json',
            'titles': page.title()
        }
        request = self.site._simple_request(**params)
        response = request.submit()
        try:
            return self.parse_text(next(iter(response['query']['pages'].values()), None)['extract'])
        except (KeyError, TypeError):
            pass

    @staticmethod
    def parse_text(text: str):
        return re.sub('={2,} ?(.+?)={2,}', r'<b>\1</b>', text)

    def get_page_summary(self, page: pywikibot.Page) -> [str, None]:
        if page is None:
            return

        html = self.get_plain_text(page)
        link = f'<a href="{unquote(page.full_url())}">Читати у Вікіпедії</a>'

        return f'{html}\n\n{link}'

    def get_random_page(self) -> pywikibot.Page:
        generator = self.site.randompages(total=1, redirects=False, namespaces=[0])

        return next(iter(generator), None)

    def random(self) -> str:
        page = self.get_random_page()

        return self.get_page_summary(page)

    def get_gender(self, page):
        item = pywikibot.ItemPage.fromPage(page)
        wb_item = next(iter(item.claims['P21']), None)
        if wb_item.target.title() == 'Q6581097':
            return 'male'
        elif wb_item.target.title() == 'Q6581072':
            return 'female'
        return 'unknown'

    def get_birthday(self, page):
        return self.get_wikidata_date(page, 'P569')

    def get_deathday(self, page):
        return self.get_wikidata_date(page, 'P570')

    def get_coords(self, page):
        try:
            item = pywikibot.ItemPage.fromPage(page)
            for wb_item in item.claims['P625']:
                return wb_item.target.lat, wb_item.target.lon
        except (KeyError, IndexError, AttributeError):
            pass

    def get_wikidata_date(self, page, prop):
        try:
            item = pywikibot.ItemPage.fromPage(page)
            for wb_item in item.claims[prop]:
                if 'Q1985727' in wb_item.target.calendarmodel:
                    return f'{wb_item.target.day} {MONTH_MAP[wb_item.target.month - 1]} {wb_item.target.year}'
        except (KeyError, IndexError):
            pass

    def get_images_genitive(self, text: str):
        page = self.genitive_search(text)
        try:
            item = pywikibot.ItemPage.fromPage(page)
            wb_item = next(iter(item.claims['P18']), None)
            if wb_item:
                return wb_item.target.get_file_url(url_width=800)
        except (AttributeError, KeyError, IndexError, ValueError):
            pass

    def genitive_search(self, text: str) -> [str, None]:
        morph = pymorphy2.MorphAnalyzer(lang='uk')
        for word in reversed(morph.parse(text)):
            page = self.search_page(word.normal_form)
            if page:
                return page

    def search(self, text: str) -> [str, None]:
        page = self.search_page(text)

        return self.get_page_summary(page)


if __name__ == '__main__':
    parser = WikipediaParser()
    page = parser.genitive_search('Віталій Кличко')
    print(parser.get_gender(page))
