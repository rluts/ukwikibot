FROM python:3.12.4-slim

WORKDIR /home/ukwikibot/src
COPY . .
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y sudo bash vim curl
RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/usr/local python -
RUN poetry config virtualenvs.create false && poetry install --without dev,test --no-root && rm -rf "$POETRY_CACHE_DIR"
CMD ["poetry", "run", "python", "run.py"]