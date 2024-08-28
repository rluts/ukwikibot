import os

import dotenv

dotenv.load_dotenv(override=False)


class Config:
    wiki_disable_auth = os.getenv("WIKI_DISABLE_AUTH", "").lower() in ["true", "1"]
    telegram_token = os.getenv("TELEGRAM_TOKEN", None)
    wiki_consumer_token = os.getenv("WIKI_CONSUMER_TOKEN", None)
    wiki_consumer_secret = os.getenv("WIKI_CONSUMER_SECRET", None)
    wiki_access_token = os.getenv("WIKI_ACCESS_TOKEN", None)
    wiki_access_secret = os.getenv("WIKI_ACCESS_SECRET", None)
    wiki_username = os.getenv("WIKI_USERNAME", None)

    if telegram_token is None:
        raise ValueError("Missing TELEGRAM_TOKEN")
    if not wiki_disable_auth and not all(
        [wiki_consumer_token, wiki_consumer_secret, wiki_access_token, wiki_access_secret, wiki_username]
    ):
        print(wiki_consumer_token, wiki_consumer_secret, wiki_access_token, wiki_access_secret, wiki_username)
        raise ValueError(
            "Missing WIKI_CONSUMER_TOKEN, WIKI_CONSUMER_SECRET, WIKI_ACCESS_TOKEN, WIKI_ACCESS_SECRET or WIKI_USERNAME"
        )


config = Config()
