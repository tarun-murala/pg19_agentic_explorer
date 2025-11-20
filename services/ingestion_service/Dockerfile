FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY services/ingestion_service/requirements.txt services/ingestion_service/requirements.txt
COPY shared shared
RUN pip install --no-cache-dir -r services/ingestion_service/requirements.txt \
    && pip install --no-cache-dir -e shared/clients/llm_client

COPY services/ingestion_service/app services/ingestion_service/app

WORKDIR /app/services/ingestion_service
ENV PYTHONPATH=/app:/app/services/ingestion_service:$PYTHONPATH

EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
