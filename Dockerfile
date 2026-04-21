# ============================================================================
# Multi-stage build untuk optimasi image size dan security
# ============================================================================

# Stage 1: Builder - Install dependencies
FROM python:3.10-slim as builder

WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies ke virtual environment
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir --upgrade pip setuptools wheel && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# ============================================================================
# Stage 2: Runtime - Minimal production image
# ============================================================================

FROM python:3.10-slim

# Set environment variables untuk Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    # Default values (akan di-override oleh runtime env vars)
    DEBUG=False \
    HOST=0.0.0.0 \
    PORT=5000 \
    FLASK_APP=main.py

# Install system dependencies untuk OCR dan runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libtesseract-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user untuk security
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Copy virtual environment dari builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY --chown=appuser:appuser . .

# Create volume mount points untuk extracted_texts
# Ini memungkinkan data disimpan ke volume, bukan di filesystem container
RUN mkdir -p /app/extracted_texts && \
    chown -R appuser:appuser /app/extracted_texts

# Switch ke non-root user
USER appuser

# Expose port (default 5000, bisa di-override saat runtime)
EXPOSE ${PORT}

# Healthcheck untuk monitoring
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:${PORT}/health', timeout=5)" || exit 1

# Container entry point - baca semua config dari environment variable saat runtime
CMD ["python", "main.py"]