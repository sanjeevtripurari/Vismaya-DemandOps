# Multi-stage Dockerfile optimized for layer caching
FROM python:3.11-slim as base

# Set working directory
WORKDIR /app

# Install system dependencies (cached layer - rarely changes)
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    python3-venv \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create virtual environment (cached layer - rarely changes)
RUN python -m venv /opt/venv

# Ensure venv Python and pip are used by default
ENV PATH="/opt/venv/bin:$PATH"
ENV DOCKER_CONTAINER=1

# ============================================
# Dependencies stage (cached when requirements.txt unchanged)
# ============================================
FROM base as dependencies

# Copy only requirements file (for better caching)
COPY requirements.txt .

# Install Python dependencies in virtual environment (cached layer)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Create app-level virtual environment for detection (cached layer)
RUN python -m venv venv && \
    ./venv/bin/pip install --no-cache-dir --upgrade pip && \
    ./venv/bin/pip install --no-cache-dir -r requirements.txt

# ============================================
# Application stage (rebuilt when code changes)
# ============================================
FROM dependencies as application

# Create non-root user first (cached layer)
RUN useradd -m -u 1000 appuser

# Copy application code (this layer rebuilds when code changes)
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run the application using the virtual environment
CMD ["/opt/venv/bin/python", "app.py"]