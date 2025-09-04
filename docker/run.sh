#!/bin/bash
# Run script for Karma MCP Server Docker container

set -e

# Variables
IMAGE_NAME="karma-mcp"
VERSION=${1:-"latest"}
CONTAINER_NAME="karma-mcp-server"
KARMA_URL=${KARMA_URL:-"http://localhost:8080"}

echo "🚀 Running Karma MCP Server Docker container..."
echo "   Image: ${IMAGE_NAME}:${VERSION}"
echo "   Container: ${CONTAINER_NAME}"
echo "   Karma URL: ${KARMA_URL}"
echo ""

# Stop and remove existing container if it exists
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "🛑 Stopping and removing existing container..."
    docker stop "${CONTAINER_NAME}" > /dev/null 2>&1 || true
    docker rm "${CONTAINER_NAME}" > /dev/null 2>&1 || true
fi

# Run the container
docker run -d \
  --name "${CONTAINER_NAME}" \
  --restart unless-stopped \
  -e KARMA_URL="${KARMA_URL}" \
  -e LOG_LEVEL="${LOG_LEVEL:-INFO}" \
  "${IMAGE_NAME}:${VERSION}"

echo "✅ Container started successfully!"
echo ""
echo "📋 Container status:"
docker ps --filter "name=${CONTAINER_NAME}" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "🔍 To view logs:"
echo "   docker logs -f ${CONTAINER_NAME}"
echo ""
echo "🔧 To access container shell:"
echo "   docker exec -it ${CONTAINER_NAME} bash"
echo ""
echo "🛑 To stop container:"
echo "   docker stop ${CONTAINER_NAME}"