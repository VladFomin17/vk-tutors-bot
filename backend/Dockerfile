FROM python:3.13-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app app \
    && mkdir -p /data/media && chown app:app /data/media

COPY pyproject.toml alembic.ini logging.json ./
COPY app ./app
COPY alembic ./alembic

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install . && chown -R app:app /app

FROM base AS test

COPY tests ./tests
RUN --mount=type=cache,target=/root/.cache/pip pip install ".[dev]"

USER app

CMD ["pytest", "-q"]

FROM base AS runtime

USER app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-config", "logging.json"]
