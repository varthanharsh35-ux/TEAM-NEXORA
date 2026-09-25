FROM node:24-bookworm-slim AS frontend
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run check:i18n && npm run build

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 LOCAL_LLM=0 APP_ENV=production DATA_DIR=/var/lib/gramsahayak PORT=8000
WORKDIR /app
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY backend/ backend/
COPY data/ data/
COPY models/business_classifier.joblib models/metrics.json models/
COPY --from=frontend /app/frontend/dist frontend/dist
RUN mkdir -p /var/lib/gramsahayak
EXPOSE 8000
CMD ["sh", "-c", "exec python -m uvicorn main:app --app-dir backend --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
