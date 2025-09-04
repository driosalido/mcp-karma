#!/usr/bin/env python3
"""
Simple MCP server for Karma Alerts using FastMCP
"""

import logging
import os

import httpx
from mcp.server.fastmcp import FastMCP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration from environment variables
KARMA_URL = os.getenv("KARMA_URL", "http://localhost:8080")

# Create FastMCP server
mcp = FastMCP("karma-mcp")


@mcp.tool()
async def check_karma() -> str:
    """Check connection to Karma server"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{KARMA_URL}/health")
            if response.status_code == 200:
                return f"✓ Karma is running at {KARMA_URL}"
            else:
                return f"⚠ Karma responded with code {response.status_code}"
    except Exception as e:
        return f"✗ Error connecting to Karma: {str(e)}"


@mcp.tool()
async def list_alerts() -> str:
    """List all active alerts in Karma"""
    try:
        async with httpx.AsyncClient() as client:
            # Karma API endpoint for alerts - requires POST
            response = await client.post(
                f"{KARMA_URL}/alerts.json",
                headers={"Content-Type": "application/json"},
                json={},
            )

            if response.status_code == 200:
                data = response.json()

                # Karma returns alerts grouped by grid/alertGroups
                total_alerts = 0
                alert_text = ""

                grids = data.get("grids", [])
                if not grids:
                    return "No active alerts"

                for grid in grids:
                    for group in grid.get("alertGroups", []):
                        # Get group labels (contains alertname)
                        group_labels_dict = {}
                        for label in group.get("labels", []):
                            group_labels_dict[label.get("name", "")] = label.get(
                                "value", ""
                            )

                        alerts = group.get("alerts", [])
                        total_alerts += len(alerts)

                        for alert in alerts[:10]:  # Show max 10 alerts per group
                            # Get alert-specific labels
                            alert_labels_dict = {}
                            for label in alert.get("labels", []):
                                alert_labels_dict[label.get("name", "")] = label.get(
                                    "value", ""
                                )

                            # alertname is in group labels, not alert labels
                            alertname = group_labels_dict.get("alertname", "No name")
                            severity = group_labels_dict.get(
                                "severity", alert_labels_dict.get("severity", "unknown")
                            )
                            namespace = alert_labels_dict.get("namespace", "N/A")

                            alert_text += f"• {alertname}\n"
                            alert_text += f"  Severity: {severity}\n"
                            alert_text += f"  State: {alert.get('state', 'unknown')}\n"
                            alert_text += f"  Namespace: {namespace}\n\n"

                if total_alerts == 0:
                    return "No active alerts"

                alert_text = f"Found {total_alerts} alerts:\n\n" + alert_text
                return alert_text
            else:
                return f"Error fetching alerts: code {response.status_code}"

    except Exception as e:
        return f"Error connecting to Karma: {str(e)}"


@mcp.tool()
async def get_alerts_summary() -> str:
    """Get a summary of alerts grouped by severity and state"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{KARMA_URL}/alerts.json",
                headers={"Content-Type": "application/json"},
                json={},
            )

            if response.status_code == 200:
                data = response.json()

                # Count alerts by severity and state
                severity_counts = {}
                state_counts = {"active": 0, "suppressed": 0}
                alert_names = set()

                grids = data.get("grids", [])
                for grid in grids:
                    for group in grid.get("alertGroups", []):
                        # Get group labels
                        group_labels_dict = {}
                        for label in group.get("labels", []):
                            group_labels_dict[label.get("name", "")] = label.get(
                                "value", ""
                            )

                        alertname = group_labels_dict.get("alertname", "unknown")
                        severity = group_labels_dict.get("severity", "unknown")
                        alert_names.add(alertname)

                        alerts = group.get("alerts", [])
                        for alert in alerts:
                            state = alert.get("state", "unknown")

                            # Count by severity
                            if severity not in severity_counts:
                                severity_counts[severity] = 0
                            severity_counts[severity] += 1

                            # Count by state
                            if state in state_counts:
                                state_counts[state] += 1

                # Format summary
                summary = "Karma Alert Summary\n"
                summary += "=" * 50 + "\n\n"

                total_alerts = sum(state_counts.values())
                summary += f"Total Alerts: {total_alerts}\n"
                summary += f"Unique Alert Types: {len(alert_names)}\n\n"

                summary += "By State:\n"
                for state, count in state_counts.items():
                    percentage = (count / total_alerts * 100) if total_alerts > 0 else 0
                    summary += f"  {state.capitalize()}: {count} ({percentage:.1f}%)\n"

                summary += "\nBy Severity:\n"
                for severity, count in sorted(
                    severity_counts.items(), key=lambda x: x[1], reverse=True
                ):
                    percentage = (count / total_alerts * 100) if total_alerts > 0 else 0
                    summary += (
                        f"  {severity.capitalize()}: {count} ({percentage:.1f}%)\n"
                    )

                summary += "\nTop Alert Types:\n"
                # Count alerts by type
                alert_type_counts = {}
                for grid in grids:
                    for group in grid.get("alertGroups", []):
                        group_labels_dict = {}
                        for label in group.get("labels", []):
                            group_labels_dict[label.get("name", "")] = label.get(
                                "value", ""
                            )

                        alertname = group_labels_dict.get("alertname", "unknown")
                        alert_count = len(group.get("alerts", []))

                        if alertname not in alert_type_counts:
                            alert_type_counts[alertname] = 0
                        alert_type_counts[alertname] += alert_count

                # Show top 10 alert types
                top_alerts = sorted(
                    alert_type_counts.items(), key=lambda x: x[1], reverse=True
                )[:10]
                for alertname, count in top_alerts:
                    summary += f"  {alertname}: {count}\n"

                return summary
            else:
                return f"Error fetching alerts: code {response.status_code}"

    except Exception as e:
        return f"Error connecting to Karma: {str(e)}"


@mcp.tool()
async def list_clusters() -> str:
    """List all available Kubernetes clusters in Karma"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{KARMA_URL}/alerts.json",
                headers={"Content-Type": "application/json"},
                json={},
            )

            if response.status_code == 200:
                data = response.json()

                # Get clusters from upstreams
                upstreams = data.get("upstreams", {})
                instances = upstreams.get("instances", [])

                clusters = {}
                for instance in instances:
                    cluster_name = instance.get("cluster", "unknown")
                    cluster_uri = instance.get("publicURI", "N/A")
                    cluster_version = instance.get("version", "N/A")
                    cluster_error = instance.get("error", "")

                    clusters[cluster_name] = {
                        "uri": cluster_uri,
                        "version": cluster_version,
                        "status": "healthy"
                        if not cluster_error
                        else f"error: {cluster_error}",
                        "instance_name": instance.get("name", "N/A"),
                    }

                # Count alerts per cluster
                cluster_alert_counts = {}
                grids = data.get("grids", [])

                for grid in grids:
                    for group in grid.get("alertGroups", []):
                        for alert in group.get("alerts", []):
                            alertmanagers = alert.get("alertmanager", [])
                            for am in alertmanagers:
                                cluster = am.get("cluster", "unknown")
                                if cluster not in cluster_alert_counts:
                                    cluster_alert_counts[cluster] = 0
                                cluster_alert_counts[cluster] += 1

                # Format output
                result = "Available Kubernetes Clusters\n"
                result += "=" * 50 + "\n\n"

                for cluster_name, info in sorted(clusters.items()):
                    alert_count = cluster_alert_counts.get(cluster_name, 0)
                    result += f"📋 {cluster_name}\n"
                    result += f"   Instance: {info['instance_name']}\n"
                    result += f"   Status: {info['status']}\n"
                    result += f"   Alertmanager: {info['version']}\n"
                    result += f"   Active Alerts: {alert_count}\n"
                    result += f"   URI: {info['uri']}\n\n"

                result += f"Total Clusters: {len(clusters)}\n"
                result += f"Total Alert Instances: {sum(cluster_alert_counts.values())}"

                return result
            else:
                return f"Error fetching clusters: code {response.status_code}"

    except Exception as e:
        return f"Error connecting to Karma: {str(e)}"


@mcp.tool()
async def list_alerts_by_cluster(cluster_name: str) -> str:
    """List alerts filtered by specific cluster

    Args:
        cluster_name: Name of the cluster to filter by (e.g., 'teddy-prod', 'edge-prod')
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{KARMA_URL}/alerts.json",
                headers={"Content-Type": "application/json"},
                json={},
            )

            if response.status_code == 200:
                data = response.json()

                cluster_alerts = []
                grids = data.get("grids", [])

                for grid in grids:
                    for group in grid.get("alertGroups", []):
                        # Get group labels (contains alertname)
                        group_labels_dict = {}
                        for label in group.get("labels", []):
                            group_labels_dict[label.get("name", "")] = label.get(
                                "value", ""
                            )

                        for alert in group.get("alerts", []):
                            # Check if this alert belongs to the specified cluster
                            alertmanagers = alert.get("alertmanager", [])
                            for am in alertmanagers:
                                if (
                                    am.get("cluster", "").lower()
                                    == cluster_name.lower()
                                ):
                                    # Get alert-specific labels
                                    alert_labels_dict = {}
                                    for label in alert.get("labels", []):
                                        alert_labels_dict[label.get("name", "")] = (
                                            label.get("value", "")
                                        )

                                    cluster_alerts.append(
                                        {
                                            "alert": alert,
                                            "group_labels": group_labels_dict,
                                            "alert_labels": alert_labels_dict,
                                            "alertmanager": am,
                                        }
                                    )
                                    break  # Found in this cluster, no need to check other alertmanagers

                if not cluster_alerts:
                    return f"No alerts found for cluster: {cluster_name}"

                # Format output
                result = f"Alerts in cluster '{cluster_name}'\n"
                result += "=" * 50 + "\n\n"
                result += f"Found {len(cluster_alerts)} alerts:\n\n"

                for i, item in enumerate(cluster_alerts, 1):
                    alert = item["alert"]
                    group_labels = item["group_labels"]
                    alert_labels = item["alert_labels"]
                    am = item["alertmanager"]

                    alertname = group_labels.get("alertname", "No name")
                    severity = group_labels.get(
                        "severity", alert_labels.get("severity", "unknown")
                    )
                    namespace = alert_labels.get("namespace", "N/A")
                    state = alert.get("state", "unknown")

                    result += f"{i:2d}. {alertname}\n"
                    result += f"    Severity: {severity}\n"
                    result += f"    State: {state}\n"
                    result += f"    Namespace: {namespace}\n"
                    result += f"    Cluster: {am.get('cluster', 'N/A')}\n"

                    if "instance" in alert_labels:
                        result += f"    Instance: {alert_labels['instance']}\n"

                    result += "\n"

                return result
            else:
                return f"Error fetching alerts: code {response.status_code}"

    except Exception as e:
        return f"Error connecting to Karma: {str(e)}"


@mcp.tool()
async def get_alert_details(alert_name: str) -> str:
    """Get detailed information about a specific alert

    Args:
        alert_name: Name of the alert to get details for
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{KARMA_URL}/alerts.json",
                headers={"Content-Type": "application/json"},
                json={},
            )

            if response.status_code == 200:
                data = response.json()

                # Find matching alerts across all grids and groups
                matching_alerts = []
                grids = data.get("grids", [])

                for grid in grids:
                    for group in grid.get("alertGroups", []):
                        # Get group labels (contains alertname)
                        group_labels_dict = {}
                        for label in group.get("labels", []):
                            group_labels_dict[label.get("name", "")] = label.get(
                                "value", ""
                            )

                        # Check if this group matches the alert name
                        if (
                            group_labels_dict.get("alertname", "").lower()
                            == alert_name.lower()
                        ):
                            for alert in group.get("alerts", []):
                                # Convert alert labels array to dictionary
                                alert_labels_dict = {}
                                for label in alert.get("labels", []):
                                    alert_labels_dict[label.get("name", "")] = (
                                        label.get("value", "")
                                    )

                                matching_alerts.append(
                                    {
                                        "alert": alert,
                                        "group_labels": group_labels_dict,
                                        "alert_labels": alert_labels_dict,
                                    }
                                )

                if not matching_alerts:
                    return f"No alert found with name: {alert_name}"

                # Format alert details
                details = (
                    f"Found {len(matching_alerts)} instance(s) of {alert_name}:\n\n"
                )

                for i, item in enumerate(matching_alerts, 1):
                    alert = item["alert"]
                    group_labels = item["group_labels"]
                    alert_labels = item["alert_labels"]

                    # Convert annotations array to dictionary
                    annotations_dict = {}
                    for annotation in alert.get("annotations", []):
                        annotations_dict[annotation.get("name", "")] = annotation.get(
                            "value", ""
                        )

                    details += f"Instance {i}:\n"
                    details += f"  State: {alert.get('state', 'unknown')}\n"
                    details += (
                        f"  Severity: {group_labels.get('severity', 'unknown')}\n"
                    )

                    if "instance" in alert_labels:
                        details += f"  Instance: {alert_labels['instance']}\n"

                    if "namespace" in alert_labels:
                        details += f"  Namespace: {alert_labels['namespace']}\n"

                    if "description" in annotations_dict:
                        description = annotations_dict["description"]
                        if len(description) > 200:
                            description = description[:200] + "..."
                        details += f"  Description: {description}\n"

                    if "summary" in annotations_dict:
                        details += f"  Summary: {annotations_dict['summary']}\n"

                    details += "\n"

                return details
            else:
                return f"Error fetching alerts: code {response.status_code}"

    except Exception as e:
        return f"Error connecting to Karma: {str(e)}"


@mcp.tool()
async def list_active_alerts() -> str:
    """List only active (non-suppressed) alerts"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{KARMA_URL}/alerts.json",
                headers={"Content-Type": "application/json"},
                json={},
            )

            if response.status_code == 200:
                data = response.json()

                active_alerts = []
                grids = data.get("grids", [])

                for grid in grids:
                    for group in grid.get("alertGroups", []):
                        # Get group labels (contains alertname)
                        group_labels_dict = {}
                        for label in group.get("labels", []):
                            group_labels_dict[label.get("name", "")] = label.get(
                                "value", ""
                            )

                        alertname = group_labels_dict.get("alertname", "unknown")

                        for alert in group.get("alerts", []):
                            alert_state = alert.get("state", "unknown")

                            # Only include active alerts (not suppressed)
                            if alert_state.lower() == "active":
                                # Convert alert labels to dict
                                alert_labels_dict = {}
                                for label in alert.get("labels", []):
                                    alert_labels_dict[label.get("name", "")] = (
                                        label.get("value", "")
                                    )

                                active_alerts.append(
                                    {
                                        "name": alertname,
                                        "state": alert_state,
                                        "severity": group_labels_dict.get(
                                            "severity", "unknown"
                                        ),
                                        "namespace": alert_labels_dict.get(
                                            "namespace", "N/A"
                                        ),
                                        "instance": alert_labels_dict.get(
                                            "instance", "N/A"
                                        ),
                                        "starts_at": alert.get("startsAt", "N/A"),
                                    }
                                )

                if not active_alerts:
                    return "No active alerts found."

                # Format output
                result = "Active Alerts (Non-Suppressed)\n"
                result += "=" * 50 + "\n\n"

                # Group by alert name
                alert_groups = {}
                for alert in active_alerts:
                    name = alert["name"]
                    if name not in alert_groups:
                        alert_groups[name] = []
                    alert_groups[name].append(alert)

                for alertname, alerts in sorted(alert_groups.items()):
                    result += f"🔥 {alertname} ({len(alerts)} instance{'s' if len(alerts) > 1 else ''})\n"
                    result += f"   Severity: {alerts[0]['severity']}\n"

                    # Show details for each instance
                    for alert in alerts[:5]:  # Limit to 5 instances to avoid clutter
                        result += f"   • {alert['instance']} ({alert['namespace']})\n"

                    if len(alerts) > 5:
                        result += f"   • ... and {len(alerts) - 5} more\n"

                    result += "\n"

                result += f"Total Active Alerts: {len(active_alerts)}"
                return result
            else:
                return f"Error fetching alerts: code {response.status_code}"

    except Exception as e:
        return f"Error connecting to Karma: {str(e)}"


@mcp.tool()
async def list_suppressed_alerts() -> str:
    """List only suppressed alerts"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{KARMA_URL}/alerts.json",
                headers={"Content-Type": "application/json"},
                json={},
            )

            if response.status_code == 200:
                data = response.json()

                suppressed_alerts = []
                grids = data.get("grids", [])

                for grid in grids:
                    for group in grid.get("alertGroups", []):
                        # Get group labels (contains alertname)
                        group_labels_dict = {}
                        for label in group.get("labels", []):
                            group_labels_dict[label.get("name", "")] = label.get(
                                "value", ""
                            )

                        alertname = group_labels_dict.get("alertname", "unknown")

                        for alert in group.get("alerts", []):
                            alert_state = alert.get("state", "unknown")

                            # Only include suppressed alerts
                            if alert_state.lower() == "suppressed":
                                # Convert alert labels to dict
                                alert_labels_dict = {}
                                for label in alert.get("labels", []):
                                    alert_labels_dict[label.get("name", "")] = (
                                        label.get("value", "")
                                    )

                                suppressed_alerts.append(
                                    {
                                        "name": alertname,
                                        "state": alert_state,
                                        "severity": group_labels_dict.get(
                                            "severity", "unknown"
                                        ),
                                        "namespace": alert_labels_dict.get(
                                            "namespace", "N/A"
                                        ),
                                        "instance": alert_labels_dict.get(
                                            "instance", "N/A"
                                        ),
                                        "starts_at": alert.get("startsAt", "N/A"),
                                    }
                                )

                if not suppressed_alerts:
                    return "No suppressed alerts found."

                # Format output
                result = "Suppressed Alerts\n"
                result += "=" * 50 + "\n\n"

                # Group by alert name
                alert_groups = {}
                for alert in suppressed_alerts:
                    name = alert["name"]
                    if name not in alert_groups:
                        alert_groups[name] = []
                    alert_groups[name].append(alert)

                for alertname, alerts in sorted(alert_groups.items()):
                    result += f"🔕 {alertname} ({len(alerts)} instance{'s' if len(alerts) > 1 else ''})\n"
                    result += f"   Severity: {alerts[0]['severity']}\n"

                    # Show details for each instance
                    for alert in alerts[:5]:  # Limit to 5 instances to avoid clutter
                        result += f"   • {alert['instance']} ({alert['namespace']})\n"

                    if len(alerts) > 5:
                        result += f"   • ... and {len(alerts) - 5} more\n"

                    result += "\n"

                result += f"Total Suppressed Alerts: {len(suppressed_alerts)}"
                return result
            else:
                return f"Error fetching alerts: code {response.status_code}"

    except Exception as e:
        return f"Error connecting to Karma: {str(e)}"


@mcp.tool()
async def get_alerts_by_state(state: str) -> str:
    """Get alerts filtered by state (active, suppressed, or all)"""
    valid_states = ["active", "suppressed", "all"]

    if state.lower() not in valid_states:
        return f"Invalid state '{state}'. Valid options: {', '.join(valid_states)}"

    if state.lower() == "active":
        return await list_active_alerts()
    elif state.lower() == "suppressed":
        return await list_suppressed_alerts()
    else:  # all
        return await list_alerts()


@mcp.tool()
async def get_alert_details_multi_cluster(
    alert_name: str, cluster_filter: str = ""
) -> str:
    """Get detailed information about a specific alert across multiple clusters

    Args:
        alert_name: Name of the alert to search for (e.g., 'KubePodCrashLooping')
        cluster_filter: Optional cluster name filter. If empty, searches all clusters.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{KARMA_URL}/alerts.json",
                headers={"Content-Type": "application/json"},
                json={},
            )

            if response.status_code == 200:
                data = response.json()

                matching_alerts = []
                cluster_stats = {}
                grids = data.get("grids", [])

                for grid in grids:
                    for group in grid.get("alertGroups", []):
                        # Get group labels (contains alertname)
                        group_labels_dict = {}
                        for label in group.get("labels", []):
                            group_labels_dict[label.get("name", "")] = label.get(
                                "value", ""
                            )

                        # Check if this group matches the alert name
                        if (
                            group_labels_dict.get("alertname", "").lower()
                            == alert_name.lower()
                        ):
                            for alert in group.get("alerts", []):
                                # Get alert labels
                                alert_labels_dict = {}
                                for label in alert.get("labels", []):
                                    alert_labels_dict[label.get("name", "")] = (
                                        label.get("value", "")
                                    )

                                # Get cluster information
                                alertmanagers = alert.get("alertmanager", [])
                                for am in alertmanagers:
                                    cluster = am.get("cluster", "unknown")

                                    # Apply cluster filter if specified
                                    if (
                                        cluster_filter
                                        and cluster_filter.lower()
                                        not in cluster.lower()
                                    ):
                                        continue

                                    # Track cluster stats
                                    if cluster not in cluster_stats:
                                        cluster_stats[cluster] = {
                                            "total": 0,
                                            "active": 0,
                                            "suppressed": 0,
                                        }

                                    cluster_stats[cluster]["total"] += 1
                                    state = alert.get("state", "unknown").lower()
                                    if state in cluster_stats[cluster]:
                                        cluster_stats[cluster][state] += 1

                                    # Get annotations
                                    annotations_dict = {}
                                    for annotation in alert.get("annotations", []):
                                        annotations_dict[annotation.get("name", "")] = (
                                            annotation.get("value", "")
                                        )

                                    matching_alerts.append(
                                        {
                                            "alert_name": group_labels_dict.get(
                                                "alertname", "unknown"
                                            ),
                                            "cluster": cluster,
                                            "state": alert.get("state", "unknown"),
                                            "severity": group_labels_dict.get(
                                                "severity", "unknown"
                                            ),
                                            "namespace": alert_labels_dict.get(
                                                "namespace", "N/A"
                                            ),
                                            "instance": alert_labels_dict.get(
                                                "instance", "N/A"
                                            ),
                                            "pod": alert_labels_dict.get("pod", "N/A"),
                                            "container": alert_labels_dict.get(
                                                "container", "N/A"
                                            ),
                                            "starts_at": alert.get("startsAt", "N/A"),
                                            "alertmanager_name": am.get("name", "N/A"),
                                            "annotations": annotations_dict,
                                            "labels": alert_labels_dict,
                                        }
                                    )
                                    break  # Found in this cluster

                if not matching_alerts:
                    filter_text = (
                        f" in cluster '{cluster_filter}'"
                        if cluster_filter
                        else " across all clusters"
                    )
                    return f"No instances of alert '{alert_name}' found{filter_text}"

                # Format output
                filter_text = (
                    f" in cluster '{cluster_filter}'"
                    if cluster_filter
                    else " (multi-cluster search)"
                )
                result = f"Alert Details: '{alert_name}'{filter_text}\n"
                result += "=" * 60 + "\n\n"

                # Overall summary
                result += "📊 Summary:\n"
                result += f"   Alert Name: {alert_name}\n"
                severity = (
                    matching_alerts[0]["severity"] if matching_alerts else "unknown"
                )
                result += f"   Severity: {severity}\n"
                result += f"   Total Instances: {len(matching_alerts)}\n"
                result += f"   Clusters Affected: {len(cluster_stats)}\n\n"

                # Cluster breakdown
                result += "📈 Cluster Breakdown:\n"
                for cluster, stats in sorted(cluster_stats.items()):
                    result += f"   {cluster}: {stats['total']} instances "
                    result += f"({stats.get('active', 0)} active, {stats.get('suppressed', 0)} suppressed)\n"
                result += "\n"

                # Group alerts by cluster
                clusters_alerts = {}
                for alert in matching_alerts:
                    cluster = alert["cluster"]
                    if cluster not in clusters_alerts:
                        clusters_alerts[cluster] = []
                    clusters_alerts[cluster].append(alert)

                # Display detailed information per cluster
                for cluster, alerts in sorted(clusters_alerts.items()):
                    result += f"🏗️  Cluster: {cluster}\n"
                    result += "-" * 40 + "\n"

                    for i, alert in enumerate(
                        alerts[:10], 1
                    ):  # Limit to 10 per cluster
                        state_emoji = (
                            "🔥" if alert["state"].lower() == "active" else "🔕"
                        )
                        result += f"  {i}. {state_emoji} {alert['alert_name']}\n"
                        result += f"      State: {alert['state']}\n"
                        result += f"      Started: {alert['starts_at']}\n"

                        if alert["namespace"] != "N/A":
                            result += f"      Namespace: {alert['namespace']}\n"
                        if alert["instance"] != "N/A":
                            result += f"      Instance: {alert['instance']}\n"
                        if alert["pod"] != "N/A":
                            result += f"      Pod: {alert['pod']}\n"
                        if alert["container"] != "N/A":
                            result += f"      Container: {alert['container']}\n"

                        # Show important annotations
                        if "description" in alert["annotations"]:
                            desc = alert["annotations"]["description"]
                            if len(desc) > 150:
                                desc = desc[:150] + "..."
                            result += f"      Description: {desc}\n"
                        if "summary" in alert["annotations"]:
                            result += (
                                f"      Summary: {alert['annotations']['summary']}\n"
                            )

                        # Show key labels (limit to most important ones)
                        important_labels = [
                            "job",
                            "service",
                            "deployment",
                            "statefulset",
                        ]
                        shown_labels = []
                        for label in important_labels:
                            if label in alert["labels"]:
                                shown_labels.append(f"{label}={alert['labels'][label]}")
                        if shown_labels:
                            result += f"      Labels: {', '.join(shown_labels)}\n"

                        result += "\n"

                    if len(alerts) > 10:
                        result += f"      ... and {len(alerts) - 10} more instances\n\n"

                # Final summary
                active_count = sum(
                    1 for a in matching_alerts if a["state"].lower() == "active"
                )
                suppressed_count = sum(
                    1 for a in matching_alerts if a["state"].lower() == "suppressed"
                )
                result += f"📋 Total: {len(matching_alerts)} instance{'s' if len(matching_alerts) != 1 else ''} "
                result += f"({active_count} active, {suppressed_count} suppressed) "
                result += f"across {len(cluster_stats)} cluster{'s' if len(cluster_stats) != 1 else ''}"

                return result
            else:
                return f"Error fetching alerts: code {response.status_code}"

    except Exception as e:
        return f"Error connecting to Karma: {str(e)}"


@mcp.tool()
async def search_alerts_by_container(
    container_name: str, cluster_filter: str = ""
) -> str:
    """Search for alerts by container name across multiple clusters

    Args:
        container_name: Name of the container to search for
        cluster_filter: Optional cluster name filter (e.g., 'teddy-prod', 'edge-prod'). If empty, searches all clusters.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{KARMA_URL}/alerts.json",
                headers={"Content-Type": "application/json"},
                json={},
            )

            if response.status_code == 200:
                data = response.json()

                matching_alerts = []
                cluster_stats = {}
                grids = data.get("grids", [])

                for grid in grids:
                    for group in grid.get("alertGroups", []):
                        # Get group labels (contains alertname)
                        group_labels_dict = {}
                        for label in group.get("labels", []):
                            group_labels_dict[label.get("name", "")] = label.get(
                                "value", ""
                            )

                        alertname = group_labels_dict.get("alertname", "unknown")

                        for alert in group.get("alerts", []):
                            # Convert alert labels to dict
                            alert_labels_dict = {}
                            for label in alert.get("labels", []):
                                alert_labels_dict[label.get("name", "")] = label.get(
                                    "value", ""
                                )

                            # Check if this alert has the container label we're looking for
                            alert_container = alert_labels_dict.get("container", "")

                            if container_name.lower() in alert_container.lower():
                                # Get cluster information
                                alertmanagers = alert.get("alertmanager", [])
                                for am in alertmanagers:
                                    cluster = am.get("cluster", "unknown")

                                    # Apply cluster filter if specified
                                    if (
                                        cluster_filter
                                        and cluster_filter.lower()
                                        not in cluster.lower()
                                    ):
                                        continue

                                    # Track cluster stats
                                    if cluster not in cluster_stats:
                                        cluster_stats[cluster] = {
                                            "total": 0,
                                            "active": 0,
                                            "suppressed": 0,
                                        }

                                    cluster_stats[cluster]["total"] += 1
                                    state = alert.get("state", "unknown").lower()
                                    if state in cluster_stats[cluster]:
                                        cluster_stats[cluster][state] += 1

                                    matching_alerts.append(
                                        {
                                            "alert_name": alertname,
                                            "container": alert_container,
                                            "cluster": cluster,
                                            "state": alert.get("state", "unknown"),
                                            "severity": group_labels_dict.get(
                                                "severity", "unknown"
                                            ),
                                            "namespace": alert_labels_dict.get(
                                                "namespace", "N/A"
                                            ),
                                            "instance": alert_labels_dict.get(
                                                "instance", "N/A"
                                            ),
                                            "pod": alert_labels_dict.get("pod", "N/A"),
                                            "starts_at": alert.get("startsAt", "N/A"),
                                            "alertmanager_name": am.get("name", "N/A"),
                                        }
                                    )
                                    break  # Found in this cluster, no need to check other alertmanagers

                if not matching_alerts:
                    filter_text = (
                        f" in cluster '{cluster_filter}'"
                        if cluster_filter
                        else " across all clusters"
                    )
                    return (
                        f"No alerts found for container '{container_name}'{filter_text}"
                    )

                # Format output
                filter_text = (
                    f" in cluster '{cluster_filter}'"
                    if cluster_filter
                    else " (multi-cluster search)"
                )
                result = f"Container Alert Search: '{container_name}'{filter_text}\n"
                result += "=" * 60 + "\n\n"

                # Cluster summary
                result += "📊 Cluster Summary:\n"
                for cluster, stats in sorted(cluster_stats.items()):
                    result += f"   {cluster}: {stats['total']} alerts "
                    result += f"({stats.get('active', 0)} active, {stats.get('suppressed', 0)} suppressed)\n"
                result += "\n"

                # Group alerts by cluster and then by alert name
                clusters_alerts = {}
                for alert in matching_alerts:
                    cluster = alert["cluster"]
                    alert_name = alert["alert_name"]

                    if cluster not in clusters_alerts:
                        clusters_alerts[cluster] = {}
                    if alert_name not in clusters_alerts[cluster]:
                        clusters_alerts[cluster][alert_name] = []
                    clusters_alerts[cluster][alert_name].append(alert)

                # Display alerts grouped by cluster
                for cluster, alert_groups in sorted(clusters_alerts.items()):
                    result += f"🏗️  Cluster: {cluster}\n"
                    result += "-" * 40 + "\n"

                    for alert_name, alerts in sorted(alert_groups.items()):
                        # Count states for this alert type
                        state_counts = {"active": 0, "suppressed": 0}
                        for alert in alerts:
                            state = alert["state"].lower()
                            if state in state_counts:
                                state_counts[state] += 1

                        state_emoji = "🔥" if state_counts["active"] > 0 else "🔕"
                        result += f"  {state_emoji} {alert_name} ({len(alerts)} instance{'s' if len(alerts) > 1 else ''})\n"
                        result += f"      Severity: {alerts[0]['severity']}\n"
                        result += f"      States: {state_counts['active']} active, {state_counts['suppressed']} suppressed\n"

                        # Show container instances (limit to avoid clutter)
                        containers_shown = set()
                        for alert in alerts[:8]:  # Limit to 8 instances
                            container_info = (
                                f"{alert['container']} ({alert['namespace']})"
                            )
                            if container_info not in containers_shown:
                                state_icon = (
                                    "🔥" if alert["state"].lower() == "active" else "🔕"
                                )
                                result += f"      {state_icon} Container: {alert['container']}\n"
                                result += f"         Namespace: {alert['namespace']}\n"
                                if alert["pod"] != "N/A":
                                    result += f"         Pod: {alert['pod']}\n"
                                if alert["instance"] != "N/A":
                                    result += (
                                        f"         Instance: {alert['instance']}\n"
                                    )
                                result += "\n"
                                containers_shown.add(container_info)

                        if len(alerts) > 8:
                            result += f"      ... and {len(alerts) - len(containers_shown)} more instances\n"

                    result += "\n"

                # Final summary
                total_alerts = len(matching_alerts)
                total_clusters = len(cluster_stats)
                result += f"📋 Total: {total_alerts} alert instance{'s' if total_alerts != 1 else ''} "
                result += f"across {total_clusters} cluster{'s' if total_clusters != 1 else ''}"

                return result
            else:
                return f"Error fetching alerts: code {response.status_code}"

    except Exception as e:
        return f"Error connecting to Karma: {str(e)}"


if __name__ == "__main__":
    logger.info(f"Starting MCP server for Karma at {KARMA_URL}")
    mcp.run()
