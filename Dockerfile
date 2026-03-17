FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
COPY schemas ./schemas
COPY rules ./rules

RUN python -m pip install --upgrade pip && \
    python -m pip install .

RUN useradd --create-home --shell /bin/bash appuser && \
    mkdir -p /app/output /app/runs /app/scenarios /app/custom_schemas && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["uvicorn", "data_forge.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
