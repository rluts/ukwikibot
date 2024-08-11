FROM python:3.12.4-slim

WORKDIR /home/ukwikibot/src
COPY . .
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y sudo bash vim curl libffi-dev gcc
ENV CRYPTOGRAPHY_DONT_BUILD_RUST=1
RUN pip install poetry
RUN poetry config virtualenvs.create false && poetry install --without dev,test --no-root && rm -rf "$POETRY_CACHE_DIR"
CMD ["poetry", "run", "python", "run.py"]