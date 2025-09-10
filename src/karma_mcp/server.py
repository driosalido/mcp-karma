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

# Import version info from package metadata
try:
    from importlib.metadata import version
    __version__ = version("karma-mcp")
except ImportError:
    __version__ = "unknown"

# Configuration from environment variables
KARMA_URL = os.getenv("KARMA_URL", "http://localhost:8080")

# Create FastMCP server
mcp = FastMCP("karma-mcp")

# Log server startup information
logger.info(f"🚀 Starting Karma MCP Server v{__version__}")
logger.info(f"🌐 Karma URL configured: {KARMA_URL}")


# Utility functions to reduce code duplication
async def create_karma_client():
    """Create and configure HTTP client for Karma API calls"""
    return httpx.AsyncClient()


async def fetch_karma_alerts():
    """Fetch alerts data from Karma API with common error handling"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{KARMA_URL}/alerts.json",
                headers={"Content-Type": "application/json"},
                json={},
            )

            if response.status_code != 200:
                return None, f"Error fetching alerts: code {response.status_code}"

            data = response.json()
            grids = data.get("grids", [])

            if not grids:
                return None, "No active alerts"

            return data, None

    except Exception as e:
        return None, f"Error connecting to Karma: {str(e)}"


def extract_label_value(labels: list, name: str, default: str = "unknown") -> str:
    """Extract a label value from a list of label objects"""
    if not labels:
        return default
    for label in labels:
        if label.get("name", "") == name:
            return label.get("value", default)
    return default


def extract_alert_metadata(group, alert):
    """Extract common alert metadata (alertname, severity, namespace, cluster)"""
    group_labels = group.get("labels", [])
    alert_labels = alert.get("labels", [])

    alertname = extract_label_value(group_labels, "alertname", "Unknown")

    # Severity can be in group or alert labels
    severity = extract_label_value(group_labels, "severity")
    if severity == "unknown":
        severity = extract_label_value(alert_labels, "severity", "none")

    namespace = extract_label_value(alert_labels, "namespace", "N/A")

    # Extract cluster from alertmanager info
    cluster = "unknown"
    for am in alert.get("alertmanager", []):
        if "cluster" in am:
            cluster = am["cluster"]
            break

    return {
        "alertname": alertname,
        "severity": severity,
        "namespace": namespace,
        "cluster": cluster,
        "state": alert.get("state", "unknown"),
        "starts_at": alert.get("startsAt", ""),
        "group_id": group.get("id", ""),
        "receiver": alert.get("receiver", "unknown"),
    }


def format_alert_summary(alerts_data, include_clusters=False):
    """Format alert data into a readable summary"""
    total_alerts = 0
    severity_counts = {"critical": 0, "warning": 0, "info": 0, "none": 0}
    state_counts = {"active": 0, "suppressed": 0}
    cluster_counts = {}

    grids = alerts_data.get("grids", [])

    for grid in grids:
        for group in grid.get("alertGroups", []):
            alerts = group.get("alerts", [])
            total_alerts += len(alerts)

            for alert in alerts:
                metadata = extract_alert_metadata(group, alert)

                # Count by severity
                severity = metadata["severity"]
                if severity in severity_counts:
                    severity_counts[severity] += 1

                # Count by state
                state = metadata["state"]
                if state in state_counts:
                    state_counts[state] += 1

                # Count by cluster if needed
                if include_clusters:
                    cluster = metadata["cluster"]
                    cluster_counts[cluster] = cluster_counts.get(cluster, 0) + 1

    # Format summary matching the expected test format
    summary = f"Total Alerts: {total_alerts}\n"

    # Severity breakdown
    summary += "\nBy Severity:\n"
    for severity, count in severity_counts.items():
        if count > 0:
            summary += f"  {severity.capitalize()}: {count}\n"

    summary += "\nBy State:\n"
    for state, count in state_counts.items():
        if count > 0:
            summary += f"  {state.capitalize()}: {count}\n"

    if include_clusters and cluster_counts:
        summary += "\nBy Cluster:\n"
        sorted_clusters = sorted(
            cluster_counts.items(), key=lambda x: x[1], reverse=True
        )
        for cluster, count in sorted_clusters:
            summary += f"  {cluster}: {count}\n"

    return summary


def filter_alerts_by_cluster(alerts_data, cluster_name):
    """Filter alerts data to only include alerts from a specific cluster"""
    filtered_grids = []

    for grid in alerts_data.get("grids", []):
        filtered_groups = []

        for group in grid.get("alertGroups", []):
            filtered_alerts = []

            for alert in group.get("alerts", []):
                # Check if alert belongs to specified cluster
                for am in alert.get("alertmanager", []):
                    if am.get("cluster", "").lower() == cluster_name.lower():
                        filtered_alerts.append(alert)
                        break

            if filtered_alerts:
                # Create a copy of the group with filtered alerts
                filtered_group = group.copy()
                filtered_group["alerts"] = filtered_alerts
                filtered_group["totalAlerts"] = len(filtered_alerts)
                filtered_groups.append(filtered_group)

        if filtered_groups:
            filtered_grid = grid.copy()
            filtered_grid["alertGroups"] = filtered_groups
            filtered_grids.append(filtered_grid)

    # Return filtered data structure
    filtered_data = alerts_data.copy()
    filtered_data["grids"] = filtered_grids
    return filtered_data


def extract_cluster_info(alerts_data):
    """Extract cluster information and alert counts from Karma data"""
    clusters = {}
    cluster_alert_counts = {}

    # Get clusters from upstreams
    upstreams = alerts_data.get("upstreams", {})
    instances = upstreams.get("instances", [])

    for instance in instances:
        cluster_name = instance.get("cluster", "unknown")
        cluster_uri = instance.get("publicURI", "N/A")
        cluster_version = instance.get("version", "N/A")
        cluster_error = instance.get("error", "")

        clusters[cluster_name] = {
            "uri": cluster_uri,
            "version": cluster_version,
            "status": "healthy" if not cluster_error else f"error: {cluster_error}",
            "instance_name": instance.get("name", "N/A"),
        }

    # Count alerts per cluster
    grids = alerts_data.get("grids", [])
    for grid in grids:
        for group in grid.get("alertGroups", []):
            for alert in group.get("alerts", []):
                for am in alert.get("alertmanager", []):
                    cluster = am.get("cluster", "unknown")
                    cluster_alert_counts[cluster] = (
                        cluster_alert_counts.get(cluster, 0) + 1
                    )

    return clusters, cluster_alert_counts


def extract_annotations(alert):
    """Extract annotations from alert object"""
    annotations = {}
    for annotation in alert.get("annotations", []):
        annotations[annotation.get("name", "")] = annotation.get("value", "")
    return annotations


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
    data, error = await fetch_karma_alerts()
    if error:
        return error

    # Process alerts using utility functions
    total_alerts = 0
    alert_text = ""

    grids = data.get("grids", [])
    for grid in grids:
        for group in grid.get("alertGroups", []):
            alerts = group.get("alerts", [])
            total_alerts += len(alerts)

            for alert in alerts[:10]:  # Show max 10 alerts per group
                metadata = extract_alert_metadata(group, alert)

                alert_text += f"• {metadata['alertname']}\n"
                alert_text += f"  Severity: {metadata['severity']}\n"
                alert_text += f"  State: {metadata['state']}\n"
                alert_text += f"  Namespace: {metadata['namespace']}\n\n"

    if total_alerts == 0:
        return "No active alerts"

    alert_text = f"Found {total_alerts} alerts:\n\n" + alert_text
    return alert_text


@mcp.tool()
async def get_alerts_summary() -> str:
    """Get a summary of alerts grouped by severity and state"""
    data, error = await fetch_karma_alerts()
    if error:
        return error

    # Use the centralized summary function
    summary = format_alert_summary(data, include_clusters=True)

    # Add top alert types section
    alert_type_counts = {}
    grids = data.get("grids", [])
    for grid in grids:
        for group in grid.get("alertGroups", []):
            alertname = extract_label_value(
                group.get("labels", []), "alertname", "Unknown"
            )
            alert_count = len(group.get("alerts", []))
            alert_type_counts[alertname] = (
                alert_type_counts.get(alertname, 0) + alert_count
            )

    # Add top alert types to summary
    if alert_type_counts:
        summary += "\n🔝 Top Alert Types:\n"
        top_alerts = sorted(
            alert_type_counts.items(), key=lambda x: x[1], reverse=True
        )[:10]
        for alertname, count in top_alerts:
            summary += f"  • {alertname}: {count}\n"

    return summary


@mcp.tool()
async def list_clusters() -> str:
    """List all available Kubernetes clusters in Karma"""
    data, error = await fetch_karma_alerts()
    if error:
        return error

    clusters, cluster_alert_counts = extract_cluster_info(data)

    # Format output
    result = "🏢 Available Kubernetes Clusters\n"
    result += "=" * 50 + "\n\n"

    for cluster_name, info in sorted(clusters.items()):
        alert_count = cluster_alert_counts.get(cluster_name, 0)
        status_icon = "✅" if "healthy" in info["status"] else "❌"

        result += f"📋 {cluster_name}\n"
        result += f"   Instance: {info['instance_name']}\n"
        result += f"   Status: {status_icon} {info['status']}\n"
        result += f"   Alertmanager: {info['version']}\n"
        result += f"   Active Alerts: {alert_count}\n"
        result += f"   URI: {info['uri']}\n\n"

    result += "📊 Summary:\n"
    result += f"   Total Clusters: {len(clusters)}\n"
    result += f"   Total Alert Instances: {sum(cluster_alert_counts.values())}"

    return result


@mcp.tool()
async def list_alerts_by_cluster(cluster_name: str) -> str:
    """List alerts filtered by specific cluster

    Args:
        cluster_name: Name of the cluster to filter by (e.g., 'teddy-prod', 'edge-prod')
    """
    data, error = await fetch_karma_alerts()
    if error:
        return error

    # Use utility function to filter by cluster
    filtered_data = filter_alerts_by_cluster(data, cluster_name)

    # Count filtered alerts
    total_alerts = 0
    grids = filtered_data.get("grids", [])
    for grid in grids:
        for group in grid.get("alertGroups", []):
            total_alerts += len(group.get("alerts", []))

    if total_alerts == 0:
        return f"No alerts found for cluster: {cluster_name}"

    # Format output using utility functions
    result = f"🏢 Alerts in cluster '{cluster_name}'\n"
    result += "=" * 50 + "\n\n"
    result += f"Found {total_alerts} alerts:\n\n"

    counter = 1
    for grid in grids:
        for group in grid.get("alertGroups", []):
            for alert in group.get("alerts", []):
                metadata = extract_alert_metadata(group, alert)

                result += f"{counter:2d}. {metadata['alertname']}\n"
                result += f"    Severity: {metadata['severity']}\n"
                result += f"    State: {metadata['state']}\n"
                result += f"    Namespace: {metadata['namespace']}\n"
                result += f"    Cluster: {metadata['cluster']}\n"

                # Add instance if available
                instance = extract_label_value(alert.get("labels", []), "instance")
                if instance != "unknown":
                    result += f"    Instance: {instance}\n"

                result += "\n"
                counter += 1

    return result


@mcp.tool()
async def get_alert_details(alert_name: str) -> str:
    """Get detailed information about a specific alert

    Args:
        alert_name: Name of the alert to get details for
    """
    data, error = await fetch_karma_alerts()
    if error:
        return error

    # Find matching alerts
    matching_alerts = []
    grids = data.get("grids", [])

    for grid in grids:
        for group in grid.get("alertGroups", []):
            alertname = extract_label_value(group.get("labels", []), "alertname")

            if alertname.lower() == alert_name.lower():
                for alert in group.get("alerts", []):
                    matching_alerts.append({"alert": alert, "group": group})

    if not matching_alerts:
        return f"No alert found with name: {alert_name}"

    # Format alert details
    details = f"🔍 Found {len(matching_alerts)} instance(s) of {alert_name}:\n\n"

    for i, item in enumerate(matching_alerts, 1):
        alert = item["alert"]
        group = item["group"]

        metadata = extract_alert_metadata(group, alert)
        annotations = extract_annotations(alert)

        details += f"📋 Instance {i}:\n"
        details += f"  State: {metadata['state']}\n"
        details += f"  Severity: {metadata['severity']}\n"
        details += f"  Namespace: {metadata['namespace']}\n"
        details += f"  Cluster: {metadata['cluster']}\n"

        # Add instance if available
        instance = extract_label_value(alert.get("labels", []), "instance")
        if instance != "unknown":
            details += f"  Instance: {instance}\n"

        # Add annotations
        if "description" in annotations:
            description = annotations["description"]
            if len(description) > 200:
                description = description[:200] + "..."
            details += f"  Description: {description}\n"

        if "summary" in annotations:
            details += f"  Summary: {annotations['summary']}\n"

        details += "\n"

    return details


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


@mcp.tool()
async def list_silences(cluster: str = "") -> str:
    """List all active silences across clusters or for a specific cluster

    Args:
        cluster: Optional cluster name to filter silences (e.g., 'teddy-prod')

    Returns:
        Formatted list of active silences with details
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{KARMA_URL}/alerts.json",
                json={},
                headers={"Content-Type": "application/json"},
                timeout=10.0,
            )

            if response.status_code == 200:
                data = response.json()
                silences = data.get("silences", {})

                if not silences:
                    return "No active silences found"

                # Filter by cluster if specified
                if cluster:
                    cluster_lower = cluster.lower()
                    filtered_silences = {}
                    for cluster_name, cluster_silences in silences.items():
                        if cluster_lower in cluster_name.lower():
                            filtered_silences[cluster_name] = cluster_silences
                    silences = filtered_silences

                    if not silences:
                        return f"No active silences found for cluster: {cluster}"

                # Format output
                result = f"Active Silences{f' in {cluster}' if cluster else ''}\n"
                result += "=" * 50 + "\n\n"

                total_count = 0
                for cluster_name, cluster_silences in silences.items():
                    if cluster_silences:
                        result += f"📍 Cluster: {cluster_name}\n"
                        result += f"   Silences: {len(cluster_silences)}\n\n"

                        for silence_id, silence in list(cluster_silences.items())[
                            :5
                        ]:  # Limit to 5 per cluster
                            total_count += 1
                            result += f"  🔕 Silence ID: {silence_id[:8]}...\n"
                            result += f"     Created by: {silence.get('createdBy', 'unknown')}\n"
                            result += f"     Comment: {silence.get('comment', 'No comment')}\n"
                            result += (
                                f"     Starts: {silence.get('startsAt', 'unknown')}\n"
                            )
                            result += f"     Ends: {silence.get('endsAt', 'unknown')}\n"

                            # Show matchers
                            matchers = silence.get("matchers", [])
                            if matchers:
                                result += "     Matchers:\n"
                                for matcher in matchers[:3]:  # Show first 3 matchers
                                    name = matcher.get("name", "")
                                    value = matcher.get("value", "")
                                    if len(value) > 50:
                                        value = value[:47] + "..."
                                    result += f"       - {name}: {value}\n"
                            result += "\n"

                        if len(cluster_silences) > 5:
                            result += f"   ... and {len(cluster_silences) - 5} more silences\n\n"

                result += f"\n📊 Total: {total_count} active silence{'s' if total_count != 1 else ''}"
                return result
            else:
                return f"Error fetching silences: code {response.status_code}"

    except Exception as e:
        return f"Error connecting to Karma: {str(e)}"


@mcp.tool()
async def create_silence(
    cluster: str,
    alertname: str,
    duration: str = "2h",
    comment: str = "Silenced via MCP",
    matchers: str = "",
) -> str:
    """Create a new silence for specific alerts

    Args:
        cluster: Target cluster name (e.g., 'teddy-prod')
        alertname: Name of the alert to silence
        duration: Duration of silence (e.g., '2h', '30m', '1d')
        comment: Comment explaining why the alert is being silenced
        matchers: Additional matchers in format 'key=value,key2=value2' (optional)

    Returns:
        Silence creation result with silence ID
    """
    try:
        # First, get the Alertmanager URL for this cluster
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{KARMA_URL}/alerts.json",
                json={},
                headers={"Content-Type": "application/json"},
                timeout=10.0,
            )

            if response.status_code != 200:
                return (
                    f"Error fetching cluster information: code {response.status_code}"
                )

            data = response.json()
            upstreams = data.get("upstreams", {}).get("instances", [])

            # Find the Alertmanager for this cluster
            alertmanager_url = None
            for upstream in upstreams:
                if cluster.lower() in upstream.get("cluster", "").lower():
                    # For now, we'll need to use the publicURI
                    # In production, you might need to handle authentication
                    alertmanager_url = upstream.get("publicURI")
                    break

            if not alertmanager_url:
                return f"Could not find Alertmanager for cluster: {cluster}"

            # Parse duration
            import re
            from datetime import datetime, timedelta

            # Parse duration string (e.g., '2h', '30m', '1d')
            duration_match = re.match(r"(\d+)([hdm])", duration.lower())
            if not duration_match:
                return "Invalid duration format. Use format like '2h', '30m', or '1d'"

            amount = int(duration_match.group(1))
            unit = duration_match.group(2)

            if unit == "h":
                delta = timedelta(hours=amount)
            elif unit == "m":
                delta = timedelta(minutes=amount)
            elif unit == "d":
                delta = timedelta(days=amount)
            else:
                return f"Unsupported time unit: {unit}"

            starts_at = datetime.utcnow()
            ends_at = starts_at + delta

            # Build matchers
            silence_matchers = [
                {
                    "name": "alertname",
                    "value": alertname,
                    "isRegex": False,
                    "isEqual": True,
                }
            ]

            # Add additional matchers if provided
            if matchers:
                for matcher_str in matchers.split(","):
                    if "=" in matcher_str:
                        key, value = matcher_str.split("=", 1)
                        silence_matchers.append(
                            {
                                "name": key.strip(),
                                "value": value.strip(),
                                "isRegex": False,
                                "isEqual": True,
                            }
                        )

            # Create silence request
            {
                "matchers": silence_matchers,
                "startsAt": starts_at.isoformat() + "Z",
                "endsAt": ends_at.isoformat() + "Z",
                "createdBy": "karma-mcp",
                "comment": comment,
            }

            # Note: Actually creating the silence requires direct Alertmanager API access
            # which may need authentication. This is a placeholder for the actual implementation
            return f"""
⚠️ Silence Creation Request Prepared:

📍 Cluster: {cluster}
🔕 Alert: {alertname}
⏱️ Duration: {duration} (until {ends_at.strftime("%Y-%m-%d %H:%M UTC")})
💬 Comment: {comment}
🏷️ Matchers: {len(silence_matchers)} configured

Note: Direct Alertmanager API integration is required to complete this action.
The Alertmanager endpoint would be: {alertmanager_url}/api/v2/silences

To manually create this silence, you can use the Karma UI or Alertmanager API directly.
"""

    except Exception as e:
        return f"Error creating silence: {str(e)}"


@mcp.tool()
async def delete_silence(silence_id: str, cluster: str) -> str:
    """Delete (expire) an existing silence

    Args:
        silence_id: ID of the silence to delete
        cluster: Cluster where the silence exists

    Returns:
        Deletion result
    """
    try:
        # First verify the silence exists
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{KARMA_URL}/alerts.json",
                json={},
                headers={"Content-Type": "application/json"},
                timeout=10.0,
            )

            if response.status_code != 200:
                return (
                    f"Error fetching silence information: code {response.status_code}"
                )

            data = response.json()
            silences = data.get("silences", {}).get(cluster, {})

            if silence_id not in silences:
                # Try to find with partial match
                found = False
                for sid in silences:
                    if silence_id in sid:
                        silence_id = sid
                        found = True
                        break

                if not found:
                    return f"Silence ID {silence_id} not found in cluster {cluster}"

            silence_info = silences.get(silence_id, {})

            return f"""
⚠️ Silence Deletion Request:

🔕 Silence ID: {silence_id}
📍 Cluster: {cluster}
💬 Original comment: {silence_info.get("comment", "N/A")}
👤 Created by: {silence_info.get("createdBy", "unknown")}

Note: Direct Alertmanager API integration is required to complete this deletion.
To manually delete this silence, use the Karma UI or Alertmanager API directly.
"""

    except Exception as e:
        return f"Error deleting silence: {str(e)}"


if __name__ == "__main__":
    logger.info(f"Starting MCP server for Karma at {KARMA_URL}")
    mcp.run()
