FROM python:3.11-slim

# Force cache invalidation with timestamp
RUN echo "Build timestamp: $(date)" > /build_info.txt

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements-dashboard.txt requirements.txt
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy ALL project files
COPY . .

# Change to flask_dashboard directory
WORKDIR /app/flask_dashboard

# Create uploads directory and set permissions
RUN mkdir -p /app/uploads
RUN chmod 755 /app/uploads

# Create non-root user for security
RUN useradd -m -u 1001 appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose port (Railway will set PORT at runtime)
EXPOSE 8000

# Start command with container test
CMD ["python", "test_container.py"]