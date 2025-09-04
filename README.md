# Karma MCP Server

Simple MCP server for integrating Claude with Karma Alert dashboard.

## Quick Start

### 1. Install dependencies

```bash
uv pip install -e .
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and set KARMA_URL to your Karma instance
```

### 3. Test with your Karma instance

```bash
# Port forward to your Karma instance (if in Kubernetes)
kubectl port-forward svc/karma 8080:80 -n monitoring

# Set environment variable
export KARMA_URL=http://localhost:8080

# Test the MCP tools (optional)
uv run python tests/manual/test_mcp_tools.py

# Run the server
cd src && python -m karma_mcp.server
```

### 4. Using Docker (Alternative)

```bash
# Build the Docker image
./docker/build.sh

# Run with Docker
KARMA_URL=http://your-karma-url:8080 ./docker/run.sh

# Or use docker-compose
cp .env.docker .env
# Edit .env with your settings
docker-compose up -d
```

### 5. Configure in Claude Desktop

Add to your Claude Desktop configuration (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "karma": {
      "command": "python",
      "args": ["-m", "karma_mcp.server"],
      "env": {
        "KARMA_URL": "http://localhost:8080"
      }
    }
  }
}
```

## Available Tools

- `check_karma`: Check connection to Karma server
- `list_alerts`: List all active alerts with basic info
- `get_alerts_summary`: Get statistical summary of alerts by severity and state
- `get_alert_details`: Get detailed information about a specific alert by name
- `list_clusters`: List all available Kubernetes clusters with alert counts
- `list_alerts_by_cluster`: Filter alerts by specific cluster name

## How it works

This MCP server connects to your Karma Alert dashboard API and provides tools for Claude to:
1. Check if Karma is accessible
2. Retrieve and display active alerts
3. Filter alerts by cluster, severity, namespace, and state
4. Get detailed information about specific alerts
5. Analyze alert statistics and trends

The server uses the Karma JSON API endpoints to fetch alert data.

## Testing

Manual testing scripts are available in `tests/manual/`:

```bash
# Test all MCP tools
uv run python tests/manual/test_mcp_tools.py

# Test cluster filtering
uv run python tests/manual/test_cluster_features.py

# Debug API responses
uv run python tests/manual/debug_data.py
```

See `tests/manual/README.md` for complete testing documentation.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

### Development Setup

```bash
# Clone the repository
git clone <repository-url>
cd karma-mcp

# Install dependencies
uv pip install -e .

# Set up pre-commit hooks (optional)
# pip install pre-commit
# pre-commit install
```

### Running Tests

```bash
# Run manual tests
uv run python tests/manual/test_mcp_tools.py
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Karma Alert Dashboard](https://github.com/prymitive/karma) by prymitive
- [Model Context Protocol](https://github.com/modelcontextprotocol/python-sdk) by Anthropic
- [FastMCP](https://pypi.org/project/fastmcp/) for simplified MCP server development
