#!/bin/bash
set -e

echo "Running database migrations..."
python3 -m alembic upgrade head

echo "Starting API server..."
exec python3 -m uvicorn app.main:app --host 0.0.0.0 --port 9527 --lifespan on
