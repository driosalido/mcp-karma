# Makefile for Karma MCP Server

.PHONY: help install test test-unit test-integration test-all lint type-check coverage clean docker docker-build docker-run

# Default target
.DEFAULT_GOAL := help

# Variables
PYTHON := python
UV := uv
DOCKER_IMAGE := driosalido/karma-mcp
DOCKER_TAG := latest

help: ## Show this help message
	@echo "Karma MCP Server - Available commands:"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*##/ {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install dependencies
	$(UV) pip install -e ".[test]"

install-dev: ## Install development dependencies  
	$(UV) pip install -e ".[test]"
	@echo "✅ Development dependencies installed"

test: ## Run all tests
	$(PYTHON) scripts/run_tests.py --verbose

test-unit: ## Run only unit tests
	$(PYTHON) scripts/run_tests.py --unit --verbose

test-integration: ## Run only integration tests (requires KARMA_URL)
	$(PYTHON) scripts/run_tests.py --integration --verbose --karma-url $(KARMA_URL)

test-with-karma: ## Run integration tests with local Karma
	$(PYTHON) scripts/run_tests.py --integration --verbose --karma-url http://localhost:8080

test-all: ## Run all tests with coverage
	$(PYTHON) scripts/run_tests.py --all --coverage --verbose

coverage: ## Generate coverage report
	$(PYTHON) -m pytest --cov=src/karma_mcp --cov-report=html --cov-report=term-missing
	@echo "📊 Coverage report generated in htmlcov/"

lint: ## Run linting checks
	$(PYTHON) scripts/run_tests.py --lint

type-check: ## Run type checking
	$(PYTHON) scripts/run_tests.py --type-check

format: ## Format code (if ruff is available)
	@if command -v ruff >/dev/null 2>&1; then \
		ruff format src/ tests/; \
		echo "✅ Code formatted"; \
	else \
		echo "⚠️  ruff not found - install with: pip install ruff"; \
	fi

check: ## Run all checks (lint, type-check, test)
	$(PYTHON) scripts/run_tests.py --all --verbose

# Test individual components
test-mcp-tools: ## Test MCP tools specifically
	$(PYTHON) -m pytest tests/unit/test_mcp_tools.py -v

test-http-server: ## Test HTTP server specifically  
	$(PYTHON) -m pytest tests/unit/test_http_server.py -v

test-e2e: ## Test end-to-end functionality
	$(PYTHON) -m pytest tests/integration/test_http_server_e2e.py -v

# Manual testing
test-manual: ## Run manual test scripts
	@echo "Running manual tests..."
	KARMA_URL=http://localhost:8080 $(UV) run python tests/manual/test_mcp_tools.py
	KARMA_URL=http://localhost:8080 $(UV) run python tests/manual/test_state_filtering.py

# Development helpers
serve-local: ## Run HTTP server locally for testing
	KARMA_URL=http://localhost:8080 $(UV) run python -m karma_mcp.http_server

serve-mcp: ## Run MCP server locally for testing  
	KARMA_URL=http://localhost:8080 $(UV) run python -m karma_mcp.server

debug-karma: ## Debug Karma API responses
	KARMA_URL=http://localhost:8080 $(UV) run python tests/manual/debug_data.py

# Docker commands
docker-build: ## Build Docker image
	docker buildx build --platform linux/amd64,linux/arm64 -t $(DOCKER_IMAGE):$(DOCKER_TAG) -f docker/Dockerfile . --push

docker-run: ## Run Docker image locally
	docker run --rm -p 8080:8080 -e KARMA_URL=http://localhost:8080 $(DOCKER_IMAGE):$(DOCKER_TAG)

docker-test: ## Test Docker image
	docker run --rm $(DOCKER_IMAGE):$(DOCKER_TAG) python -m pytest tests/unit/ -v

# Kubernetes/Helm commands
helm-install: ## Install Helm chart (requires kubectl context)
	helm install karma-mcp ./helm/karma-mcp -f helm/karma-mcp/values-teddy.yaml -n monitoring

helm-upgrade: ## Upgrade Helm chart
	helm upgrade karma-mcp ./helm/karma-mcp -f helm/karma-mcp/values-teddy.yaml -n monitoring

helm-uninstall: ## Uninstall Helm chart
	helm uninstall karma-mcp -n monitoring

# Cleanup
clean: ## Clean up generated files
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "🧹 Cleaned up generated files"

clean-docker: ## Clean up Docker images
	docker image prune -f
	@echo "🐳 Docker images cleaned"

# CI/CD helpers
ci-test: ## Run tests in CI environment
	$(PYTHON) -m pytest --cov=src/karma_mcp --cov-report=xml --cov-report=term-missing -v

validate-config: ## Validate configuration files
	@echo "Validating pyproject.toml..."
	@$(PYTHON) -c "import tomllib; tomllib.load(open('pyproject.toml', 'rb'))" && echo "✅ pyproject.toml is valid"
	@echo "Validating Helm charts..."
	@helm lint ./helm/karma-mcp/ && echo "✅ Helm chart is valid"

# Documentation
docs: ## Generate documentation (placeholder)
	@echo "📚 Documentation generation not yet implemented"

# Quick development workflow
dev-setup: install-dev ## Set up development environment
	@echo "🚀 Development environment ready!"
	@echo ""
	@echo "Next steps:"
	@echo "  make test-unit     # Run unit tests"
	@echo "  make serve-local   # Start local server"
	@echo "  make test-manual   # Run manual tests"

# Show current version
version: ## Show current version
	@echo "Karma MCP Server"
	@grep version pyproject.toml | head -1
	@echo "Docker image: $(DOCKER_IMAGE):$(DOCKER_TAG)"