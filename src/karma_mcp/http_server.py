#!/usr/bin/env python3
"""
HTTP server wrapper for Karma MCP tools
Exposes MCP tools as REST endpoints and SSE for ingress access
"""

import asyncio
import json
import logging
import os
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# Import MCP tools
from .server import (
    check_karma,
    create_silence,
    delete_silence,
    get_alert_details,
    get_alert_details_multi_cluster,
    get_alerts_by_state,
    get_alerts_summary,
    list_active_alerts,
    list_alerts,
    list_alerts_by_cluster,
    list_clusters,
    list_silences,
    list_suppressed_alerts,
    search_alerts_by_container,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Karma MCP HTTP Server",
    description="HTTP wrapper for Karma MCP tools with SSE support",
    version="0.4.0",
)

# Add CORS middleware for browser access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class ClusterRequest(BaseModel):
    cluster_name: str


class AlertDetailsRequest(BaseModel):
    alert_name: str


class ContainerSearchRequest(BaseModel):
    container_name: str
    cluster_filter: str | None = ""


class AlertSearchRequest(BaseModel):
    alert_name: str
    cluster_filter: str | None = ""


class SilenceRequest(BaseModel):
    cluster: str
    alertname: str
    duration: str = "2h"
    comment: str = "Silenced via API"
    matchers: str = ""


class DeleteSilenceRequest(BaseModel):
    silence_id: str
    cluster: str


class MCPResponse(BaseModel):
    success: bool
    data: str
    error: str | None = None


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "Karma MCP HTTP Server",
        "version": "0.1.0",
        "endpoints": [
            "GET /health - Check Karma connectivity",
            "GET /alerts - List all alerts",
            "GET /alerts/summary - Get alerts summary",
            "GET /clusters - List all clusters",
            "POST /alerts/by-cluster - Get alerts by cluster",
            "POST /alerts/details - Get alert details",
            "POST /alerts/search/container - Search alerts by container name",
            "POST /alerts/search/name - Search alerts by name across clusters",
            "GET /silences - List all active silences",
            "POST /silences - Create a new silence",
            "DELETE /silences - Delete an existing silence",
        ],
    }


@app.get("/health")
async def health_check():
    """Health check endpoint that also checks Karma connectivity"""
    try:
        result = await check_karma()
        if "✓" in result:
            return {"status": "healthy", "karma": "connected", "message": result}
        else:
            return {"status": "degraded", "karma": "issues", "message": result}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=503, detail=f"Health check failed: {str(e)}"
        ) from e


@app.get("/alerts", response_model=MCPResponse)
async def get_alerts():
    """List all alerts"""
    try:
        result = await list_alerts()
        return MCPResponse(success=True, data=result)
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        return MCPResponse(success=False, data="", error=str(e))


@app.get("/alerts/summary", response_model=MCPResponse)
async def get_summary():
    """Get alerts summary"""
    try:
        result = await get_alerts_summary()
        return MCPResponse(success=True, data=result)
    except Exception as e:
        logger.error(f"Error getting summary: {e}")
        return MCPResponse(success=False, data="", error=str(e))


@app.get("/clusters", response_model=MCPResponse)
async def get_clusters():
    """List all clusters"""
    try:
        result = await list_clusters()
        return MCPResponse(success=True, data=result)
    except Exception as e:
        logger.error(f"Error getting clusters: {e}")
        return MCPResponse(success=False, data="", error=str(e))


@app.post("/alerts/by-cluster", response_model=MCPResponse)
async def get_alerts_by_cluster(request: ClusterRequest):
    """Get alerts filtered by cluster"""
    try:
        result = await list_alerts_by_cluster(request.cluster_name)
        return MCPResponse(success=True, data=result)
    except Exception as e:
        logger.error(f"Error getting alerts by cluster: {e}")
        return MCPResponse(success=False, data="", error=str(e))


@app.post("/alerts/details", response_model=MCPResponse)
async def get_details(request: AlertDetailsRequest):
    """Get detailed information about a specific alert"""
    try:
        result = await get_alert_details(request.alert_name)
        return MCPResponse(success=True, data=result)
    except Exception as e:
        logger.error(f"Error getting alert details: {e}")
        return MCPResponse(success=False, data="", error=str(e))


@app.post("/alerts/search/container", response_model=MCPResponse)
async def search_container_alerts(request: ContainerSearchRequest):
    """Search for alerts by container name across multiple clusters"""
    try:
        result = await search_alerts_by_container(
            request.container_name, request.cluster_filter
        )
        return MCPResponse(success=True, data=result)
    except Exception as e:
        logger.error(f"Error searching container alerts: {e}")
        return MCPResponse(success=False, data="", error=str(e))


@app.post("/alerts/search/name", response_model=MCPResponse)
async def search_alert_by_name(request: AlertSearchRequest):
    """Search for a specific alert by name across multiple clusters"""
    try:
        result = await get_alert_details_multi_cluster(
            request.alert_name, request.cluster_filter
        )
        return MCPResponse(success=True, data=result)
    except Exception as e:
        logger.error(f"Error searching alert by name: {e}")
        return MCPResponse(success=False, data="", error=str(e))


@app.get("/silences", response_model=MCPResponse)
async def get_silences(cluster: str = ""):
    """List all active silences, optionally filtered by cluster"""
    try:
        result = await list_silences(cluster)
        return MCPResponse(success=True, data=result)
    except Exception as e:
        logger.error(f"Error listing silences: {e}")
        return MCPResponse(success=False, data="", error=str(e))


@app.post("/silences", response_model=MCPResponse)
async def create_silence_endpoint(request: SilenceRequest):
    """Create a new silence for specific alerts"""
    try:
        result = await create_silence(
            cluster=request.cluster,
            alertname=request.alertname,
            duration=request.duration,
            comment=request.comment,
            matchers=request.matchers,
        )
        return MCPResponse(success=True, data=result)
    except Exception as e:
        logger.error(f"Error creating silence: {e}")
        return MCPResponse(success=False, data="", error=str(e))


@app.delete("/silences", response_model=MCPResponse)
async def delete_silence_endpoint(request: DeleteSilenceRequest):
    """Delete (expire) an existing silence"""
    try:
        result = await delete_silence(
            silence_id=request.silence_id, cluster=request.cluster
        )
        return MCPResponse(success=True, data=result)
    except Exception as e:
        logger.error(f"Error deleting silence: {e}")
        return MCPResponse(success=False, data="", error=str(e))


# MCP compatibility endpoint for Claude integration
@app.post("/mcp/tools/{tool_name}")
async def mcp_tool_endpoint(tool_name: str, params: dict[str, Any] = None):
    """Generic MCP tool endpoint for Claude integration"""
    if params is None:
        params = {}

    try:
        if tool_name == "check_karma":
            result = await check_karma()
        elif tool_name == "list_alerts":
            result = await list_alerts()
        elif tool_name == "get_alerts_summary":
            result = await get_alerts_summary()
        elif tool_name == "list_clusters":
            result = await list_clusters()
        elif tool_name == "list_alerts_by_cluster":
            cluster_name = params.get("cluster_name")
            if not cluster_name:
                raise ValueError("cluster_name parameter required")
            result = await list_alerts_by_cluster(cluster_name)
        elif tool_name == "get_alert_details":
            alert_name = params.get("alert_name")
            if not alert_name:
                raise ValueError("alert_name parameter required")
            result = await get_alert_details(alert_name)
        elif tool_name == "list_active_alerts":
            result = await list_active_alerts()
        elif tool_name == "list_suppressed_alerts":
            result = await list_suppressed_alerts()
        elif tool_name == "get_alerts_by_state":
            state = params.get("state")
            if not state:
                raise ValueError("state parameter required")
            result = await get_alerts_by_state(state)
        elif tool_name == "search_alerts_by_container":
            container_name = params.get("container_name")
            if not container_name:
                raise ValueError("container_name parameter required")
            cluster_filter = params.get("cluster_filter", "")
            result = await search_alerts_by_container(container_name, cluster_filter)
        elif tool_name == "get_alert_details_multi_cluster":
            alert_name = params.get("alert_name")
            if not alert_name:
                raise ValueError("alert_name parameter required")
            cluster_filter = params.get("cluster_filter", "")
            result = await get_alert_details_multi_cluster(alert_name, cluster_filter)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Error executing tool {tool_name}: {e}")
        raise HTTPException(status_code=400, detail=str(e)) from e


# MCP protocol endpoint for proper JSON-RPC communication
@app.post("/mcp/sse")
async def mcp_jsonrpc_endpoint(request: Request):
    """MCP JSON-RPC endpoint for Claude Code integration"""
    try:
        data = await request.json()

        # Handle MCP initialize request
        if data.get("method") == "initialize":
            response = {
                "jsonrpc": "2.0",
                "id": data.get("id"),
                "result": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "karma-mcp", "version": "0.4.0"},
                },
            }
            return response

        # Handle tools/list request
        elif data.get("method") == "tools/list":
            tools = [
                {
                    "name": "check_karma",
                    "description": "Check connection to Karma server",
                    "inputSchema": {"type": "object", "properties": {}, "required": []},
                },
                {
                    "name": "list_alerts",
                    "description": "List all active alerts",
                    "inputSchema": {"type": "object", "properties": {}, "required": []},
                },
                {
                    "name": "get_alerts_summary",
                    "description": "Get alert statistics",
                    "inputSchema": {"type": "object", "properties": {}, "required": []},
                },
                {
                    "name": "list_clusters",
                    "description": "List all clusters",
                    "inputSchema": {"type": "object", "properties": {}, "required": []},
                },
                {
                    "name": "list_alerts_by_cluster",
                    "description": "Filter alerts by cluster",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "cluster_name": {
                                "type": "string",
                                "description": "Name of the cluster to filter by",
                            }
                        },
                        "required": ["cluster_name"],
                    },
                },
                {
                    "name": "get_alert_details",
                    "description": "Get specific alert details",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "alert_name": {
                                "type": "string",
                                "description": "Name of the alert to get details for",
                            }
                        },
                        "required": ["alert_name"],
                    },
                },
                {
                    "name": "list_active_alerts",
                    "description": "List only active (non-suppressed) alerts",
                    "inputSchema": {"type": "object", "properties": {}, "required": []},
                },
                {
                    "name": "list_suppressed_alerts",
                    "description": "List only suppressed alerts",
                    "inputSchema": {"type": "object", "properties": {}, "required": []},
                },
                {
                    "name": "get_alerts_by_state",
                    "description": "Get alerts filtered by state (active, suppressed, or all)",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "state": {
                                "type": "string",
                                "description": "Alert state to filter by",
                                "enum": ["active", "suppressed", "all"],
                            }
                        },
                        "required": ["state"],
                    },
                },
                {
                    "name": "search_alerts_by_container",
                    "description": "Search for alerts by container name across multiple clusters",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "container_name": {
                                "type": "string",
                                "description": "Name of the container to search for",
                            },
                            "cluster_filter": {
                                "type": "string",
                                "description": "Optional cluster name filter. If empty, searches all clusters.",
                                "default": "",
                            },
                        },
                        "required": ["container_name"],
                    },
                },
                {
                    "name": "get_alert_details_multi_cluster",
                    "description": "Get detailed information about a specific alert across multiple clusters",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "alert_name": {
                                "type": "string",
                                "description": "Name of the alert to search for (e.g., 'KubePodCrashLooping')",
                            },
                            "cluster_filter": {
                                "type": "string",
                                "description": "Optional cluster name filter. If empty, searches all clusters.",
                                "default": "",
                            },
                        },
                        "required": ["alert_name"],
                    },
                },
            ]
            response = {
                "jsonrpc": "2.0",
                "id": data.get("id"),
                "result": {"tools": tools},
            }
            return response

        # Handle tools/call request
        elif data.get("method") == "tools/call":
            tool_name = data.get("params", {}).get("name")
            arguments = data.get("params", {}).get("arguments", {})

            try:
                # Execute the tool
                if tool_name == "check_karma":
                    result = await check_karma()
                elif tool_name == "list_alerts":
                    result = await list_alerts()
                elif tool_name == "get_alerts_summary":
                    result = await get_alerts_summary()
                elif tool_name == "list_clusters":
                    result = await list_clusters()
                elif tool_name == "list_alerts_by_cluster":
                    cluster_name = arguments.get("cluster_name")
                    if not cluster_name:
                        raise ValueError("cluster_name parameter required")
                    result = await list_alerts_by_cluster(cluster_name)
                elif tool_name == "get_alert_details":
                    alert_name = arguments.get("alert_name")
                    if not alert_name:
                        raise ValueError("alert_name parameter required")
                    result = await get_alert_details(alert_name)
                elif tool_name == "list_active_alerts":
                    result = await list_active_alerts()
                elif tool_name == "list_suppressed_alerts":
                    result = await list_suppressed_alerts()
                elif tool_name == "get_alerts_by_state":
                    state = arguments.get("state")
                    if not state:
                        raise ValueError("state parameter required")
                    result = await get_alerts_by_state(state)
                elif tool_name == "search_alerts_by_container":
                    container_name = arguments.get("container_name")
                    if not container_name:
                        raise ValueError("container_name parameter required")
                    cluster_filter = arguments.get("cluster_filter", "")
                    result = await search_alerts_by_container(
                        container_name, cluster_filter
                    )
                elif tool_name == "get_alert_details_multi_cluster":
                    alert_name = arguments.get("alert_name")
                    if not alert_name:
                        raise ValueError("alert_name parameter required")
                    cluster_filter = arguments.get("cluster_filter", "")
                    result = await get_alert_details_multi_cluster(
                        alert_name, cluster_filter
                    )
                else:
                    raise ValueError(f"Unknown tool: {tool_name}")

                response = {
                    "jsonrpc": "2.0",
                    "id": data.get("id"),
                    "result": {"content": [{"type": "text", "text": result}]},
                }
                return response

            except Exception as e:
                response = {
                    "jsonrpc": "2.0",
                    "id": data.get("id"),
                    "error": {"code": -32000, "message": str(e)},
                }
                return response

        # Handle notifications/initialized (Claude Code bug workaround)
        elif data.get("method") == "notifications/initialized":
            # Just acknowledge, no response needed for notifications
            return None

        # Unknown method
        else:
            response = {
                "jsonrpc": "2.0",
                "id": data.get("id"),
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {data.get('method')}",
                },
            }
            return response

    except Exception as e:
        logger.error(f"MCP protocol error: {e}")
        response = {
            "jsonrpc": "2.0",
            "id": data.get("id", None) if "data" in locals() else None,
            "error": {"code": -32603, "message": f"Internal error: {str(e)}"},
        }
        return response


# Keep SSE endpoint for testing
@app.get("/mcp/sse")
async def mcp_sse_stream(request: Request):
    """Server-Sent Events endpoint for testing"""

    async def event_stream():
        try:
            # Send initial connection event
            yield f"data: {json.dumps({'type': 'connection', 'status': 'connected', 'server': 'karma-mcp', 'version': '0.3.2'})}\n\n"

            # Send available tools list
            tools = [
                {
                    "name": "check_karma",
                    "description": "Check connection to Karma server",
                },
                {"name": "list_alerts", "description": "List all active alerts"},
                {"name": "get_alerts_summary", "description": "Get alert statistics"},
                {
                    "name": "get_alert_details",
                    "description": "Get specific alert details",
                },
                {"name": "list_clusters", "description": "List all clusters"},
                {
                    "name": "list_alerts_by_cluster",
                    "description": "Filter alerts by cluster",
                },
            ]
            yield f"data: {json.dumps({'type': 'tools', 'tools': tools})}\n\n"

            # Keep connection alive and listen for client disconnect
            while True:
                # Check if client disconnected
                if await request.is_disconnected():
                    break

                # Send periodic heartbeat
                yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': asyncio.get_event_loop().time()})}\n\n"
                await asyncio.sleep(30)

        except asyncio.CancelledError:
            logger.info("SSE connection cancelled")
        except Exception as e:
            logger.error(f"SSE stream error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


# WebSocket-like endpoint for tool execution via SSE
@app.post("/mcp/execute")
async def execute_tool_sse(request: Request):
    """Execute MCP tool and return result via SSE-compatible response"""
    try:
        data = await request.json()
        tool_name = data.get("tool")
        params = data.get("params", {})

        if not tool_name:
            raise HTTPException(status_code=400, detail="Tool name required")

        # Execute the tool
        if tool_name == "check_karma":
            result = await check_karma()
        elif tool_name == "list_alerts":
            result = await list_alerts()
        elif tool_name == "get_alerts_summary":
            result = await get_alerts_summary()
        elif tool_name == "list_clusters":
            result = await list_clusters()
        elif tool_name == "list_alerts_by_cluster":
            cluster_name = params.get("cluster_name")
            if not cluster_name:
                raise HTTPException(
                    status_code=400, detail="cluster_name parameter required"
                )
            result = await list_alerts_by_cluster(cluster_name)
        elif tool_name == "get_alert_details":
            alert_name = params.get("alert_name")
            if not alert_name:
                raise HTTPException(
                    status_code=400, detail="alert_name parameter required"
                )
            result = await get_alert_details(alert_name)
        elif tool_name == "list_active_alerts":
            result = await list_active_alerts()
        elif tool_name == "list_suppressed_alerts":
            result = await list_suppressed_alerts()
        elif tool_name == "get_alerts_by_state":
            state = params.get("state")
            if not state:
                raise HTTPException(status_code=400, detail="state parameter required")
            result = await get_alerts_by_state(state)
        elif tool_name == "search_alerts_by_container":
            container_name = params.get("container_name")
            if not container_name:
                raise HTTPException(
                    status_code=400, detail="container_name parameter required"
                )
            cluster_filter = params.get("cluster_filter", "")
            result = await search_alerts_by_container(container_name, cluster_filter)
        elif tool_name == "get_alert_details_multi_cluster":
            alert_name = params.get("alert_name")
            if not alert_name:
                raise HTTPException(
                    status_code=400, detail="alert_name parameter required"
                )
            cluster_filter = params.get("cluster_filter", "")
            result = await get_alert_details_multi_cluster(alert_name, cluster_filter)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown tool: {tool_name}")

        return {
            "type": "tool_result",
            "tool": tool_name,
            "success": True,
            "result": result,
            "timestamp": asyncio.get_event_loop().time(),
        }

    except HTTPException:
        # Re-raise HTTP exceptions to let FastAPI handle them
        raise
    except Exception as e:
        logger.error(f"Tool execution error: {e}")
        return {
            "type": "tool_result",
            "tool": tool_name if "tool_name" in locals() else "unknown",
            "success": False,
            "error": str(e),
            "timestamp": asyncio.get_event_loop().time(),
        }


def run_server():
    """Run the HTTP server"""
    port = int(os.getenv("PORT", "8080"))
    host = os.getenv("HOST", "0.0.0.0")

    logger.info(f"Starting Karma MCP HTTP server on {host}:{port}")
    logger.info(f"Karma URL: {os.getenv('KARMA_URL', 'http://localhost:8080')}")
    logger.info("SSE endpoint available at /mcp/sse")
    logger.info("Tool execution endpoint at /mcp/execute")

    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    run_server()
