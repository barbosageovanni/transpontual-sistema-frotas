FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app app
COPY main.py .

# Create uploads directory
RUN mkdir -p /app/uploads

# Expose port (Railway will set PORT environment variable at runtime)
EXPOSE 8000

# Start command using our main.py entry point
CMD ["python", "main.py"]
