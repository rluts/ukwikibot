FROM python:3.12-alpine

WORKDIR /home/ukwikibot/src
COPY . .
RUN apk add build-base libressl-dev musl-dev libffi-dev curl vim cargo
ENV CRYPTOGRAPHY_DONT_BUILD_RUST=1
RUN pip install poetry
RUN poetry config virtualenvs.create false && poetry install --without dev,test --no-root && rm -rf "$POETRY_CACHE_DIR"
CMD ["poetry", "run", "python", "run.py"]