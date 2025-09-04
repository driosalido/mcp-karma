"""
Unit tests for HTTP server functionality
"""

from unittest.mock import patch

from fastapi.testclient import TestClient

from karma_mcp.http_server import app


class TestHealthEndpoint:
    """Test suite for health endpoint"""

    def test_health_endpoint_success(self):
        """Test health endpoint returns 200 when Karma is healthy"""
        client = TestClient(app)

        with patch("karma_mcp.http_server.check_karma") as mock_check:
            mock_check.return_value = "✓ Karma is running at http://localhost:8080"

            response = client.get("/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["karma"] == "connected"

    def test_health_endpoint_degraded(self):
        """Test health endpoint when Karma has issues"""
        client = TestClient(app)

        with patch("karma_mcp.http_server.check_karma") as mock_check:
            mock_check.return_value = "⚠ Karma responded with code 500"

            response = client.get("/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "degraded"
            assert data["karma"] == "issues"

    def test_health_endpoint_failure(self):
        """Test health endpoint when Karma check fails"""
        client = TestClient(app)

        with patch("karma_mcp.http_server.check_karma") as mock_check:
            mock_check.side_effect = Exception("Connection failed")

            response = client.get("/health")

            assert response.status_code == 503
            assert "Health check failed" in response.json()["detail"]


class TestRESTEndpoints:
    """Test suite for REST API endpoints"""

    def test_get_alerts_endpoint(self):
        """Test GET /alerts endpoint"""
        client = TestClient(app)

        with patch("karma_mcp.http_server.list_alerts") as mock_list:
            mock_list.return_value = "Found 5 alerts"

            response = client.get("/alerts")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"] == "Found 5 alerts"

    def test_get_alerts_summary_endpoint(self):
        """Test GET /alerts/summary endpoint"""
        client = TestClient(app)

        with patch("karma_mcp.http_server.get_alerts_summary") as mock_summary:
            mock_summary.return_value = "Total Alerts: 10"

            response = client.get("/alerts/summary")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"] == "Total Alerts: 10"

    def test_get_clusters_endpoint(self):
        """Test GET /clusters endpoint"""
        client = TestClient(app)

        with patch("karma_mcp.http_server.list_clusters") as mock_clusters:
            mock_clusters.return_value = "Found 2 clusters"

            response = client.get("/clusters")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"] == "Found 2 clusters"

    def test_post_alerts_by_cluster_endpoint(self):
        """Test POST /alerts/by-cluster endpoint"""
        client = TestClient(app)

        with patch(
            "karma_mcp.http_server.list_alerts_by_cluster"
        ) as mock_cluster_alerts:
            mock_cluster_alerts.return_value = "Found 3 alerts in prod-cluster"

            response = client.post(
                "/alerts/by-cluster", json={"cluster_name": "prod-cluster"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"] == "Found 3 alerts in prod-cluster"
            mock_cluster_alerts.assert_called_once_with("prod-cluster")

    def test_post_alert_details_endpoint(self):
        """Test POST /alerts/details endpoint"""
        client = TestClient(app)

        with patch("karma_mcp.http_server.get_alert_details") as mock_details:
            mock_details.return_value = "Alert details for TestAlert"

            response = client.post("/alerts/details", json={"alert_name": "TestAlert"})

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"] == "Alert details for TestAlert"
            mock_details.assert_called_once_with("TestAlert")

    def test_post_container_search_endpoint(self):
        """Test POST /alerts/search/container endpoint"""
        client = TestClient(app)

        with patch("karma_mcp.http_server.search_alerts_by_container") as mock_search:
            mock_search.return_value = (
                "Container Alert Search: 'nginx' found 2 instances across 2 clusters"
            )

            response = client.post(
                "/alerts/search/container",
                json={"container_name": "nginx", "cluster_filter": "prod-cluster"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert (
                data["data"]
                == "Container Alert Search: 'nginx' found 2 instances across 2 clusters"
            )
            mock_search.assert_called_once_with("nginx", "prod-cluster")

    def test_post_container_search_endpoint_no_cluster_filter(self):
        """Test POST /alerts/search/container endpoint without cluster filter"""
        client = TestClient(app)

        with patch("karma_mcp.http_server.search_alerts_by_container") as mock_search:
            mock_search.return_value = (
                "Container Alert Search: 'nginx' (multi-cluster search)"
            )

            response = client.post(
                "/alerts/search/container", json={"container_name": "nginx"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert (
                data["data"] == "Container Alert Search: 'nginx' (multi-cluster search)"
            )
            mock_search.assert_called_once_with("nginx", "")

    def test_post_alert_search_by_name_endpoint(self):
        """Test POST /alerts/search/name endpoint"""
        client = TestClient(app)

        with patch(
            "karma_mcp.http_server.get_alert_details_multi_cluster"
        ) as mock_search:
            mock_search.return_value = (
                "Alert Details: 'KubePodCrashLooping' found in 2 clusters"
            )

            response = client.post(
                "/alerts/search/name",
                json={"alert_name": "KubePodCrashLooping", "cluster_filter": "prod"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert (
                data["data"]
                == "Alert Details: 'KubePodCrashLooping' found in 2 clusters"
            )
            mock_search.assert_called_once_with("KubePodCrashLooping", "prod")


class TestMCPProtocolEndpoint:
    """Test suite for MCP JSON-RPC protocol endpoint"""

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
        assert "list_active_alerts" in tool_names
        assert "list_suppressed_alerts" in tool_names
        assert "get_alerts_by_state" in tool_names
        assert "search_alerts_by_container" in tool_names
        assert "get_alert_details_multi_cluster" in tool_names
        assert "check_karma" in tool_names
        assert "list_alerts" in tool_names

    def test_mcp_tool_call_check_karma(self):
        """Test MCP tools/call for check_karma"""
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
            assert data["result"]["content"][0]["type"] == "text"
            assert "✓ Karma is running" in data["result"]["content"][0]["text"]

    def test_mcp_tool_call_list_active_alerts(self):
        """Test MCP tools/call for list_active_alerts"""
        client = TestClient(app)

        with patch("karma_mcp.http_server.list_active_alerts") as mock_active:
            mock_active.return_value = "Active Alerts: 5 found"

            payload = {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {"name": "list_active_alerts", "arguments": {}},
            }

            response = client.post("/mcp/sse", json=payload)

            assert response.status_code == 200
            data = response.json()
            assert data["result"]["content"][0]["text"] == "Active Alerts: 5 found"

    def test_mcp_tool_call_get_alerts_by_state(self):
        """Test MCP tools/call for get_alerts_by_state"""
        client = TestClient(app)

        with patch("karma_mcp.http_server.get_alerts_by_state") as mock_state:
            mock_state.return_value = "Suppressed Alerts: 2 found"

            payload = {
                "jsonrpc": "2.0",
                "id": 5,
                "method": "tools/call",
                "params": {
                    "name": "get_alerts_by_state",
                    "arguments": {"state": "suppressed"},
                },
            }

            response = client.post("/mcp/sse", json=payload)

            assert response.status_code == 200
            data = response.json()
            assert data["result"]["content"][0]["text"] == "Suppressed Alerts: 2 found"
            mock_state.assert_called_once_with("suppressed")

    def test_mcp_tool_call_search_alerts_by_container(self):
        """Test MCP tools/call for search_alerts_by_container"""
        client = TestClient(app)

        with patch("karma_mcp.http_server.search_alerts_by_container") as mock_search:
            mock_search.return_value = (
                "Container Alert Search: 'nginx' found 3 instances"
            )

            payload = {
                "jsonrpc": "2.0",
                "id": 5,
                "method": "tools/call",
                "params": {
                    "name": "search_alerts_by_container",
                    "arguments": {
                        "container_name": "nginx",
                        "cluster_filter": "prod-cluster",
                    },
                },
            }

            response = client.post("/mcp/sse", json=payload)

            assert response.status_code == 200
            data = response.json()
            assert (
                data["result"]["content"][0]["text"]
                == "Container Alert Search: 'nginx' found 3 instances"
            )
            mock_search.assert_called_once_with("nginx", "prod-cluster")

    def test_mcp_tool_call_get_alert_details_multi_cluster(self):
        """Test MCP tools/call for get_alert_details_multi_cluster"""
        client = TestClient(app)

        with patch(
            "karma_mcp.http_server.get_alert_details_multi_cluster"
        ) as mock_details:
            mock_details.return_value = (
                "Alert Details: 'KubePodCrashLooping' across 3 clusters"
            )

            payload = {
                "jsonrpc": "2.0",
                "id": 6,
                "method": "tools/call",
                "params": {
                    "name": "get_alert_details_multi_cluster",
                    "arguments": {
                        "alert_name": "KubePodCrashLooping",
                        "cluster_filter": "prod",
                    },
                },
            }

            response = client.post("/mcp/sse", json=payload)

            assert response.status_code == 200
            data = response.json()
            assert (
                data["result"]["content"][0]["text"]
                == "Alert Details: 'KubePodCrashLooping' across 3 clusters"
            )
            mock_details.assert_called_once_with("KubePodCrashLooping", "prod")

    def test_mcp_tool_call_missing_required_param(self):
        """Test MCP tools/call with missing required parameter"""
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
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == 6
        assert "error" in data
        assert "state parameter required" in data["error"]["message"]

    def test_mcp_unknown_tool(self):
        """Test MCP tools/call with unknown tool"""
        client = TestClient(app)

        payload = {
            "jsonrpc": "2.0",
            "id": 7,
            "method": "tools/call",
            "params": {"name": "unknown_tool", "arguments": {}},
        }

        response = client.post("/mcp/sse", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "error" in data
        assert "Unknown tool: unknown_tool" in data["error"]["message"]

    def test_mcp_unknown_method(self):
        """Test MCP request with unknown method"""
        client = TestClient(app)

        payload = {"jsonrpc": "2.0", "id": 8, "method": "unknown/method"}

        response = client.post("/mcp/sse", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "error" in data
        assert "Method not found: unknown/method" in data["error"]["message"]

    def test_mcp_notifications_initialized(self):
        """Test MCP notifications/initialized handling"""
        client = TestClient(app)

        payload = {"jsonrpc": "2.0", "method": "notifications/initialized"}

        response = client.post("/mcp/sse", json=payload)

        # Should return 200 with no content for notifications
        assert response.status_code == 200


class TestExecuteEndpoint:
    """Test suite for /mcp/execute endpoint"""

    def test_execute_check_karma(self):
        """Test /mcp/execute endpoint for check_karma"""
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

    def test_execute_list_active_alerts(self):
        """Test /mcp/execute endpoint for list_active_alerts"""
        client = TestClient(app)

        with patch("karma_mcp.http_server.list_active_alerts") as mock_active:
            mock_active.return_value = "Active alerts found: 10"

            payload = {"tool": "list_active_alerts", "params": {}}

            response = client.post("/mcp/execute", json=payload)

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["result"] == "Active alerts found: 10"

    def test_execute_search_alerts_by_container(self):
        """Test /mcp/execute endpoint for search_alerts_by_container"""
        client = TestClient(app)

        with patch("karma_mcp.http_server.search_alerts_by_container") as mock_search:
            mock_search.return_value = (
                "Container Alert Search: 'nginx' found 3 instances"
            )

            payload = {
                "tool": "search_alerts_by_container",
                "params": {"container_name": "nginx", "cluster_filter": "prod-cluster"},
            }

            response = client.post("/mcp/execute", json=payload)

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["result"] == "Container Alert Search: 'nginx' found 3 instances"
            mock_search.assert_called_once_with("nginx", "prod-cluster")

    def test_execute_missing_tool_name(self):
        """Test /mcp/execute endpoint with missing tool name"""
        client = TestClient(app)

        payload = {"params": {}}

        response = client.post("/mcp/execute", json=payload)

        assert response.status_code == 400
        assert "Tool name required" in response.json()["detail"]

    def test_execute_unknown_tool(self):
        """Test /mcp/execute endpoint with unknown tool"""
        client = TestClient(app)

        payload = {"tool": "unknown_tool", "params": {}}

        response = client.post("/mcp/execute", json=payload)

        assert response.status_code == 400
        assert "Unknown tool: unknown_tool" in response.json()["detail"]


class TestErrorHandling:
    """Test suite for error handling in HTTP server"""

    def test_rest_endpoint_exception(self):
        """Test REST endpoint handling internal exceptions"""
        client = TestClient(app)

        with patch("karma_mcp.http_server.list_alerts") as mock_list:
            mock_list.side_effect = Exception("Internal error")

            response = client.get("/alerts")

            assert response.status_code == 200  # Should not crash
            data = response.json()
            assert data["success"] is False
            assert "Internal error" in data["error"]

    def test_mcp_tool_execution_exception(self):
        """Test MCP tool execution with internal exception"""
        client = TestClient(app)

        with patch("karma_mcp.http_server.check_karma") as mock_check:
            mock_check.side_effect = Exception("Connection failed")

            payload = {
                "jsonrpc": "2.0",
                "id": 10,
                "method": "tools/call",
                "params": {"name": "check_karma", "arguments": {}},
            }

            response = client.post("/mcp/sse", json=payload)

            assert response.status_code == 200
            data = response.json()
            assert "error" in data
            assert "Connection failed" in data["error"]["message"]

    def test_invalid_json_payload(self):
        """Test MCP endpoint with invalid JSON"""
        client = TestClient(app)

        response = client.post(
            "/mcp/sse",
            data="invalid json",
            headers={"Content-Type": "application/json"},
        )

        # Should return 200 with MCP error response for invalid JSON
        assert response.status_code == 200
        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert "error" in data
        assert data["error"]["code"] == -32603  # Internal error
