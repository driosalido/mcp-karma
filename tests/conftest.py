"""
Pytest configuration and fixtures
"""

import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import AsyncClient, Response

# Add src directory to Python path
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from tests.fixtures.karma_data import (
    EMPTY_KARMA_RESPONSE,
    HEALTH_RESPONSE,
    SAMPLE_KARMA_RESPONSE,
)


@pytest.fixture
def karma_url():
    """Test Karma URL fixture"""
    return "http://localhost:8080"


@pytest.fixture
def env_setup(karma_url):
    """Set up environment variables for testing"""
    original_url = os.environ.get("KARMA_URL")
    os.environ["KARMA_URL"] = karma_url

    yield karma_url

    # Cleanup
    if original_url:
        os.environ["KARMA_URL"] = original_url
    elif "KARMA_URL" in os.environ:
        del os.environ["KARMA_URL"]


@pytest.fixture
def sample_karma_data():
    """Sample Karma API response data"""
    return SAMPLE_KARMA_RESPONSE


@pytest.fixture
def empty_karma_data():
    """Empty Karma API response data"""
    return EMPTY_KARMA_RESPONSE


@pytest.fixture
def health_response():
    """Sample health check response"""
    return HEALTH_RESPONSE


@pytest.fixture
def mock_httpx_client():
    """Mock httpx.AsyncClient for testing"""
    mock_client = AsyncMock(spec=AsyncClient)

    # Create mock responses
    mock_response = MagicMock(spec=Response)
    mock_response.status_code = 200
    mock_response.json.return_value = SAMPLE_KARMA_RESPONSE

    mock_health_response = MagicMock(spec=Response)
    mock_health_response.status_code = 200
    mock_health_response.json.return_value = HEALTH_RESPONSE

    # Configure mock client methods
    mock_client.get.return_value = mock_health_response
    mock_client.post.return_value = mock_response

    return mock_client


@pytest.fixture
def mock_httpx_client_with_data(sample_karma_data):
    """Mock httpx client that returns specific test data"""

    def _create_mock(data=None, status_code=200, method_responses=None):
        mock_client = AsyncMock(spec=AsyncClient)

        if method_responses:
            # Configure specific responses for different methods
            for method, response_data in method_responses.items():
                mock_response = MagicMock(spec=Response)
                mock_response.status_code = response_data.get("status_code", 200)
                mock_response.json.return_value = response_data.get("data", {})

                if method == "get":
                    mock_client.get.return_value = mock_response
                elif method == "post":
                    mock_client.post.return_value = mock_response
        else:
            # Default behavior
            mock_response = MagicMock(spec=Response)
            mock_response.status_code = status_code
            mock_response.json.return_value = data or sample_karma_data

            mock_client.get.return_value = mock_response
            mock_client.post.return_value = mock_response

        return mock_client

    return _create_mock


@pytest.fixture
def mock_failing_httpx_client():
    """Mock httpx client that simulates failures"""
    mock_client = AsyncMock(spec=AsyncClient)
    mock_client.get.side_effect = Exception("Connection failed")
    mock_client.post.side_effect = Exception("Connection failed")
    return mock_client


# Parametrized fixtures for different states
@pytest.fixture(params=["active", "suppressed", "all"])
def alert_states(request):
    """Parametrized fixture for different alert states"""
    return request.param


@pytest.fixture(params=["critical", "warning", "info", "unknown"])
def alert_severities(request):
    """Parametrized fixture for different alert severities"""
    return request.param


@pytest.fixture(params=["production", "staging", "monitoring", "kube-system"])
def alert_namespaces(request):
    """Parametrized fixture for different namespaces"""
    return request.param


class MockAsyncContextManager:
    """Helper class for mocking async context managers"""

    def __init__(self, mock_client):
        self.mock_client = mock_client

    async def __aenter__(self):
        return self.mock_client

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


@pytest.fixture
def mock_httpx_async_client(mock_httpx_client):
    """Mock httpx.AsyncClient with async context manager support"""
    return MockAsyncContextManager(mock_httpx_client)


# Test data helpers
@pytest.fixture
def create_test_alert():
    """Factory for creating test alert data"""

    def _create_alert(
        name="TestAlert",
        state="active",
        severity="warning",
        namespace="test-ns",
        instance="10.1.1.1:8080",
        description="Test alert description",
    ):
        return {
            "annotations": [
                {"name": "description", "value": description},
                {"name": "summary", "value": f"{name} summary"},
            ],
            "labels": [
                {"name": "instance", "value": instance},
                {"name": "namespace", "value": namespace},
                {"name": "pod", "value": f"{name.lower()}-pod"},
            ],
            "startsAt": "2025-09-04T10:00:00Z",
            "state": state,
            "alertmanager": [
                {"cluster": "test-cluster", "name": "alertmanager", "state": state}
            ],
            "receiver": "test-receiver",
            "id": f"alert-{name.lower()}",
        }

    return _create_alert


@pytest.fixture
def create_test_group():
    """Factory for creating test alert groups"""

    def _create_group(alertname="TestAlert", severity="warning", alerts=None):
        if alerts is None:
            alerts = []

        return {
            "receiver": "test-receiver",
            "labels": [
                {"name": "alertname", "value": alertname},
                {"name": "severity", "value": severity},
            ],
            "alerts": alerts,
            "id": f"group-{alertname.lower()}",
            "alertmanagerCount": {
                "active": len([a for a in alerts if a.get("state") == "active"])
            },
            "stateCount": {
                "active": len([a for a in alerts if a.get("state") == "active"]),
                "suppressed": len(
                    [a for a in alerts if a.get("state") == "suppressed"]
                ),
            },
            "totalAlerts": len(alerts),
        }

    return _create_group
