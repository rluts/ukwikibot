import logging

from wikibot.bot import app

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("pymorphy3").setLevel(logging.WARNING)
logging.getLogger("hpack").setLevel(logging.WARNING)
logging.basicConfig(
    level=logging.DEBUG,
)

if __name__ == "__main__":
    app.run_polling()
