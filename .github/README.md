# GitHub Actions Workflows

This project uses GitHub Actions for complete CI/CD automation with the following capabilities:

## 🚀 Available Workflows

### 1. **Test Suite** (`test.yml`)
**Trigger:** Push and PR to `main` and `develop`

- ✅ Tests on multiple Python versions (3.11, 3.12)
- 🧪 Unit and integration tests
- 📊 Coverage report with Codecov
- 🐳 Docker build verification

### 2. **Code Quality** (`quality.yml`)
**Trigger:** Push and PR to `main` and `develop`

- 🔧 Formatting with ruff
- 🧹 Linting with ruff
- 🔍 Type checking with mypy
- 🔒 Security checks with bandit

### 3. **Build and Deploy** (`build-and-deploy.yml`)
**Trigger:** Push to `main` and PRs

- 📦 Multi-architecture build (linux/amd64, linux/arm64)
- 🚀 Automatic push to Docker Hub
- 📋 Mandatory prior tests
- 🏷️ Smart tagging by branch

### 4. **PR Review** (`pr-review.yml`)
**Trigger:** Pull Requests to `main`

- 📝 Automatic change review
- 🧪 Complete quality verification
- 🐳 Docker build test
- 📊 Summary of changes and new features

### 5. **Release** (`docker-release.yml`)
**Trigger:** Release creation

- 🎯 Build for official releases
- 🏷️ Automatic semantic versioning
- 📋 Complete pre-release tests
- 📄 Automatic Docker Hub update

## 🔧 Local Configuration

### Install development tools:
```bash
# Install development dependencies
uv sync --all-extras --dev

# Configure pre-commit hooks
uv run pre-commit install
```

### Validate before commit:
```bash
# Run all validations
python scripts/validate.py

# Or manually:
uv run ruff format .
uv run ruff check .
uv run mypy src/
uv run python scripts/run_tests.py --unit --verbose
```

## 🐳 Multi-Architecture Docker

All workflows build images for:
- **linux/amd64** (Intel/AMD x64)
- **linux/arm64** (Apple Silicon, ARM64)

### Automatic tags:
- `latest` - Latest version from main
- `main-{sha}` - Specific commit from main
- `v1.2.3` - Releases with semantic versioning
- `pr-123` - Pull requests for testing

## 📋 Environment Variables

Configure these secrets in GitHub:

```bash
DOCKERHUB_USERNAME  # Docker Hub username
DOCKERHUB_TOKEN     # Docker Hub token
CODECOV_TOKEN       # Codecov token (optional)
```

## 🚀 New Features

GitHub Actions are optimized for the new karma-mcp v0.5.0 with:

- 🔍 **Multi-cluster search by alert name** (`get_alert_details_multi_cluster`)
- 🐳 **Container-based alert search** (`search_alerts_by_container`)
- 🌐 **Enhanced REST API** endpoints
- 🚀 **Full MCP protocol** support

## 📊 Metrics and Monitoring

- **Build time:** ~3-5 minutes average
- **Test coverage:** Automatically reported
- **Security scans:** On every PR
- **Multi-platform builds:** Parallelized for efficiency

## 🔄 Development Workflow

1. **Local development:** `scripts/validate.py`
2. **Create PR:** Automatic trigger of `pr-review.yml`
3. **Merge to main:** Automatic build and deploy
4. **Create release:** Complete release with semantic versioning

Everything automated for maximum efficiency! 🎉