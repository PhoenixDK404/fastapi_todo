FROM python:3.12-slim AS builder

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    git && \
    pip install poetry && \
    rm -rf /var/lib/apt/lists/*

ENV POETRY_VIRTUALENVS_IN_PROJECT=fal se
ENV POETRY_VIRTUALENVS_PATH="/opt/venv"
ENV POETRY_NO_INTERACTION=1

WORKDIR /app

COPY . .


RUN poetry lock
RUN poetry install --only main --no-root

FROM python:3.12-slim AS production

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY --from=builder /opt/venv /opt/venv

COPY app app
COPY *.py .


EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD ["curl", "-f", "http://localhost:8000/"]

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]