# Docker Configuration for Karma MCP Server

This directory contains Docker configuration and utilities for containerizing the Karma MCP Server.

## 🐳 Quick Start

### 1. Build the Docker Image

```bash
# Build with latest tag
./docker/build.sh

# Build with specific version
./docker/build.sh v1.0.0
```

### 2. Run with Docker Compose (Recommended)

```bash
# Copy environment template
cp docker/.env.docker .env

# Edit .env with your Karma URL
# KARMA_URL=http://your-karma-instance:8080

# Start services (from project root)
docker-compose -f docker/docker-compose.yml up -d

# View logs
docker-compose -f docker/docker-compose.yml logs -f karma-mcp
```

### 3. Run with Docker directly

```bash
# Run with default settings
KARMA_URL=http://localhost:8080 ./docker/run.sh

# Run with custom settings
KARMA_URL=http://your-karma:8080 LOG_LEVEL=DEBUG ./docker/run.sh
```

## 📁 Files Overview

### Core Files
- **`Dockerfile`** - Multi-stage Docker build configuration
- **`.dockerignore`** - Excludes unnecessary files from build context
- **`docker-compose.yml`** - Complete stack with Karma MCP + example Karma service

### Utilities
- **`docker/build.sh`** - Build script with versioning support
- **`docker/run.sh`** - Run script with environment configuration
- **`.env.docker`** - Environment template for Docker Compose

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `KARMA_URL` | Karma Alert Dashboard URL | `http://karma:8080` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |

### Docker Build Features

- ✅ **Multi-stage build** - Optimized image size
- ✅ **Non-root user** - Enhanced security
- ✅ **Health checks** - Container monitoring
- ✅ **UV package manager** - Fast dependency installation
- ✅ **Minimal base image** - Python 3.12 slim

## 🚀 Usage Scenarios

### Development Mode

```bash
# Build and run for development (from project root)
docker-compose -f docker/docker-compose.yml up --build

# With volume mounting (uncomment in docker/docker-compose.yml)
# This allows live code changes without rebuilding
```

### Production Mode

```bash
# Build production image
./docker/build.sh v1.0.0

# Tag for registry
docker tag karma-mcp:v1.0.0 your-registry/karma-mcp:v1.0.0

# Push to registry
docker push your-registry/karma-mcp:v1.0.0
```

### Testing Mode

```bash
# Run with test Karma instance (from project root)
KARMA_URL=http://test-karma:8080 docker-compose -f docker/docker-compose.yml up
```

## 🔍 Monitoring & Debugging

### Health Checks

The container includes health checks that verify:
- Karma connectivity via `check_karma` tool
- Container responds within 10 seconds
- Checks every 30 seconds

### View Logs

```bash
# Real-time logs
docker logs -f karma-mcp-server

# Or with docker-compose (from project root)
docker-compose -f docker/docker-compose.yml logs -f karma-mcp
```

### Access Container Shell

```bash
# Interactive shell
docker exec -it karma-mcp-server bash

# Check MCP tools manually
docker exec -it karma-mcp-server python -c "
import sys; sys.path.append('/app/src')
from karma_mcp.server import check_karma
import asyncio
print(asyncio.run(check_karma()))
"
```

## 📊 Image Information

### Image Layers
1. **Base Layer**: Python 3.12 slim
2. **Dependencies**: UV-managed Python packages
3. **Application**: MCP server source code
4. **Security**: Non-root user configuration

### Typical Image Size
- **Production image**: ~200-300 MB
- **Development image**: ~400-500 MB

## 🔒 Security Features

- **Non-root user** (karma:karma)
- **Minimal attack surface** (slim base image)
- **No unnecessary packages** in production layer
- **Read-only application code**
- **Health check monitoring**

## 🐛 Troubleshooting

### Common Issues

**Container exits immediately:**
```bash
# Check logs for errors
docker logs karma-mcp-server

# Verify KARMA_URL is accessible
curl -I http://your-karma-url:8080/health
```

**Health check failing:**
```bash
# Test health check manually
docker exec karma-mcp-server python -c "
import sys; sys.path.append('/app/src')
from karma_mcp.server import check_karma
import asyncio
print(asyncio.run(check_karma()))
"
```

**Connection refused:**
```bash
# Verify network connectivity
docker exec karma-mcp-server ping karma
docker exec karma-mcp-server curl -I http://karma:8080/health
```

### Debug Mode

```bash
# Run with debug logging
LOG_LEVEL=DEBUG docker-compose up

# Run with interactive mode
docker run -it --rm \
  -e KARMA_URL=http://your-karma:8080 \
  karma-mcp:latest bash
```