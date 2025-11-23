FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY services/orchestrator_service/requirements.txt services/orchestrator_service/requirements.txt
COPY shared shared
RUN pip install --no-cache-dir -r services/orchestrator_service/requirements.txt \
    && pip install --no-cache-dir -e shared/clients/llm_client

COPY services/orchestrator_service/app services/orchestrator_service/app
COPY services/orchestrator_service/.env.example services/orchestrator_service/.env.example

WORKDIR /app/services/orchestrator_service
ENV PYTHONPATH=/app:$PYTHONPATH

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
