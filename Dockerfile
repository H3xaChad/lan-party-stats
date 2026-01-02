FROM python:3.13-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml ./

RUN uv venv /opt/venv && \
    uv pip install --python /opt/venv/bin/python --no-cache -r pyproject.toml --extra web

FROM python:3.13-slim

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv

COPY main.py web_main.py ./
COPY src/ ./src/
COPY static/ ./static/
COPY templates/ ./templates/

RUN mkdir -p /data && \
    useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app /data

USER appuser

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DATABASE_PATH=/data/stats.db

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

CMD ["python", "main.py"]
