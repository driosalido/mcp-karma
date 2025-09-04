"""
Basic functionality tests that don't require async
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

# Add src to path
project_root = Path(__file__).parent.parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from karma_mcp.http_server import app  # noqa: E402


class TestHTTPServerBasics:
    """Test basic HTTP server functionality"""

    def test_app_creation(self):
        """Test that the FastAPI app is created correctly"""
        assert app.title == "Karma MCP HTTP Server"
        assert "0.4.0" in app.version

    def test_root_endpoint(self):
        """Test root endpoint"""
        client = TestClient(app)
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "Karma MCP HTTP Server"
        assert "endpoints" in data
        assert isinstance(data["endpoints"], list)

    def test_health_endpoint_basic(self):
        """Test health endpoint basic structure"""
        client = TestClient(app)

        with patch("karma_mcp.http_server.check_karma") as mock_check:
            mock_check.return_value = "✓ Karma is running at http://localhost:8080"

            response = client.get("/health")

            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert "karma" in data
            assert "message" in data


class TestMCPProtocolBasics:
    """Test MCP protocol basics without async complexity"""

    def test_mcp_initialize_request(self):
        """Test MCP initialize handshake"""
        client = TestClient(app)

        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"},
            },
        }

        response = client.post("/mcp/sse", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == 1
        assert "result" in data
        assert data["result"]["protocolVersion"] == "2025-06-18"
        assert data["result"]["serverInfo"]["name"] == "karma-mcp"
        assert data["result"]["serverInfo"]["version"] == "0.4.0"

    def test_mcp_tools_list_request(self):
        """Test MCP tools/list request"""
        client = TestClient(app)

        payload = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}

        response = client.post("/mcp/sse", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == 2
        assert "tools" in data["result"]

        # Check that our new state filtering tools are included
        tool_names = [tool["name"] for tool in data["result"]["tools"]]
        expected_tools = [
            "check_karma",
            "list_alerts",
            "get_alerts_summary",
            "list_clusters",
            "list_alerts_by_cluster",
            "get_alert_details",
            "get_alert_details_multi_cluster",
            "list_active_alerts",
            "list_suppressed_alerts",
            "get_alerts_by_state",
            "search_alerts_by_container",
        ]

        for expected_tool in expected_tools:
            assert expected_tool in tool_names

    def test_mcp_tool_call_with_mock(self):
        """Test MCP tool call with mocked response"""
        client = TestClient(app)

        with patch("karma_mcp.http_server.check_karma") as mock_check:
            mock_check.return_value = "✓ Karma is running"

            payload = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {"name": "check_karma", "arguments": {}},
            }

            response = client.post("/mcp/sse", json=payload)

            assert response.status_code == 200
            data = response.json()
            assert data["jsonrpc"] == "2.0"
            assert data["id"] == 3
            assert "result" in data
            assert "content" in data["result"]
            assert data["result"]["content"][0]["type"] == "text"
            assert "✓ Karma is running" in data["result"]["content"][0]["text"]

    def test_mcp_state_filtering_tools_in_list(self):
        """Test that state filtering tools appear in tools list"""
        client = TestClient(app)

        payload = {"jsonrpc": "2.0", "id": 4, "method": "tools/list"}

        response = client.post("/mcp/sse", json=payload)
        data = response.json()

        tools = data["result"]["tools"]
        tool_names = [tool["name"] for tool in tools]

        # Verify state filtering tools are present
        assert "list_active_alerts" in tool_names
        assert "list_suppressed_alerts" in tool_names
        assert "get_alerts_by_state" in tool_names

        # Check schema for get_alerts_by_state
        state_tool = next(
            tool for tool in tools if tool["name"] == "get_alerts_by_state"
        )
        assert "state" in state_tool["inputSchema"]["properties"]
        assert state_tool["inputSchema"]["properties"]["state"]["enum"] == [
            "active",
            "suppressed",
            "all",
        ]

    def test_mcp_error_handling(self):
        """Test MCP error handling"""
        client = TestClient(app)

        # Test unknown method
        payload = {"jsonrpc": "2.0", "id": 5, "method": "unknown/method"}

        response = client.post("/mcp/sse", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == -32601
        assert "Method not found" in data["error"]["message"]

    def test_mcp_missing_required_parameter(self):
        """Test MCP tool call with missing required parameter"""
        client = TestClient(app)

        payload = {
            "jsonrpc": "2.0",
            "id": 6,
            "method": "tools/call",
            "params": {
                "name": "get_alerts_by_state",
                "arguments": {},  # Missing required 'state' parameter
            },
        }

        response = client.post("/mcp/sse", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert "error" in data
        assert "state parameter required" in data["error"]["message"]


class TestRESTEndpointsBasic:
    """Test REST endpoints with mocking"""

    def test_get_alerts_endpoint_mocked(self):
        """Test GET /alerts endpoint with mocked response"""
        client = TestClient(app)

        with patch("karma_mcp.http_server.list_alerts") as mock_list:
            mock_list.return_value = "Found 5 alerts"

            response = client.get("/alerts")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"] == "Found 5 alerts"

    def test_post_endpoints_validation(self):
        """Test POST endpoints parameter validation"""
        client = TestClient(app)

        # Test missing cluster_name
        response = client.post("/alerts/by-cluster", json={})
        assert response.status_code == 422  # Validation error

        # Test missing alert_name
        response = client.post("/alerts/details", json={})
        assert response.status_code == 422  # Validation error

    def test_execute_endpoint_basic(self):
        """Test /mcp/execute endpoint basic functionality"""
        client = TestClient(app)

        with patch("karma_mcp.http_server.check_karma") as mock_check:
            mock_check.return_value = "✓ Karma is running"

            payload = {"tool": "check_karma", "params": {}}

            response = client.post("/mcp/execute", json=payload)

            assert response.status_code == 200
            data = response.json()
            assert data["type"] == "tool_result"
            assert data["tool"] == "check_karma"
            assert data["success"] is True
            assert data["result"] == "✓ Karma is running"
            assert "timestamp" in data


class TestConfigurationAndStructure:
    """Test configuration and project structure"""

    def test_project_structure(self):
        """Test that project has expected structure"""
        project_root = Path(__file__).parent.parent.parent

        # Check key directories exist
        assert (project_root / "src").exists()
        assert (project_root / "src" / "karma_mcp").exists()
        assert (project_root / "tests").exists()
        assert (project_root / "tests" / "unit").exists()
        assert (project_root / "tests" / "integration").exists()
        assert (project_root / "tests" / "fixtures").exists()

        # Check key files exist
        assert (project_root / "pyproject.toml").exists()
        assert (project_root / "src" / "karma_mcp" / "server.py").exists()
        assert (project_root / "src" / "karma_mcp" / "http_server.py").exists()

    def test_imports_work(self):
        """Test that key imports work correctly"""
        # Test that we can import the modules
        from karma_mcp import http_server, server

        # Test that key functions exist
        assert hasattr(server, "check_karma")
        assert hasattr(server, "list_active_alerts")
        assert hasattr(server, "list_suppressed_alerts")
        assert hasattr(server, "get_alerts_by_state")

        # Test that HTTP server has the app
        assert hasattr(http_server, "app")

    def test_version_consistency(self):
        """Test version consistency across files"""
        from karma_mcp.http_server import app

        # Check that version is consistent
        assert "0.4.0" in app.version or "0.4" in app.version


if __name__ == "__main__":
    # Simple test runner if executed directly
    pytest.main([__file__, "-v"])
