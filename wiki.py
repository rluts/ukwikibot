import re
from datetime import date
from urllib.parse import unquote

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

    def get_birthday(self, page):
        try:
            item = pywikibot.ItemPage.fromPage(page)
            for wb_item in item.claims['P569']:
                if 'Q1985727' in wb_item.target.calendarmodel:
                    return f'{wb_item.target.day} {MONTH_MAP[wb_item.target.month - 1]} {wb_item.target.year}'
        except (KeyError, IndexError):
            pass

    def search(self, text: str) -> [str, None]:
        page = self.search_page(text)

        return self.get_page_summary(page)


if __name__ == '__main__':
    parser = WikipediaParser()
    page = parser.search_page('Джордж Буш старший')
    print(page)
    print(parser.get_birthday(page))
