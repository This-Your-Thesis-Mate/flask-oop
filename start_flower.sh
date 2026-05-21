#!/bin/bash
# Start Flower dashboard for Celery monitoring

cd "$(dirname "$0")"

# Activate venv if needed
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run Flower
celery -A app.celery_app flower --port=5555
