# Karma MCP Server - Modern task runner with Just
# https://github.com/casey/just

# Variables
python := "python3"
uv := "uv"
docker_image := "driosalido/karma-mcp"
docker_tag := "latest"
karma_url := env_var_or_default("KARMA_URL", "http://localhost:8080")

# Default command - show available recipes
default:
    @just --list

# === Installation ===

# Install dependencies
install:
    {{uv}} sync --all-extras
    @echo "✅ Dependencies installed"

# Install development dependencies
install-dev:
    {{uv}} sync --all-extras --dev
    @echo "✅ Development dependencies installed"

# === Testing ===

# Run all tests
test:
    {{uv}} run pytest tests/ -v

# Run only unit tests
test-unit:
    {{uv}} run pytest tests/unit/ -v

# Run only integration tests (requires KARMA_URL)
test-integration:
    KARMA_URL={{karma_url}} {{uv}} run pytest tests/integration/ -v

# Run tests with coverage
test-coverage:
    {{uv}} run pytest --cov=src/karma_mcp --cov-report=html --cov-report=term-missing tests/
    @echo "📊 Coverage report generated in htmlcov/"

# Test specific MCP tools
test-mcp-tools:
    {{uv}} run pytest tests/unit/test_mcp_tools.py -v

# === Code Quality ===

# Run linting checks
lint:
    {{uv}} run ruff check src/ tests/

# Format code
format:
    {{uv}} run ruff format src/ tests/
    @echo "✅ Code formatted"

# Run type checking
type-check:
    {{uv}} run mypy src/

# Run all quality checks
check: lint type-check test-unit
    @echo "✅ All checks passed"

# === Development ===

# Run MCP server locally for testing
serve-mcp:
    KARMA_URL={{karma_url}} {{uv}} run python -m karma_mcp.server

# Debug Karma API responses
debug-karma:
    KARMA_URL={{karma_url}} {{uv}} run python -c 'import asyncio; from karma_mcp.server import check_karma; asyncio.run(check_karma())'

# === Docker ===

# Build Docker image for multiple platforms
docker-build:
    docker buildx build --platform linux/amd64,linux/arm64 -t {{docker_image}}:{{docker_tag}} -f docker/Dockerfile . --push

# Build Docker image locally
docker-build-local:
    docker buildx build -t {{docker_image}}:{{docker_tag}} -f docker/Dockerfile . --load

# Run Docker image locally
docker-run:
    docker run --rm -p 8080:8080 -e KARMA_URL={{karma_url}} {{docker_image}}:{{docker_tag}}

# Test Docker image
docker-test:
    docker run --rm {{docker_image}}:{{docker_tag}} python -m pytest tests/unit/ -v

# === Kubernetes/Helm ===

# Install Helm chart (requires kubectl context)
helm-install:
    helm install karma-mcp ./helm/karma-mcp -n monitoring --create-namespace

# Upgrade Helm chart
helm-upgrade:
    helm upgrade karma-mcp ./helm/karma-mcp -n monitoring

# Uninstall Helm chart
helm-uninstall:
    helm uninstall karma-mcp -n monitoring

# === Cleanup ===

# Clean up generated files
clean:
    rm -rf htmlcov/
    rm -rf .coverage
    rm -rf .pytest_cache/
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete
    @echo "🧹 Cleaned up generated files"

# Clean up Docker images
clean-docker:
    docker image prune -f
    @echo "🐳 Docker images cleaned"

# === Utilities ===

# Show current version
version:
    @echo "Karma MCP Server"
    @grep -E '^version = ' pyproject.toml | head -1
    @echo "Docker image: {{docker_image}}:{{docker_tag}}"

# Validate configuration files
validate:
    @echo "Validating pyproject.toml..."
    @{{python}} -c "import tomllib; tomllib.load(open('pyproject.toml', 'rb'))" && echo "✅ pyproject.toml is valid"

# Set up development environment
dev-setup: install-dev
    @echo "🚀 Development environment ready!"
    @echo ""
    @echo "Next steps:"
    @echo "  just test-unit     # Run unit tests"
    @echo "  just serve-mcp     # Start MCP server"
    @echo "  just check         # Run all checks"

# === CI/CD ===

# Run tests in CI environment
ci-test:
    {{uv}} run pytest --cov=src/karma_mcp --cov-report=xml --cov-report=term-missing -v

# Run quality checks for CI
ci-quality: lint type-check
    @echo "✅ Quality checks completed"

# === Karma Integration ===

# Quick test with real Karma server (requires port-forward)
test-with-karma:
    @echo "Testing with Karma at {{karma_url}}"
    KARMA_URL={{karma_url}} {{uv}} run python scripts/test_karma.py