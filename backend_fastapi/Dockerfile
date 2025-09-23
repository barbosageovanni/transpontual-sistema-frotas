# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Debug: List all files to see what's being copied
RUN echo "=== DEBUG: Files in /app ==="
RUN ls -la /app
RUN echo "=== DEBUG: Looking for main.py ==="
RUN find /app -name "main.py" -type f || echo "main.py not found!"
RUN echo "=== DEBUG: Python files ==="
RUN find /app -name "*.py" -type f | head -10

# Create uploads directory
RUN mkdir -p uploads

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=utf-8

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run the application (try main.py first, fallback to start.py)
CMD ["python", "start.py"]
