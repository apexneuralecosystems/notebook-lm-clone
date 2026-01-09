# Backend Dockerfile for NotebookLM API
# Uses Python 3.11 with uv for fast dependency management

FROM python:3.11-slim AS base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies using uv
RUN uv sync --frozen --no-dev

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs outputs/podcast_audio uploads qdrant_db

# Copy and set permissions for entrypoint script
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Expose port (EXPOSE is informational - actual port comes from BACKEND_PORT env var)
# Default to 8000, but can be overridden via environment variable at runtime
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Set backend host and port from environment variables (can be overridden at runtime)
# BACKEND_PORT defaults to 8000 if not set - runtime env vars will override this
ENV BACKEND_PORT=8000
ENV BACKEND_HOST=0.0.0.0

# Health check - uses BACKEND_PORT environment variable (defaults to 8000)
# NOTE: 'localhost' is correct here - health checks run INSIDE the container
# and check if the service is listening on the container's own network interface
# This is the standard Docker health check pattern for production
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD sh -c 'curl -f http://localhost:${BACKEND_PORT:-8000}/health || exit 1'

# Use entrypoint script that runs migrations before starting server
# The entrypoint script will:
# 1. Wait for database to be ready
# 2. Run database migrations (alembic upgrade head)
# 3. Start the FastAPI server
ENTRYPOINT ["/docker-entrypoint.sh"]

