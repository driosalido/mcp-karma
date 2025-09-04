# Multi-stage Docker build for Karma MCP Server
# Stage 1: Build environment
FROM python:3.12-slim as builder

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies to virtual environment
RUN uv sync --frozen --no-dev --no-install-project

# Stage 2: Runtime environment
FROM python:3.12-slim as runtime

# Create non-root user for security
RUN groupadd -r karma && useradd -r -g karma karma

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY src/ ./src/
COPY README.md LICENSE ./

# Change ownership to non-root user
RUN chown -R karma:karma /app

# Switch to non-root user
USER karma

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src"
ENV KARMA_URL=""

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Expose port for HTTP server
EXPOSE 8080

# Default command - run HTTP server (use MCP_MODE=stdio for stdio mode)
CMD ["python", "-m", "karma_mcp.http_server"]