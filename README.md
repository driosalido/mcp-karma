# 🚨 Karma MCP Server

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![MCP Protocol](https://img.shields.io/badge/MCP-Protocol-green.svg)](https://modelcontextprotocol.io/)
[![Docker Support](https://img.shields.io/badge/Docker-Supported-blue.svg)](https://www.docker.com/)
[![Just](https://img.shields.io/badge/Task_Runner-Just-orange.svg)](https://github.com/casey/just)

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

### Advanced Capabilities
- 🔍 **Alert name search** - Search specific alerts by pattern matching
- 🔍 **State filtering** - Filter by active, suppressed, or all states
- 🔍 **Cross-cluster analysis** - Compare alert patterns between environments

### Integration Features
- 🔄 **MCP Protocol** support for AI assistants
- 🐳 **Docker support** with multi-architecture images
- ☸️ **Kubernetes-ready** deployment

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

# Optional: Install Just task runner for easier development
brew install just        # macOS
# See: https://github.com/casey/just#installation for other platforms
```

2. **Configure Claude Desktop, Claude Code, or Cursor**

#### Local Installation (Stdio Mode)
Add to your MCP client configuration:

**Claude Desktop** (`~/Library/Application Support/Claude/claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "karma": {
      "command": "uv",
      "args": ["run", "python", "-m", "karma_mcp.server"],
      "cwd": "/path/to/karma-mcp",
      "env": {
        "KARMA_URL": "http://your-karma-instance:8080"
      }
    }
  }
}
```

**Claude Code** (add to project's `claude_desktop_config.json` or global config):
```json
{
  "mcpServers": {
    "karma": {
      "command": "uv",
      "args": ["run", "python", "-m", "karma_mcp.server"],
      "cwd": "/path/to/karma-mcp",
      "env": {
        "KARMA_URL": "http://your-karma-instance:8080"
      }
    }
  }
}
```

**Cursor** (via MCP extension or custom configuration):
```json
{
  "mcpServers": {
    "karma": {
      "command": "uv", 
      "args": ["run", "python", "-m", "karma_mcp.server"],
      "cwd": "/path/to/karma-mcp",
      "env": {
        "KARMA_URL": "http://your-karma-instance:8080"
      }
    }
  }
}
```

#### Remote HTTP Server (Alternative)
If you have deployed the HTTP server version, use SSE transport:

```json
{
  "mcpServers": {
    "karma": {
      "transport": {
        "type": "sse",
        "url": "https://your-karma-mcp-server.com/mcp/sse"
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

### Kubernetes Deployment

```bash
# Deploy using Docker image
kubectl create deployment karma-mcp \
  --image=driosalido/karma-mcp:latest

kubectl set env deployment/karma-mcp \
  KARMA_URL=http://karma.monitoring:80
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
| `list_active_alerts` | Show only active alerts | "What's currently firing?" |
| `list_suppressed_alerts` | Show silenced/inhibited | "What alerts are suppressed?" |
| `get_alerts_by_state` | Filter by state (active/suppressed/all) | "Show all suppressed alerts" |
| `search_alerts` | Search alerts by name pattern | "Find all OOM alerts" |
| `silence_alert` | Create alert silence | "Silence KubePodCrashLooping for 2h" |

## 🧠 AI-Enhanced Analysis

The Karma MCP Server includes specialized prompts that help Claude provide more valuable alert analysis:

### 📚 Available Prompt Resources

| Resource | Purpose | Description |
|----------|---------|-------------|
| `prompts://alert-analysis` | Alert Analysis | Comprehensive guidelines for troubleshooting common K8s alerts |
| `prompts://incident-response` | Incident Response | Escalation procedures and communication templates |
| `prompts://kubernetes-context` | K8s Context | Deep Kubernetes knowledge for alert interpretation |
| `prompts://business-impact` | Business Impact | Prioritization framework based on service criticality |

### 🎯 Enhanced Capabilities

With these prompts, Claude can:
- 🔍 **Correlate related alerts** across clusters and namespaces
- 🚨 **Prioritize by business impact** (prod > staging > dev)
- 🔧 **Suggest specific actions** for common alert types
- 📊 **Provide context** about Kubernetes resource relationships
- 🚀 **Guide incident response** with escalation procedures

## 🔌 API Integration

The server runs as an MCP server using stdio protocol for communication with Claude Desktop. For programmatic access, you can call the MCP tools directly from your Python code:

```python
from karma_mcp.server import list_alerts, get_alerts_summary

# Example usage
alerts = await list_alerts()
summary = await get_alerts_summary()
```

## 🧪 Testing

```bash
# Run unit tests
uv run pytest tests/unit/

# Run with coverage
uv run pytest --cov=karma_mcp tests/

# Run integration tests (requires Karma instance)
KARMA_URL=http://localhost:8080 uv run pytest tests/integration/

# Manual testing with real Karma server
KARMA_URL=http://localhost:8080 uv run python -c "
import asyncio
from karma_mcp.server import list_alerts, get_alerts_summary
asyncio.run(list_alerts())
"
```

## 🔧 Development

### Setting up the development environment

```bash
# Clone the repository
git clone https://github.com/driosalido/karma-mcp.git
cd karma-mcp

# Install dependencies (includes dev dependencies)
uv sync --all-extras

# Install Just task runner (modern alternative to Make)
# macOS
brew install just

# Other platforms: https://github.com/casey/just#installation

# Set up development environment
just dev-setup
```

### Task Runner: Just vs Make

This project uses **Just** as the modern task runner (alternative to Make). Key benefits:

- ✅ **No tab/space issues** (common Make problem)
- ✅ **Better variable handling** and environment integration  
- ✅ **Cleaner syntax** and cross-platform compatibility
- ✅ **Built-in command listing** with `just`
- ✅ **Modern features** like default values and string interpolation

```bash
# See all available commands
just

# Common development tasks
just test-unit              # Run unit tests (78 tests)
just lint                   # Code linting  
just format                 # Code formatting
just check                  # All quality checks
just test-with-karma        # Test with real Karma server
just docker-build-local     # Build Docker image
just version               # Show version info
```

### Manual Development Commands

If you prefer direct commands or don't have Just installed:

```bash
# Run tests
uv run pytest tests/unit/ -v

# Code quality
uv run ruff check src/ tests/
uv run ruff format src/ tests/

# Install pre-commit hooks  
uv run pre-commit install
```

### Project Structure

```
karma-mcp/
├── src/karma_mcp/
│   └── server.py         # Main MCP server with all tools
├── tests/
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   └── fixtures/         # Test data
├── docker/
│   └── Dockerfile        # Docker configuration
├── scripts/
│   └── test_karma.py     # Integration testing utilities
├── justfile              # Modern task runner (preferred)
├── Makefile              # Traditional Make tasks (legacy)
├── pyproject.toml        # Project dependencies and config
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
- 📈 Historical trending and analytics
- 🔐 Authentication support for secured Karma instances
- 🌍 Additional language support for alert descriptions
- 📱 Slack/Teams notification integrations
- 🤖 AI-powered alert correlation and root cause analysis

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Karma Alert Dashboard](https://github.com/prymitive/karma) - The excellent alert dashboard that makes this possible
- [Model Context Protocol](https://github.com/modelcontextprotocol) - Anthropic's protocol for AI tool integration
- [FastMCP](https://github.com/jlowin/fastmcp) - Simplified MCP server development
- The Kubernetes and Prometheus communities for their amazing monitoring ecosystem

## 📚 Documentation

- **Configuration**: Set `KARMA_URL` environment variable to your Karma instance
- **Troubleshooting**: Check the [GitHub Issues](https://github.com/driosalido/karma-mcp/issues) for common problems
- **Examples**: See the "Real-World Use Cases" section above for query examples

## 🚀 Roadmap

### Completed ✅
- Core alert querying and filtering
- Multi-cluster support
- State-based filtering (active/suppressed)
- Docker containerization
- CI/CD with GitHub Actions
- Alert search by pattern
- Alert silencing capability

### In Progress 🔨
- Alert acknowledgment
- Silence management (list/delete)

### Future Plans 💭
- Historical data and trending
- Alert correlation analysis
- Grafana integration
- Authentication for secured Karma instances

---

**Need help?** Open an issue or reach out on [GitHub Discussions](https://github.com/driosalido/karma-mcp/discussions)

**Like this project?** Give it a ⭐ on GitHub!