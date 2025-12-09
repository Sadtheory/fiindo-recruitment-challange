# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY tests/ ./tests/
COPY data/ ./data/
COPY alembic/ ./alembic/
COPY README.md .
COPY .env .

# Create directories
RUN mkdir -p db logs

#
WORKDIR /app/src

# Set default command
CMD ["python", "step1_fetch.py"]