# Single-server deploy: build the React app, then serve it from FastAPI (stub mode).

# --- Stage 1: build the frontend ---
FROM node:20-slim AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# --- Stage 2: Python backend serving frontend/dist ---
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MODEL_MODE=stub
WORKDIR /app
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY backend/ backend/
COPY --from=frontend /app/frontend/dist frontend/dist

# Run as a non-root user.
RUN useradd -m -u 1000 user && chown -R user /app
USER user

WORKDIR /app/backend
EXPOSE 7860
# One worker: session memory lives in this process (app/memory.py).
# Render sets PORT; 7860 is the local default.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860} --workers 1"]
