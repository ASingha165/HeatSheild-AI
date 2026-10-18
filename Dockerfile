# Multi-stage Dockerfile for HeatShield AI production deployment

# Stage 1: Build React + Vite Frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# Stage 2: Production Python Runtime
FROM python:3.12-slim AS production
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install backend Python dependencies
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r backend/requirements.txt

# Copy backend source code
COPY backend/ ./backend/
COPY pytest.ini ./

# Copy compiled frontend distribution from Stage 1
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Production environment configuration
ENV HOST=0.0.0.0
ENV PORT=8000
ENV ENVIRONMENT=production
ENV DECIDER_MODEL_CHECKPOINT=StrandsAgents/strands-decider-2B-hobson-v21
ENV DECIDER_DEVICE=cpu
ENV AWS_REGION=us-east-1
ENV BEDROCK_MODEL_ID=global.amazon.nova-2-lite-v1:0
ENV ENABLE_DEV_MODE=true

EXPOSE 8000

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=45s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Start production ASGI server
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
