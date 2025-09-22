# Dockerfile para Railway - Sistema de Gestão de Frotas (Backend)
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY backend_fastapi/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend_fastapi/app app

# Create uploads directory
RUN mkdir -p /app/uploads

# Expose port (Railway will set PORT environment variable)
EXPOSE $PORT

# Start command (Railway will use $PORT environment variable)
CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT
