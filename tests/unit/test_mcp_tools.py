"""
Unit tests for MCP tools
"""

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from karma_mcp.server import (
    check_karma,
    get_alert_details,
    get_alert_details_multi_cluster,
    get_alerts_by_state,
    get_alerts_summary,
    list_active_alerts,
    list_alerts,
    list_alerts_by_cluster,
    list_clusters,
    list_suppressed_alerts,
    search_alerts_by_container,
)


class TestCheckKarma:
    """Test suite for check_karma function"""

    @pytest.mark.asyncio
    async def test_check_karma_success(self, env_setup, health_response):
        """Test successful karma health check"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await check_karma()

            assert "✓ Karma is running" in result
            assert env_setup in result
            mock_client.get.assert_called_once_with(f"{env_setup}/health")

    @pytest.mark.asyncio
    async def test_check_karma_http_error(self, env_setup):
        """Test karma health check with HTTP error"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 500
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await check_karma()

            assert "⚠ Karma responded with code 500" in result

    @pytest.mark.asyncio
    async def test_check_karma_connection_error(self, env_setup):
        """Test karma health check with connection error"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.side_effect = Exception("Connection refused")
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await check_karma()

            assert "✗ Error connecting to Karma" in result
            assert "Connection refused" in result


class TestListAlerts:
    """Test suite for list_alerts function"""

    @pytest.mark.asyncio
    async def test_list_alerts_success(self, env_setup, sample_karma_data):
        """Test successful alert listing"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = sample_karma_data
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await list_alerts()

            assert "Found 3 alerts" in result
            assert "KubePodCrashLooping" in result
            assert "HighMemoryUsage" in result
            mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_alerts_empty_response(self, env_setup, empty_karma_data):
        """Test alert listing with empty response"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = empty_karma_data
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await list_alerts()

            assert "Found 0 alerts" in result

    @pytest.mark.asyncio
    async def test_list_alerts_http_error(self, env_setup):
        """Test alert listing with HTTP error"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 500
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await list_alerts()

            assert "Error fetching alerts: code 500" in result


class TestGetAlertsSummary:
    """Test suite for get_alerts_summary function"""

    @pytest.mark.asyncio
    async def test_get_alerts_summary_success(self, env_setup, sample_karma_data):
        """Test successful alerts summary"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = sample_karma_data
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await get_alerts_summary()

            assert "Total Alerts: 3" in result
            assert "Active: 2" in result
            assert "Suppressed: 1" in result
            assert "By Severity:" in result


class TestStateFiltering:
    """Test suite for state filtering functions"""

    @pytest.mark.asyncio
    async def test_list_active_alerts(self, env_setup, sample_karma_data):
        """Test listing only active alerts"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = sample_karma_data
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await list_active_alerts()

            assert "Active Alerts (Non-Suppressed)" in result
            assert "Total Active Alerts: 2" in result
            # Should contain KubePodCrashLooping active instance and HighMemoryUsage
            assert "🔥" in result  # Fire emoji for active alerts

    @pytest.mark.asyncio
    async def test_list_suppressed_alerts(self, env_setup, sample_karma_data):
        """Test listing only suppressed alerts"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = sample_karma_data
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await list_suppressed_alerts()

            assert "Suppressed Alerts" in result
            assert "Total Suppressed Alerts: 1" in result
            assert "🔕" in result  # Muted emoji for suppressed alerts

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "state,expected_function",
        [
            ("active", "list_active_alerts"),
            ("suppressed", "list_suppressed_alerts"),
            ("all", "list_alerts"),
        ],
    )
    async def test_get_alerts_by_state_valid_states(
        self, state, expected_function, env_setup, sample_karma_data
    ):
        """Test get_alerts_by_state with valid states"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = sample_karma_data
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await get_alerts_by_state(state)

            # Verify result contains expected content based on state
            if state == "active":
                assert "Active Alerts" in result
            elif state == "suppressed":
                assert "Suppressed Alerts" in result
            else:  # all
                assert "Found" in result and "alerts" in result

    @pytest.mark.asyncio
    async def test_get_alerts_by_state_invalid_state(self):
        """Test get_alerts_by_state with invalid state"""
        result = await get_alerts_by_state("invalid")

        assert "Invalid state 'invalid'" in result
        assert "Valid options: active, suppressed, all" in result

    @pytest.mark.asyncio
    async def test_list_active_alerts_no_active_alerts(self, env_setup):
        """Test list_active_alerts when no active alerts exist"""
        # Create data with only suppressed alerts
        suppressed_only_data = {
            "grids": [
                {
                    "alertGroups": [
                        {
                            "labels": [{"name": "alertname", "value": "TestAlert"}],
                            "alerts": [
                                {
                                    "state": "suppressed",
                                    "labels": [{"name": "namespace", "value": "test"}],
                                }
                            ],
                        }
                    ]
                }
            ]
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = suppressed_only_data
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await list_active_alerts()

            assert "No active alerts found" in result

    @pytest.mark.asyncio
    async def test_list_suppressed_alerts_no_suppressed_alerts(self, env_setup):
        """Test list_suppressed_alerts when no suppressed alerts exist"""
        # Create data with only active alerts
        active_only_data = {
            "grids": [
                {
                    "alertGroups": [
                        {
                            "labels": [{"name": "alertname", "value": "TestAlert"}],
                            "alerts": [
                                {
                                    "state": "active",
                                    "labels": [{"name": "namespace", "value": "test"}],
                                }
                            ],
                        }
                    ]
                }
            ]
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = active_only_data
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await list_suppressed_alerts()

            assert "No suppressed alerts found" in result


class TestGetAlertDetails:
    """Test suite for get_alert_details function"""

    @pytest.mark.asyncio
    async def test_get_alert_details_success(self, env_setup, sample_karma_data):
        """Test successful alert details retrieval"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = sample_karma_data
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await get_alert_details("KubePodCrashLooping")

            assert "Found 2 instance(s) of KubePodCrashLooping" in result
            assert "Instance 1:" in result
            assert "Instance 2:" in result
            assert "State:" in result
            assert "Namespace:" in result

    @pytest.mark.asyncio
    async def test_get_alert_details_not_found(self, env_setup, sample_karma_data):
        """Test alert details for non-existent alert"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = sample_karma_data
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await get_alert_details("NonExistentAlert")

            assert "No alert found with name: NonExistentAlert" in result


class TestListClusters:
    """Test suite for list_clusters function"""

    @pytest.mark.asyncio
    async def test_list_clusters_success(self, env_setup, sample_karma_data):
        """Test successful cluster listing"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = sample_karma_data
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await list_clusters()

            assert "Available Kubernetes Clusters" in result
            assert "teddy-prod" in result
            assert "Total Clusters:" in result


class TestListAlertsByCluster:
    """Test suite for list_alerts_by_cluster function"""

    @pytest.mark.asyncio
    async def test_list_alerts_by_cluster_success(self, env_setup, sample_karma_data):
        """Test successful alert filtering by cluster"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = sample_karma_data
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await list_alerts_by_cluster("teddy-prod")

            assert "Alerts in cluster: teddy-prod" in result
            # Should contain alerts from the sample data
            assert "KubePodCrashLooping" in result or "HighMemoryUsage" in result

    @pytest.mark.asyncio
    async def test_list_alerts_by_cluster_not_found(self, env_setup, sample_karma_data):
        """Test alert filtering by non-existent cluster"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = sample_karma_data
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await list_alerts_by_cluster("non-existent-cluster")

            assert "No alerts found for cluster: non-existent-cluster" in result


class TestErrorHandling:
    """Test suite for error handling scenarios"""

    @pytest.mark.asyncio
    async def test_connection_timeout(self, env_setup):
        """Test behavior when connection times out"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post.side_effect = httpx.TimeoutException("Request timeout")
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await list_alerts()

            assert "Error connecting to Karma" in result
            assert "Request timeout" in result

    @pytest.mark.asyncio
    async def test_invalid_json_response(self, env_setup):
        """Test behavior when Karma returns invalid JSON"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.side_effect = ValueError("Invalid JSON")
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await list_alerts()

            assert "Error connecting to Karma" in result
            assert "Invalid JSON" in result


class TestSearchAlertsByContainer:
    """Test suite for search_alerts_by_container function"""

    @pytest.mark.asyncio
    async def test_search_container_success(self, env_setup):
        """Test successful container search across clusters"""
        # Create test data with container labels
        container_data = {
            "grids": [
                {
                    "alertGroups": [
                        {
                            "labels": [
                                {"name": "alertname", "value": "KubePodCrashLooping"},
                                {"name": "severity", "value": "critical"},
                            ],
                            "alerts": [
                                {
                                    "state": "active",
                                    "labels": [
                                        {
                                            "name": "container",
                                            "value": "nginx-container",
                                        },
                                        {"name": "namespace", "value": "default"},
                                        {"name": "pod", "value": "nginx-pod-123"},
                                    ],
                                    "alertmanager": [
                                        {"cluster": "prod-cluster", "name": "am1"}
                                    ],
                                    "startsAt": "2024-01-01T10:00:00Z",
                                },
                                {
                                    "state": "suppressed",
                                    "labels": [
                                        {
                                            "name": "container",
                                            "value": "nginx-container",
                                        },
                                        {"name": "namespace", "value": "staging"},
                                        {"name": "pod", "value": "nginx-pod-456"},
                                    ],
                                    "alertmanager": [
                                        {"cluster": "staging-cluster", "name": "am2"}
                                    ],
                                    "startsAt": "2024-01-01T11:00:00Z",
                                },
                            ],
                        }
                    ]
                }
            ]
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = container_data
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await search_alerts_by_container("nginx")

            assert "Container Alert Search: 'nginx'" in result
            assert "prod-cluster" in result
            assert "staging-cluster" in result
            assert "nginx-container" in result
            assert "Total: 2 alert instances" in result
            assert "across 2 clusters" in result

    @pytest.mark.asyncio
    async def test_search_container_with_cluster_filter(self, env_setup):
        """Test container search with cluster filter"""
        container_data = {
            "grids": [
                {
                    "alertGroups": [
                        {
                            "labels": [
                                {"name": "alertname", "value": "ContainerAlert"},
                                {"name": "severity", "value": "warning"},
                            ],
                            "alerts": [
                                {
                                    "state": "active",
                                    "labels": [
                                        {"name": "container", "value": "my-container"},
                                        {"name": "namespace", "value": "prod"},
                                    ],
                                    "alertmanager": [
                                        {"cluster": "prod-cluster", "name": "am1"}
                                    ],
                                },
                                {
                                    "state": "active",
                                    "labels": [
                                        {"name": "container", "value": "my-container"},
                                        {"name": "namespace", "value": "staging"},
                                    ],
                                    "alertmanager": [
                                        {"cluster": "staging-cluster", "name": "am2"}
                                    ],
                                },
                            ],
                        }
                    ]
                }
            ]
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = container_data
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await search_alerts_by_container("my-container", "prod-cluster")

            assert "in cluster 'prod-cluster'" in result
            assert "prod-cluster" in result
            assert "staging-cluster" not in result
            assert "Total: 1 alert instance" in result
            assert "across 1 cluster" in result

    @pytest.mark.asyncio
    async def test_search_container_not_found(self, env_setup):
        """Test container search when no matching containers found"""
        empty_data = {"grids": [{"alertGroups": []}]}

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = empty_data
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await search_alerts_by_container("nonexistent-container")

            assert "No alerts found for container 'nonexistent-container'" in result
            assert "across all clusters" in result

    @pytest.mark.asyncio
    async def test_search_container_no_cluster_match(self, env_setup):
        """Test container search when no matching clusters found"""
        container_data = {
            "grids": [
                {
                    "alertGroups": [
                        {
                            "labels": [{"name": "alertname", "value": "TestAlert"}],
                            "alerts": [
                                {
                                    "state": "active",
                                    "labels": [
                                        {"name": "container", "value": "my-container"}
                                    ],
                                    "alertmanager": [
                                        {"cluster": "other-cluster", "name": "am1"}
                                    ],
                                }
                            ],
                        }
                    ]
                }
            ]
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = container_data
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await search_alerts_by_container(
                "my-container", "nonexistent-cluster"
            )

            assert "No alerts found for container 'my-container'" in result
            assert "in cluster 'nonexistent-cluster'" in result

    @pytest.mark.asyncio
    async def test_search_container_http_error(self, env_setup):
        """Test container search with HTTP error"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 500
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await search_alerts_by_container("my-container")

            assert "Error fetching alerts: code 500" in result

    @pytest.mark.asyncio
    async def test_search_container_case_insensitive(self, env_setup):
        """Test that container search is case insensitive"""
        container_data = {
            "grids": [
                {
                    "alertGroups": [
                        {
                            "labels": [{"name": "alertname", "value": "TestAlert"}],
                            "alerts": [
                                {
                                    "state": "active",
                                    "labels": [
                                        {
                                            "name": "container",
                                            "value": "NGINX-Container",
                                        },
                                        {"name": "namespace", "value": "default"},
                                    ],
                                    "alertmanager": [
                                        {"cluster": "test-cluster", "name": "am1"}
                                    ],
                                }
                            ],
                        }
                    ]
                }
            ]
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = container_data
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await search_alerts_by_container("nginx")

            assert "NGINX-Container" in result
            assert "Total: 1 alert instance" in result


class TestGetAlertDetailsMultiCluster:
    """Test suite for get_alert_details_multi_cluster function"""

    @pytest.mark.asyncio
    async def test_alert_details_multi_cluster_success(self, env_setup):
        """Test successful multi-cluster alert details retrieval"""
        # Create test data with alerts across multiple clusters
        multi_cluster_data = {
            "grids": [
                {
                    "alertGroups": [
                        {
                            "labels": [
                                {"name": "alertname", "value": "KubePodCrashLooping"},
                                {"name": "severity", "value": "critical"},
                            ],
                            "alerts": [
                                {
                                    "state": "active",
                                    "labels": [
                                        {"name": "namespace", "value": "default"},
                                        {"name": "pod", "value": "app-pod-123"},
                                        {"name": "container", "value": "app-container"},
                                    ],
                                    "annotations": [
                                        {
                                            "name": "description",
                                            "value": "Pod is crash looping",
                                        },
                                        {
                                            "name": "summary",
                                            "value": "Pod crash loop detected",
                                        },
                                    ],
                                    "alertmanager": [
                                        {"cluster": "prod-cluster", "name": "am1"}
                                    ],
                                    "startsAt": "2024-01-01T10:00:00Z",
                                },
                                {
                                    "state": "active",
                                    "labels": [
                                        {"name": "namespace", "value": "staging"},
                                        {"name": "pod", "value": "app-pod-456"},
                                    ],
                                    "annotations": [
                                        {
                                            "name": "description",
                                            "value": "Pod is crash looping in staging",
                                        }
                                    ],
                                    "alertmanager": [
                                        {"cluster": "staging-cluster", "name": "am2"}
                                    ],
                                    "startsAt": "2024-01-01T11:00:00Z",
                                },
                                {
                                    "state": "suppressed",
                                    "labels": [
                                        {"name": "namespace", "value": "dev"},
                                        {"name": "pod", "value": "app-pod-789"},
                                    ],
                                    "alertmanager": [
                                        {"cluster": "dev-cluster", "name": "am3"}
                                    ],
                                    "startsAt": "2024-01-01T12:00:00Z",
                                },
                            ],
                        }
                    ]
                }
            ]
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = multi_cluster_data
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await get_alert_details_multi_cluster("KubePodCrashLooping")

            assert "Alert Details: 'KubePodCrashLooping'" in result
            assert "Total Instances: 3" in result
            assert "Clusters Affected: 3" in result
            assert "prod-cluster" in result
            assert "staging-cluster" in result
            assert "dev-cluster" in result
            assert "2 active, 1 suppressed" in result
            assert "Severity: critical" in result

    @pytest.mark.asyncio
    async def test_alert_details_multi_cluster_with_filter(self, env_setup):
        """Test multi-cluster alert details with cluster filter"""
        multi_cluster_data = {
            "grids": [
                {
                    "alertGroups": [
                        {
                            "labels": [
                                {"name": "alertname", "value": "HighMemoryUsage"},
                                {"name": "severity", "value": "warning"},
                            ],
                            "alerts": [
                                {
                                    "state": "active",
                                    "labels": [{"name": "namespace", "value": "prod"}],
                                    "alertmanager": [
                                        {"cluster": "prod-cluster", "name": "am1"}
                                    ],
                                },
                                {
                                    "state": "active",
                                    "labels": [
                                        {"name": "namespace", "value": "staging"}
                                    ],
                                    "alertmanager": [
                                        {"cluster": "staging-cluster", "name": "am2"}
                                    ],
                                },
                            ],
                        }
                    ]
                }
            ]
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = multi_cluster_data
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await get_alert_details_multi_cluster(
                "HighMemoryUsage", "prod-cluster"
            )

            assert "in cluster 'prod-cluster'" in result
            assert "prod-cluster" in result
            assert "staging-cluster" not in result
            assert "Total: 1 instance" in result

    @pytest.mark.asyncio
    async def test_alert_details_multi_cluster_not_found(self, env_setup):
        """Test multi-cluster alert details when alert not found"""
        empty_data = {"grids": [{"alertGroups": []}]}

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = empty_data
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await get_alert_details_multi_cluster("NonExistentAlert")

            assert "No instances of alert 'NonExistentAlert' found" in result
            assert "across all clusters" in result

    @pytest.mark.asyncio
    async def test_alert_details_case_insensitive(self, env_setup):
        """Test that alert name search is case insensitive"""
        data = {
            "grids": [
                {
                    "alertGroups": [
                        {
                            "labels": [
                                {"name": "alertname", "value": "KubePodCrashLooping"}
                            ],
                            "alerts": [
                                {
                                    "state": "active",
                                    "labels": [],
                                    "alertmanager": [
                                        {"cluster": "test-cluster", "name": "am1"}
                                    ],
                                }
                            ],
                        }
                    ]
                }
            ]
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = data
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Search with lowercase name
            result = await get_alert_details_multi_cluster("kubepodcrashlooping")

            assert "Alert Details: 'kubepodcrashlooping'" in result
            assert "Total Instances: 1" in result

    @pytest.mark.asyncio
    async def test_alert_details_with_annotations(self, env_setup):
        """Test that alert annotations are properly displayed"""
        data = {
            "grids": [
                {
                    "alertGroups": [
                        {
                            "labels": [{"name": "alertname", "value": "TestAlert"}],
                            "alerts": [
                                {
                                    "state": "active",
                                    "labels": [
                                        {"name": "service", "value": "api-service"},
                                        {
                                            "name": "deployment",
                                            "value": "api-deployment",
                                        },
                                    ],
                                    "annotations": [
                                        {
                                            "name": "description",
                                            "value": "This is a test description that is quite long and should be truncated if it exceeds the maximum length that we have defined for descriptions in the output formatting logic",
                                        },
                                        {
                                            "name": "summary",
                                            "value": "Test alert summary",
                                        },
                                    ],
                                    "alertmanager": [
                                        {"cluster": "test-cluster", "name": "am1"}
                                    ],
                                }
                            ],
                        }
                    ]
                }
            ]
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = data
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await get_alert_details_multi_cluster("TestAlert")

            assert "Summary: Test alert summary" in result
            assert "Description:" in result
            assert "..." in result  # Description should be truncated
            assert "service=api-service" in result
            assert "deployment=api-deployment" in result
