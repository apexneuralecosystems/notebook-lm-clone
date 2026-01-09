#!/bin/bash
set -e

echo "=========================================="
echo "Starting NotebookLM Backend"
echo "=========================================="

# Run database migrations
echo "=========================================="
echo "Running database migrations..."
echo "=========================================="
if uv run alembic upgrade head; then
    echo "✅ Migrations completed successfully"
else
    echo "⚠️  Migration failed or already up-to-date"
    echo "Continuing with server startup..."
fi

echo "=========================================="
echo "Starting FastAPI server..."
echo "=========================================="
echo "Backend will listen on: ${BACKEND_HOST:-0.0.0.0}:${BACKEND_PORT:-8000}"
echo "=========================================="

# Start the FastAPI application
exec uv run uvicorn app.api:app \
    --host "${BACKEND_HOST:-0.0.0.0}" \
    --port "${BACKEND_PORT:-8000}" \
    --loop asyncio

