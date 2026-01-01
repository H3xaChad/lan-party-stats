# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml setup.py ./

# Install dependencies
RUN pip install --no-cache-dir -e ".[web]"

# Copy application code
COPY . .

# Create directory for database and logs
RUN mkdir -p /data

# Expose web server port
EXPOSE 5000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DATABASE_PATH=/data/stats.db

# Default command (can be overridden in docker-compose)
CMD ["python", "web_main.py"]
