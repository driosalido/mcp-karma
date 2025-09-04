# GitHub Actions Workflows

Este proyecto utiliza GitHub Actions para automatización de CI/CD completa con las siguientes capacidades:

## 🚀 Workflows Disponibles

### 1. **Test Suite** (`test.yml`)
**Trigger:** Push y PR a `main` y `develop`

- ✅ Tests en múltiples versiones de Python (3.11, 3.12)
- 🧪 Tests unitarios e integración
- 📊 Reporte de cobertura con Codecov
- 🐳 Verificación de build Docker

### 2. **Code Quality** (`quality.yml`)
**Trigger:** Push y PR a `main` y `develop`

- 🔧 Formateo con ruff
- 🧹 Linting con ruff
- 🔍 Type checking con mypy
- 🔒 Security checks con bandit

### 3. **Build and Deploy** (`build-and-deploy.yml`)
**Trigger:** Push a `main` y PRs

- 📦 Build multi-arquitectura (linux/amd64, linux/arm64)
- 🚀 Push automático a Docker Hub
- 📋 Tests previos obligatorios
- 🏷️ Tagging inteligente por branch

### 4. **PR Review** (`pr-review.yml`)
**Trigger:** Pull Requests a `main`

- 📝 Review automático de cambios
- 🧪 Verificación completa de calidad
- 🐳 Test de build Docker
- 📊 Resumen de cambios y nuevas funciones

### 5. **Release** (`docker-release.yml`)
**Trigger:** Creación de releases

- 🎯 Build para releases oficiales
- 🏷️ Semantic versioning automático
- 📋 Tests completos pre-release
- 📄 Actualización automática de Docker Hub

## 🔧 Configuración Local

### Instalar herramientas de desarrollo:
```bash
# Instalar dependencias de desarrollo
uv sync --all-extras --dev

# Configurar pre-commit hooks
uv run pre-commit install
```

### Validar antes de commit:
```bash
# Ejecutar todas las validaciones
python scripts/validate.py

# O manualmente:
uv run ruff format .
uv run ruff check .
uv run mypy src/
uv run python scripts/run_tests.py --unit --verbose
```

## 🐳 Docker Multi-Arquitectura

Todos los workflows construyen imágenes para:
- **linux/amd64** (Intel/AMD x64)
- **linux/arm64** (Apple Silicon, ARM64)

### Tags automáticos:
- `latest` - Última versión de main
- `main-{sha}` - Commit específico de main
- `v1.2.3` - Releases con semantic versioning
- `pr-123` - Pull requests para testing

## 📋 Variables de Entorno

Configura estos secrets en GitHub:

```bash
DOCKERHUB_USERNAME  # Usuario de Docker Hub
DOCKERHUB_TOKEN     # Token de Docker Hub
CODECOV_TOKEN       # Token de Codecov (opcional)
```

## 🚀 Nuevas Funcionalidades

Las GitHub Actions están optimizadas para el nuevo karma-mcp v0.5.0 con:

- 🔍 **Multi-cluster search by alert name** (`get_alert_details_multi_cluster`)
- 🐳 **Container-based alert search** (`search_alerts_by_container`)
- 🌐 **Enhanced REST API** endpoints
- 🚀 **Full MCP protocol** support

## 📊 Métricas y Monitoring

- **Build time:** ~3-5 minutos promedio
- **Test coverage:** Reportado automáticamente
- **Security scans:** En cada PR
- **Multi-platform builds:** Paralelizados para eficiencia

## 🔄 Workflow de Desarrollo

1. **Desarrollo local:** `scripts/validate.py`
2. **Create PR:** Trigger automático de `pr-review.yml`
3. **Merge to main:** Build y deploy automático
4. **Create release:** Release completo con semantic versioning

¡Todo automatizado para máxima eficiencia! 🎉