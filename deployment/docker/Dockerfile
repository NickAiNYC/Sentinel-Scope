FROM python:3.12-slim AS base

WORKDIR /app

# Install dependencies first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/api/v1/health')" || exit 1

# Run FastAPI with uvicorn
CMD ["uvicorn", "api.v1.risk_routes:router", "--host", "0.0.0.0", "--port", "8000"]
