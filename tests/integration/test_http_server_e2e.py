"""
End-to-end tests for HTTP server functionality
"""

from fastapi.testclient import TestClient

from karma_mcp.http_server import app


class TestHTTPServerE2E:
    """End-to-end tests for the HTTP server"""

    def test_server_startup(self):
        """Test that the server starts up correctly"""
        client = TestClient(app)

        # Test root endpoint
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert data["service"] == "Karma MCP HTTP Server"
        assert "endpoints" in data
        assert isinstance(data["endpoints"], list)

    def test_cors_headers(self):
        """Test that CORS headers are properly set"""
        client = TestClient(app)

        # Test preflight request
        response = client.options("/health")

        # Should have CORS headers (TestClient doesn't fully simulate browser CORS)
        # But we can check that the middleware is configured
        assert response.status_code == 200

    def test_mcp_protocol_flow(self):
        """Test complete MCP protocol flow"""
        client = TestClient(app)

        # Step 1: Initialize
        init_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"},
            },
        }

        response = client.post("/mcp/sse", json=init_payload)
        assert response.status_code == 200

        init_result = response.json()
        assert init_result["jsonrpc"] == "2.0"
        assert init_result["id"] == 1
        assert "result" in init_result

        # Step 2: Send initialized notification
        notif_payload = {"jsonrpc": "2.0", "method": "notifications/initialized"}

        response = client.post("/mcp/sse", json=notif_payload)
        assert response.status_code == 200

        # Step 3: List available tools
        tools_payload = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}

        response = client.post("/mcp/sse", json=tools_payload)
        assert response.status_code == 200

        tools_result = response.json()
        assert "tools" in tools_result["result"]
        tools = tools_result["result"]["tools"]

        # Verify all expected tools are present
        expected_tools = [
            "check_karma",
            "list_alerts",
            "get_alerts_summary",
            "list_clusters",
            "list_alerts_by_cluster",
            "get_alert_details",
            "list_active_alerts",
            "list_suppressed_alerts",
            "get_alerts_by_state",
        ]

        tool_names = [tool["name"] for tool in tools]
        for expected_tool in expected_tools:
            assert expected_tool in tool_names

        # Verify tool schemas are correct
        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "inputSchema" in tool
            assert tool["inputSchema"]["type"] == "object"

    def test_tool_execution_via_mcp(self):
        """Test tool execution through MCP protocol"""
        client = TestClient(app)

        # Test check_karma tool
        payload = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "check_karma", "arguments": {}},
        }

        response = client.post("/mcp/sse", json=payload)
        assert response.status_code == 200

        result = response.json()
        assert result["jsonrpc"] == "2.0"
        assert result["id"] == 3
        assert "result" in result
        assert "content" in result["result"]
        assert len(result["result"]["content"]) > 0
        assert result["result"]["content"][0]["type"] == "text"

    def test_state_filtering_tools_via_mcp(self):
        """Test new state filtering tools via MCP protocol"""
        client = TestClient(app)

        # Test list_active_alerts
        payload = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {"name": "list_active_alerts", "arguments": {}},
        }

        response = client.post("/mcp/sse", json=payload)
        assert response.status_code == 200

        result = response.json()
        assert "result" in result
        assert "content" in result["result"]

        # Test list_suppressed_alerts
        payload["id"] = 5
        payload["params"]["name"] = "list_suppressed_alerts"

        response = client.post("/mcp/sse", json=payload)
        assert response.status_code == 200

        # Test get_alerts_by_state with parameter
        payload["id"] = 6
        payload["params"]["name"] = "get_alerts_by_state"
        payload["params"]["arguments"] = {"state": "active"}

        response = client.post("/mcp/sse", json=payload)
        assert response.status_code == 200

    def test_error_handling_in_mcp_protocol(self):
        """Test error handling in MCP protocol"""
        client = TestClient(app)

        # Test unknown method
        payload = {"jsonrpc": "2.0", "id": 7, "method": "unknown/method"}

        response = client.post("/mcp/sse", json=payload)
        assert response.status_code == 200

        result = response.json()
        assert "error" in result
        assert result["error"]["code"] == -32601

        # Test unknown tool
        payload = {
            "jsonrpc": "2.0",
            "id": 8,
            "method": "tools/call",
            "params": {"name": "unknown_tool", "arguments": {}},
        }

        response = client.post("/mcp/sse", json=payload)
        assert response.status_code == 200

        result = response.json()
        assert "error" in result
        assert "Unknown tool" in result["error"]["message"]

        # Test missing required parameter
        payload = {
            "jsonrpc": "2.0",
            "id": 9,
            "method": "tools/call",
            "params": {
                "name": "get_alerts_by_state",
                "arguments": {},  # Missing required 'state' parameter
            },
        }

        response = client.post("/mcp/sse", json=payload)
        assert response.status_code == 200

        result = response.json()
        assert "error" in result
        assert "state parameter required" in result["error"]["message"]


class TestRESTAPIE2E:
    """End-to-end tests for REST API"""

    def test_complete_rest_workflow(self):
        """Test complete workflow using REST endpoints"""
        client = TestClient(app)

        # 1. Check health
        response = client.get("/health")
        assert response.status_code in [200, 503]  # May fail if no real Karma

        # 2. Get alerts summary
        response = client.get("/alerts/summary")
        assert response.status_code == 200
        data = response.json()
        assert "success" in data

        # 3. List all alerts
        response = client.get("/alerts")
        assert response.status_code == 200
        data = response.json()
        assert "success" in data

        # 4. Get clusters
        response = client.get("/clusters")
        assert response.status_code == 200
        data = response.json()
        assert "success" in data

        # 5. Test POST endpoints with sample data
        response = client.post(
            "/alerts/by-cluster", json={"cluster_name": "test-cluster"}
        )
        assert response.status_code == 200

        response = client.post("/alerts/details", json={"alert_name": "TestAlert"})
        assert response.status_code == 200

    def test_rest_api_error_responses(self):
        """Test REST API error responses"""
        client = TestClient(app)

        # Test missing required fields
        response = client.post("/alerts/by-cluster", json={})
        assert response.status_code == 422  # Validation error

        response = client.post("/alerts/details", json={})
        assert response.status_code == 422  # Validation error

        # Test invalid JSON
        response = client.post(
            "/alerts/by-cluster",
            data="invalid json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422


class TestExecuteEndpointE2E:
    """End-to-end tests for /mcp/execute endpoint"""

    def test_execute_endpoint_workflow(self):
        """Test complete workflow using execute endpoint"""
        client = TestClient(app)

        # Test all tools via execute endpoint
        tools_to_test = [
            {"tool": "check_karma", "params": {}},
            {"tool": "list_alerts", "params": {}},
            {"tool": "get_alerts_summary", "params": {}},
            {"tool": "list_clusters", "params": {}},
            {"tool": "list_active_alerts", "params": {}},
            {"tool": "list_suppressed_alerts", "params": {}},
            {"tool": "get_alerts_by_state", "params": {"state": "all"}},
        ]

        for test_case in tools_to_test:
            response = client.post("/mcp/execute", json=test_case)
            assert response.status_code == 200

            data = response.json()
            assert data["type"] == "tool_result"
            assert data["tool"] == test_case["tool"]
            assert "success" in data
            assert "timestamp" in data

    def test_execute_endpoint_with_parameters(self):
        """Test execute endpoint with various parameters"""
        client = TestClient(app)

        # Test tools that require parameters
        test_cases = [
            {"tool": "get_alerts_by_state", "params": {"state": "active"}},
            {"tool": "get_alerts_by_state", "params": {"state": "suppressed"}},
            {
                "tool": "list_alerts_by_cluster",
                "params": {"cluster_name": "test-cluster"},
            },
            {"tool": "get_alert_details", "params": {"alert_name": "TestAlert"}},
        ]

        for test_case in test_cases:
            response = client.post("/mcp/execute", json=test_case)
            assert response.status_code == 200

            data = response.json()
            assert data["tool"] == test_case["tool"]
            # Success may be false if tool execution fails, but should not crash
            assert "success" in data


class TestServerConfiguration:
    """Tests for server configuration and setup"""

    def test_app_metadata(self):
        """Test application metadata"""
        # Test that app is configured correctly
        assert app.title == "Karma MCP HTTP Server"
        assert app.version == "0.4.0"
        assert "HTTP wrapper for Karma MCP tools" in app.description

    def test_middleware_configuration(self):
        """Test that middleware is properly configured"""
        client = TestClient(app)

        # Make a request and check that it doesn't fail due to CORS
        response = client.get("/")
        assert response.status_code == 200

        # The app should handle cross-origin requests
        # (TestClient doesn't fully simulate CORS but ensures middleware doesn't break)

    def test_route_registration(self):
        """Test that all expected routes are registered"""
        client = TestClient(app)

        # Test all expected endpoints exist
        expected_routes = [
            ("/", "GET"),
            ("/health", "GET"),
            ("/alerts", "GET"),
            ("/alerts/summary", "GET"),
            ("/clusters", "GET"),
            ("/alerts/by-cluster", "POST"),
            ("/alerts/details", "POST"),
            ("/mcp/sse", "GET"),
            ("/mcp/sse", "POST"),
            ("/mcp/execute", "POST"),
        ]

        for path, method in expected_routes:
            if method == "GET":
                response = client.get(path)
            elif method == "POST":
                response = client.post(path, json={})

            # Should not return 404 (route exists)
            assert response.status_code != 404


class TestConcurrencyAndLoad:
    """Basic concurrency and load tests"""

    def test_concurrent_requests(self):
        """Test server handles concurrent requests"""
        import threading

        client = TestClient(app)
        results = []
        errors = []

        def make_request():
            try:
                response = client.get("/health")
                results.append(response.status_code)
            except Exception as e:
                errors.append(str(e))

        # Make 10 concurrent requests
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()

        # Wait for all requests to complete
        for thread in threads:
            thread.join(timeout=5.0)

        # All requests should complete without errors
        assert len(errors) == 0, f"Concurrent requests failed: {errors}"
        assert len(results) == 10

        # All should return valid status codes
        for status_code in results:
            assert status_code in [200, 503]  # 503 if no real Karma available

    def test_repeated_requests_dont_leak_resources(self):
        """Test that repeated requests don't cause resource leaks"""
        client = TestClient(app)

        # Make many requests to the same endpoint
        for _i in range(50):
            response = client.get("/")
            assert response.status_code == 200

            # Verify basic response structure each time
            data = response.json()
            assert "service" in data

        # If we get here without hanging or crashing, no obvious resource leaks
