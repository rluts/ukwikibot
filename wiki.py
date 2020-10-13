import re
from urllib.parse import unquote

import pywikibot
import requests


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

    def summary(self, title):
        # TODO: rework to pywikibot
        params = {
            'action': 'query',
            'prop': 'extracts',
            'exsentences': 7,
            'explaintext': 1,
            'format': 'json',
            'titles': title.title()
        }
        response = requests.get(f'https://uk.wikipedia.org/w/api.php', params=params)
        if response.status_code == 200:
            try:
                return self.parse_text(next(iter(response.json()['query']['pages'].values()), None)['extract'])
            except (KeyError, TypeError):
                pass

    @staticmethod
    def parse_text(text):
        return re.sub('={2,} ?(.+?)={2,}', r'<b>\1</b>', text)

    def search_and_parse(self, text):
        page = self.search_page(text)

        html = self.summary(page)
        link = f'<a href="{unquote(page.full_url())}">Читати у Вікіпедії</a>'

        return f'{html}\n\n{link}'


if __name__ == '__main__':
    parser = WikipediaParser()
    text = parser.search_and_parse('Шевченко')
