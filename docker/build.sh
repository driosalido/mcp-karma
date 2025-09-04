#!/bin/bash
# Build script for Karma MCP Server Docker image

set -e

# Variables
IMAGE_NAME="karma-mcp"
VERSION=${1:-"latest"}
BUILD_ARGS=""

echo "🐳 Building Karma MCP Server Docker image..."
echo "   Image: ${IMAGE_NAME}:${VERSION}"
echo ""

# Build the image from parent directory
docker build \
  -f docker/Dockerfile \
  -t "${IMAGE_NAME}:${VERSION}" \
  -t "${IMAGE_NAME}:latest" \
  ${BUILD_ARGS} \
  ..

echo ""
echo "✅ Build completed successfully!"
echo ""
echo "📋 Image information:"
docker images "${IMAGE_NAME}" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"

echo ""
echo "🚀 To run the container:"
echo "   docker run -e KARMA_URL=http://your-karma-url:8080 ${IMAGE_NAME}:${VERSION}"
echo ""
echo "🔧 To run with docker-compose:"
echo "   docker-compose up -d"