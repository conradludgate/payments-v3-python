FROM python:3.9

WORKDIR /code

RUN apt-get update && apt-get install openssl ca-certificates -y \
    && curl -sSL https://install.python-poetry.org | python3 -

COPY pyproject.toml poetry.lock /code/
RUN /root/.local/bin/poetry install --no-dev --no-interaction --no-root

COPY app /code/app
COPY templates /code/templates

CMD ["/root/.local/bin/poetry", "run", "start"]
