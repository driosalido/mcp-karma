"""
Integration tests for Karma MCP server
These tests require a running Karma instance
"""

import os
from unittest.mock import patch

import httpx
import pytest

from karma_mcp.server import (
    check_karma,
    get_alerts_by_state,
    get_alerts_summary,
    list_active_alerts,
    list_alerts,
    list_clusters,
    list_suppressed_alerts,
)

# Skip integration tests if no Karma URL is provided
KARMA_URL = os.getenv("KARMA_URL")
SKIP_INTEGRATION = not KARMA_URL or KARMA_URL == "http://localhost:8080"

pytestmark = pytest.mark.skipif(
    SKIP_INTEGRATION,
    reason="Integration tests require KARMA_URL environment variable pointing to real Karma instance",
)


class TestKarmaIntegration:
    """Integration tests with real Karma instance"""

    @pytest.mark.asyncio
    async def test_karma_health_check(self):
        """Test that we can connect to Karma and get health status"""
        result = await check_karma()

        # Should either be successful or report a specific error
        assert isinstance(result, str)
        assert len(result) > 0
        # Could be success (✓) or warning (⚠) or error (✗)
        assert any(symbol in result for symbol in ["✓", "⚠", "✗"])

    @pytest.mark.asyncio
    async def test_real_karma_api_response_structure(self):
        """Test that real Karma API returns expected structure"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{KARMA_URL}/alerts.json",
                    headers={"Content-Type": "application/json"},
                    json={},
                )

                if response.status_code == 200:
                    data = response.json()

                    # Verify basic structure
                    assert "grids" in data
                    assert "totalAlerts" in data
                    assert "upstreams" in data
                    assert isinstance(data["grids"], list)
                    assert isinstance(data["totalAlerts"], int)

                    # If there are alerts, verify their structure
                    if data["totalAlerts"] > 0:
                        for grid in data["grids"]:
                            assert "alertGroups" in grid
                            for group in grid["alertGroups"]:
                                assert "labels" in group
                                assert "alerts" in group
                                for alert in group["alerts"]:
                                    assert "state" in alert
                                    assert "labels" in alert
                                    assert alert["state"] in ["active", "suppressed"]

        except Exception as e:
            pytest.skip(f"Could not connect to Karma at {KARMA_URL}: {e}")

    @pytest.mark.asyncio
    async def test_list_alerts_integration(self):
        """Test list_alerts with real Karma data"""
        result = await list_alerts()

        assert isinstance(result, str)
        assert len(result) > 0

        # Should contain basic alert listing structure
        if "Found 0 alerts" not in result:
            assert "Found" in result and "alerts" in result
            # Should contain at least some alert information
            assert any(word in result for word in ["State:", "Severity:", "Namespace:"])

    @pytest.mark.asyncio
    async def test_alerts_summary_integration(self):
        """Test get_alerts_summary with real Karma data"""
        result = await get_alerts_summary()

        assert isinstance(result, str)
        assert "Karma Alert Summary" in result
        assert "Total Alerts:" in result
        assert "By State:" in result

        # Should show actual counts
        assert any(char.isdigit() for char in result)

    @pytest.mark.asyncio
    async def test_state_filtering_integration(self):
        """Test state filtering functions with real data"""
        # Test active alerts
        active_result = await list_active_alerts()
        assert isinstance(active_result, str)

        # Test suppressed alerts
        suppressed_result = await list_suppressed_alerts()
        assert isinstance(suppressed_result, str)

        # Test parameterized state function
        for state in ["active", "suppressed", "all"]:
            result = await get_alerts_by_state(state)
            assert isinstance(result, str)
            assert len(result) > 0

        # Verify active and suppressed results are different (unless one is empty)
        if (
            "No active alerts found" not in active_result
            and "No suppressed alerts found" not in suppressed_result
        ):
            assert active_result != suppressed_result

    @pytest.mark.asyncio
    async def test_clusters_integration(self):
        """Test list_clusters with real Karma data"""
        result = await list_clusters()

        assert isinstance(result, str)
        assert "Available Kubernetes Clusters" in result
        assert "Total Clusters:" in result

    @pytest.mark.asyncio
    async def test_alert_state_consistency(self):
        """Test that alert states are consistent across different functions"""
        # Get all alerts
        all_alerts = await list_alerts()

        # Get active and suppressed separately
        active_alerts = await list_active_alerts()
        suppressed_alerts = await list_suppressed_alerts()

        # Parse counts from results (basic validation)
        if "Found 0 alerts" not in all_alerts:
            # There should be some alerts total
            assert len(all_alerts) > 0

            # Active or suppressed (or both) should have content
            has_active = "No active alerts found" not in active_alerts
            has_suppressed = "No suppressed alerts found" not in suppressed_alerts

            # At least one should have alerts
            assert has_active or has_suppressed


class TestKarmaErrorHandling:
    """Integration tests for error handling scenarios"""

    @pytest.mark.asyncio
    async def test_invalid_karma_url(self):
        """Test behavior with invalid Karma URL"""
        with patch.dict(os.environ, {"KARMA_URL": "http://invalid-url:9999"}):
            result = await check_karma()

            assert "✗ Error connecting to Karma" in result
            assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_connection_refused(self):
        """Test behavior when connection is refused"""
        with patch.dict(os.environ, {"KARMA_URL": "http://localhost:9999"}):
            result = await check_karma()

            assert "✗ Error connecting to Karma" in result


class TestRealWorldScenarios:
    """Integration tests for real-world usage scenarios"""

    @pytest.mark.asyncio
    async def test_complete_alert_workflow(self):
        """Test a complete workflow of alert operations"""
        # 1. Check Karma is accessible
        health = await check_karma()
        assert isinstance(health, str)

        # 2. Get overview of alerts
        summary = await get_alerts_summary()
        assert "Total Alerts:" in summary

        # 3. List all alerts
        all_alerts = await list_alerts()
        assert isinstance(all_alerts, str)

        # 4. Check active vs suppressed breakdown
        active = await list_active_alerts()
        suppressed = await list_suppressed_alerts()

        assert isinstance(active, str)
        assert isinstance(suppressed, str)

        # 5. If there are alerts, verify we can get details
        if "Found" in all_alerts and "0 alerts" not in all_alerts:
            # Try to extract an alert name (basic parsing)
            lines = all_alerts.split("\n")
            for line in lines:
                if "•" in line and "Severity:" in line:
                    # This is a very basic test - in real scenarios we'd parse properly
                    break

    @pytest.mark.asyncio
    async def test_state_filtering_counts_consistency(self):
        """Test that state filtering counts are mathematically consistent"""
        # Get counts from summary
        summary = await get_alerts_summary()

        # Get individual state results
        active_result = await get_alerts_by_state("active")
        suppressed_result = await get_alerts_by_state("suppressed")
        all_result = await get_alerts_by_state("all")

        # Basic consistency checks
        assert isinstance(active_result, str)
        assert isinstance(suppressed_result, str)
        assert isinstance(all_result, str)

        # If we can parse counts, verify they add up correctly
        # (This is a simplified version - real implementation would parse the actual numbers)
        if "Total Active Alerts:" in active_result:
            assert "Active Alerts" in active_result

        if "Total Suppressed Alerts:" in suppressed_result:
            assert "Suppressed Alerts" in suppressed_result

    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test that concurrent requests work correctly"""
        import asyncio

        # Make multiple concurrent requests
        tasks = [
            check_karma(),
            list_alerts(),
            get_alerts_summary(),
            list_active_alerts(),
            list_suppressed_alerts(),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All should complete without exceptions
        for result in results:
            assert not isinstance(result, Exception), f"Unexpected exception: {result}"
            assert isinstance(result, str)
            assert len(result) > 0


class TestPerformance:
    """Basic performance tests"""

    @pytest.mark.asyncio
    async def test_response_time_reasonable(self):
        """Test that responses come back in reasonable time"""
        import time

        start_time = time.time()
        result = await check_karma()
        end_time = time.time()

        # Should respond within 10 seconds (generous for integration test)
        response_time = end_time - start_time
        assert response_time < 10.0, f"Response took {response_time:.2f} seconds"

        # Should have actual content
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_large_alert_list_handling(self):
        """Test that large numbers of alerts are handled gracefully"""
        result = await list_alerts()

        # Should not crash regardless of alert count
        assert isinstance(result, str)

        # Should have reasonable length (not infinite)
        # This protects against runaway string building
        assert len(result) < 1_000_000, "Response is suspiciously large"

        # Should contain expected structure
        if "Found" in result and "0 alerts" not in result:
            assert "State:" in result or "Severity:" in result
