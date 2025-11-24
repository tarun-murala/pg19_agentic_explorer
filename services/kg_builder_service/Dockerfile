FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY services/kg_builder_service/requirements.txt services/kg_builder_service/requirements.txt
COPY shared shared
RUN pip install --no-cache-dir -r services/kg_builder_service/requirements.txt \
    && pip install --no-cache-dir -e shared/clients/llm_client

COPY services/kg_builder_service/app services/kg_builder_service/app
COPY services/kg_builder_service/.env.example services/kg_builder_service/.env.example

WORKDIR /app/services/kg_builder_service
ENV PYTHONPATH=/app:$PYTHONPATH

EXPOSE 8002

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
