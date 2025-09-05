# 🚨 Karma MCP Server

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![MCP Protocol](https://img.shields.io/badge/MCP-Protocol-green.svg)](https://modelcontextprotocol.io/)
[![Docker Support](https://img.shields.io/badge/Docker-Supported-blue.svg)](https://www.docker.com/)

**Bring AI-powered intelligence to your Kubernetes alerts.** Karma MCP Server enables Claude to directly interact with your [Karma Alert Dashboard](https://github.com/prymitive/karma), providing natural language queries, analysis, and management of Prometheus/Alertmanager alerts.

## 🌟 What is This?

Karma MCP Server is a bridge that connects Claude Desktop (or any MCP-compatible client) to your Karma Alert Dashboard. This allows you to:

- 🗣️ **Ask questions in natural language** about your alerts: *"How many critical alerts are there in production?"*
- 🔍 **Search and filter** across multiple Kubernetes clusters simultaneously
- 📊 **Get instant insights** about alert patterns and trends
- 🚀 **Accelerate incident response** with AI-powered alert analysis
- 🔄 **Automate routine checks** without leaving your conversation

### Example Interactions with Claude

```
You: "Show me all critical alerts in the production cluster"
Claude: [Lists and analyzes critical alerts with context]

You: "Which pods are crash looping?"
Claude: [Shows KubePodCrashLooping alerts with namespace, pod details, and suggestions]

You: "Search for OOM killed containers across all clusters"
Claude: [Performs multi-cluster search and provides memory optimization tips]
```

## 🎯 Key Features

### Core Alert Management
- ✅ **Real-time alert listing** with severity, state, and cluster information
- ✅ **Multi-cluster support** - search across all your Kubernetes clusters at once
- ✅ **Smart filtering** by cluster, namespace, severity, and alert state
- ✅ **Detailed alert inspection** with annotations, labels, and runbook links
- ✅ **Statistical summaries** showing alert distribution and trends

### Advanced Search Capabilities
- 🔍 **Container-based search** - Find alerts by container name across clusters
- 🔍 **Alert name search** - Search specific alerts across your entire infrastructure  
- 🔍 **Cross-cluster analysis** - Compare alert patterns between environments

### Integration Features
- 🌐 **REST API** for HTTP-based integrations
- 🔄 **MCP Protocol** support for AI assistants
- 🐳 **Docker support** with multi-architecture images
- ☸️ **Kubernetes-ready** with Helm charts included

## 📦 Installation

### Quick Start with Claude Desktop

1. **Install via UV (recommended)**
```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and install
git clone https://github.com/driosalido/karma-mcp.git
cd karma-mcp
uv sync --all-extras
```

2. **Configure Claude Desktop**

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "karma": {
      "command": "uv",
      "args": ["run", "python", "-m", "karma_mcp.server"],
      "cwd": "/path/to/karma-mcp",
      "env": {
        "KARMA_URL": "http://localhost:8080"
      }
    }
  }
}
```

3. **Connect to your Karma instance**
```bash
# If Karma is in Kubernetes
kubectl port-forward svc/karma 8080:80 -n monitoring

# Or set your Karma URL directly
export KARMA_URL=http://your-karma-instance:8080
```

4. **Restart Claude Desktop** and start asking about your alerts!

### Docker Installation

```bash
# Using pre-built image
docker run -d \
  -e KARMA_URL=http://your-karma:8080 \
  -p 8000:8000 \
  driosalido/karma-mcp:latest

# Or build locally
docker build -f docker/Dockerfile -t karma-mcp .
docker run -d -e KARMA_URL=http://karma:8080 karma-mcp
```

### Kubernetes Installation

```bash
# Using Helm
helm install karma-mcp ./helm/karma-mcp \
  --set config.karmaUrl=http://karma.monitoring:80

# Or with kubectl
kubectl apply -f helm/karma-mcp/templates/
```

## 🛠️ Available MCP Tools

The following tools are available for Claude to use:

| Tool | Description | Example Query |
|------|-------------|---------------|
| `check_karma` | Verify Karma connectivity | "Is Karma accessible?" |
| `list_alerts` | List all active alerts | "Show me all alerts" |
| `get_alerts_summary` | Statistical summary by severity/state | "Give me an alert summary" |
| `get_alert_details` | Detailed info about specific alert | "Details about KubePodCrashLooping" |
| `list_clusters` | List all K8s clusters with counts | "Which clusters have alerts?" |
| `list_alerts_by_cluster` | Filter by cluster | "Show teddy-prod alerts" |
| `search_alerts_by_container` | Search by container name | "Find nginx container alerts" |
| `get_alert_details_multi_cluster` | Search alert across clusters | "Find OOMKilled in all clusters" |
| `list_active_alerts` | Show only active alerts | "What's currently firing?" |
| `list_suppressed_alerts` | Show silenced/inhibited | "What alerts are suppressed?" |

## 🔌 REST API Endpoints

If you prefer HTTP integration:

```bash
# Start HTTP server
uv run python -m karma_mcp.http_server

# Available endpoints
GET  http://localhost:8000/health
GET  http://localhost:8000/alerts
GET  http://localhost:8000/alerts/summary
GET  http://localhost:8000/clusters
POST http://localhost:8000/alerts/by-cluster
POST http://localhost:8000/alerts/details
POST http://localhost:8000/alerts/search/container
POST http://localhost:8000/alerts/search/name
```

## 🧪 Testing

```bash
# Run unit tests
uv run pytest tests/unit/

# Run with coverage
uv run pytest --cov=karma_mcp tests/

# Run integration tests (requires Karma instance)
KARMA_URL=http://localhost:8080 uv run pytest tests/integration/

# Manual testing
uv run python tests/manual/test_mcp_tools.py
```

## 🔧 Development

### Setting up the development environment

```bash
# Clone the repository
git clone https://github.com/driosalido/karma-mcp.git
cd karma-mcp

# Install with development dependencies
uv sync --all-extras --dev

# Install pre-commit hooks
uv run pre-commit install

# Run code quality checks
uv run ruff check .
uv run mypy src/
uv run bandit -r src/
```

### Project Structure

```
karma-mcp/
├── src/karma_mcp/
│   ├── server.py          # Main MCP server with all tools
│   └── http_server.py     # REST API wrapper
├── tests/
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   └── fixtures/         # Test data
├── docker/               # Docker configurations
├── helm/                 # Kubernetes Helm charts
└── .github/workflows/    # CI/CD pipelines
```

## 📊 Real-World Use Cases

### Daily Operations
- **Morning standup**: "Show me all critical alerts from the last 24 hours"
- **Shift handover**: "Summarize current active alerts by cluster"
- **Quick checks**: "Are there any database-related alerts?"

### Incident Response
- **Investigation**: "Find all alerts related to the payment service"
- **Pattern detection**: "Show me crash loops in the API namespace"
- **Impact analysis**: "Which clusters are affected by high CPU throttling?"

### Capacity Planning
- **Resource issues**: "List all OOM killed containers this week"
- **Scaling decisions**: "Show pods with high memory pressure"
- **Performance**: "Find all high latency alerts"

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

Areas we'd love help with:
- 🔕 Alert silencing/acknowledgment features
- 📈 Historical trending and analytics
- 🔐 Authentication support for secured Karma instances
- 🌍 Additional language support for alert descriptions
- 📱 Slack/Teams notification integrations

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Karma Alert Dashboard](https://github.com/prymitive/karma) - The excellent alert dashboard that makes this possible
- [Model Context Protocol](https://github.com/modelcontextprotocol) - Anthropic's protocol for AI tool integration
- [FastMCP](https://github.com/jlowin/fastmcp) - Simplified MCP server development
- The Kubernetes and Prometheus communities for their amazing monitoring ecosystem

## 📚 Documentation

- [Full API Documentation](docs/API.md)
- [Configuration Guide](docs/CONFIGURATION.md)
- [Troubleshooting Guide](docs/TROUBLESHOOTING.md)
- [Example Queries](docs/EXAMPLES.md)

## 🚀 Roadmap

- [x] Core alert querying and filtering
- [x] Multi-cluster search capabilities
- [x] Docker and Kubernetes support
- [x] CI/CD with GitHub Actions
- [ ] Alert silencing and acknowledgment
- [ ] Historical data and trending
- [ ] Grafana integration
- [ ] Alert correlation and root cause analysis
- [ ] Natural language alert rules generation

---

**Need help?** Open an issue or reach out on [GitHub Discussions](https://github.com/driosalido/karma-mcp/discussions)

**Like this project?** Give it a ⭐ on GitHub!