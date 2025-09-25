# flask_dashboard/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including gcc for some Python packages
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements-dashboard.txt requirements.txt
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code from current directory (flask_dashboard)
COPY . .

# Create uploads directory and set permissions
RUN mkdir -p /app/uploads
RUN chmod 755 /app/uploads

# Create non-root user for security
RUN useradd -m -u 1001 appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose port (Railway will set PORT environment variable)
EXPOSE 8050

# Start command with container test
CMD ["python", "test_container.py"]