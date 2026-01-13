# =============================================================================
# HuggingFace Spaces Compatible Dockerfile
# Healthcare AI Assistant with Gradio Interface
# =============================================================================
# Stage 1: Builder - Install dependencies
# =============================================================================
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# =============================================================================
# Stage 2: Runtime - Create minimal production image
# =============================================================================
FROM python:3.11-slim

LABEL maintainer="healthcare-chatbot@example.com"
LABEL description="AI-Powered Healthcare Assistant - HuggingFace Spaces"
LABEL version="1.0"

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=appuser:appuser app/ /app/app/
COPY --chown=appuser:appuser frontend/ /app/frontend/
COPY --chown=appuser:appuser app_gradio.py /app/
COPY --chown=appuser:appuser start.sh /app/
COPY --chown=appuser:appuser seed_comprehensive_data.py /app/
COPY --chown=appuser:appuser .env /app/ 2>/dev/null || echo "No .env file"

# Make start script executable
RUN chmod +x /app/start.sh

# Create necessary directories
RUN mkdir -p /app/logs /app/.chroma /app/data && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose HuggingFace Spaces port (7860)
EXPOSE 7860

# Health check on Gradio port
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:7860/ || exit 1

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ENVIRONMENT=production \
    API_URL=http://localhost:8001 \
    GRADIO_SERVER_NAME=0.0.0.0 \
    GRADIO_SERVER_PORT=7860

# Run startup script (starts both FastAPI and Gradio)
CMD ["/bin/bash", "/app/start.sh"]
