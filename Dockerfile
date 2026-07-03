# Multi-stage Dockerfile for UAE Job Intelligence Platform
FROM python:3.11-slim as base

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY migrations/ ./migrations/

# Create logs directory
RUN mkdir -p /app/logs

# --- Ingestion Service Stage ---
FROM base as ingestion
CMD ["python", "-m", "src.ingestion.main"]

# --- API Service Stage ---
FROM base as api
EXPOSE 8000
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

# --- Dashboard Service Stage ---
FROM base as dashboard
EXPOSE 8501
CMD ["streamlit", "run", "src/dashboard/main.py", "--server.port=8501", "--server.address=0.0.0.0"]
