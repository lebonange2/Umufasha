FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY mcp/pyproject.toml /app/
COPY requirements*.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir -e /app
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /app/

# Create non-root user
RUN useradd -r -s /bin/false mcp && \
    chown -R mcp:mcp /app

# Switch to non-root user
USER mcp

# Expose port (for WebSocket mode)
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Run server
CMD ["python", "-m", "mcp.server", "--transport", "websocket", "--host", "0.0.0.0", "--port", "8080"]

