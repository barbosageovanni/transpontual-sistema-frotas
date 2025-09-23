FROM python:3.11-slim

# Force cache bust
RUN echo "Cache bust: $(date)" > /tmp/cachebust

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /app
RUN ls -la /app

# Create uploads directory
RUN mkdir -p /app/uploads

# Expose port (Railway will set PORT environment variable at runtime)
EXPOSE 8000

# Start command - test basic functionality first
CMD ["ls", "-la", "/app"]
