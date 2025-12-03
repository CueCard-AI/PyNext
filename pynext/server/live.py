"""
PyNext Live Query - Server Routes.

HTTP and WebSocket endpoints for live query subscriptions.

Routes:
- GET  /_pynext/live/sse      - SSE endpoint for subscriptions
- WS   /_pynext/live/ws       - WebSocket endpoint for subscriptions
- POST /_pynext/live/subscribe - Subscribe to a query
- POST /_pynext/live/unsubscribe - Unsubscribe from a query
- POST /_pynext/live/refresh  - Force refresh a query

Usage with FastAPI:
    from pynext.server.live import create_live_router
    
    app.include_router(create_live_router())

Usage with Starlette:
    from pynext.server.live import create_live_routes
    
    routes = create_live_routes()
    app = Starlette(routes=routes)
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from pynext.db.live.config import (
    LiveQueryConfig,
    QuerySignature,
    get_server_config,
)
from pynext.db.live.subscriptions import get_subscription_manager
from pynext.db.live.transport import get_transport_manager
from pynext.db.live.transport.base import TransportMessage, MessageType
from pynext.db.live.transport.sse import SSETransport, create_sse_response
from pynext.db.live.transport.websocket import WebSocketTransport

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


# =============================================================================
# Request Handlers
# =============================================================================

async def handle_sse(request: Any) -> Any:
    """
    Handle SSE connection for live queries.
    
    GET /_pynext/live/sse
    
    The client connects and receives updates via Server-Sent Events.
    """
    try:
        from starlette.responses import StreamingResponse
    except ImportError:
        raise RuntimeError("starlette required for SSE")
    
    # Generate client ID
    client_id = str(uuid.uuid4())
    
    # Get query parameters
    queries = request.query_params.getlist("query")
    
    logger.info(f"SSE connection: {client_id} with {len(queries)} queries")
    
    # Create SSE transport
    transport_manager = get_transport_manager()
    await transport_manager.connect(
        client_id=client_id,
        transport_type="sse",
    )
    
    # Subscribe to requested queries
    subscription_manager = get_subscription_manager()
    for query_json in queries:
        try:
            query_data = json.loads(query_json)
            await _subscribe_query(client_id, query_data)
        except json.JSONDecodeError:
            logger.warning(f"Invalid query JSON: {query_json}")
    
    # Create streaming response
    async def event_generator():
        yield ": connected\n\n"
        
        try:
            while True:
                # Wait for messages or timeout for heartbeat
                await asyncio.sleep(30)
                yield ": heartbeat\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            await transport_manager.disconnect(client_id)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


async def handle_websocket(websocket: Any) -> None:
    """
    Handle WebSocket connection for live queries.
    
    WS /_pynext/live/ws
    
    Bidirectional communication for live query subscriptions.
    """
    await websocket.accept()
    
    # Generate client ID
    client_id = str(uuid.uuid4())
    
    logger.info(f"WebSocket connection: {client_id}")
    
    # Create WebSocket transport
    transport_manager = get_transport_manager()
    await transport_manager.connect(
        client_id=client_id,
        transport_type="websocket",
        connection=websocket,
    )
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                await _handle_ws_message(client_id, message, websocket)
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "data": {"error": "Invalid JSON"},
                }))
                
    except Exception as e:
        if "disconnect" not in str(e).lower():
            logger.warning(f"WebSocket error: {e}")
    finally:
        await transport_manager.disconnect(client_id)
        logger.info(f"WebSocket disconnected: {client_id}")


async def _handle_ws_message(
    client_id: str,
    message: Dict[str, Any],
    websocket: Any,
) -> None:
    """Handle a WebSocket message."""
    msg_type = message.get("type")
    query_id = message.get("query_id")
    data = message.get("data", {})
    
    if msg_type == "subscribe":
        await _subscribe_query(client_id, {
            "id": query_id,
            **data,
        })
        await websocket.send_text(json.dumps({
            "type": "subscribed",
            "query_id": query_id,
        }))
        
    elif msg_type == "unsubscribe":
        await _unsubscribe_query(query_id)
        await websocket.send_text(json.dumps({
            "type": "unsubscribed",
            "query_id": query_id,
        }))
        
    elif msg_type == "refresh":
        await _refresh_query(query_id, websocket)
        
    elif msg_type == "ping":
        await websocket.send_text(json.dumps({"type": "pong"}))


async def _subscribe_query(client_id: str, query_data: Dict[str, Any]) -> str:
    """Subscribe to a query."""
    subscription_manager = get_subscription_manager()
    transport_manager = get_transport_manager()
    
    query_id = query_data.get("id", str(uuid.uuid4()))
    table = query_data.get("table")
    
    if not table:
        raise ValueError("Table name required")
    
    # Build query signature
    where_clauses = query_data.get("where", [])
    if isinstance(where_clauses, dict):
        where_clauses = [where_clauses]
    
    signature = QuerySignature(
        table=table,
        where_clauses=tuple(tuple(sorted(c.items())) for c in where_clauses),
        order_by=query_data.get("orderBy"),
        limit=query_data.get("limit"),
        offset=query_data.get("offset"),
    )
    
    # Create callback that sends to transport
    async def on_change(event):
        message = TransportMessage.data_message(query_id, event)
        await transport_manager.send(client_id, message)
    
    # Subscribe
    sub_id = await subscription_manager.subscribe(
        query_signature=signature,
        callback=lambda e: asyncio.create_task(on_change(e)),
        client_id=client_id,
    )
    
    # Track subscription
    transport_manager.subscribe_query(client_id, query_id)
    
    logger.debug(f"Subscribed {client_id} to {table} (query: {query_id})")
    
    return sub_id


async def _unsubscribe_query(query_id: str) -> None:
    """Unsubscribe from a query."""
    subscription_manager = get_subscription_manager()
    await subscription_manager.unsubscribe(query_id)


async def _refresh_query(query_id: str, websocket: Any) -> None:
    """Force refresh a query and send results."""
    # TODO: Implement refresh
    await websocket.send_text(json.dumps({
        "type": "sync",
        "query_id": query_id,
        "data": {"rows": []},
    }))


async def handle_subscribe(request: Any) -> Any:
    """
    Subscribe to a query via POST.
    
    POST /_pynext/live/subscribe
    
    Body: { table, where, orderBy, limit }
    Returns: { query_id }
    """
    try:
        from starlette.responses import JSONResponse
    except ImportError:
        raise RuntimeError("starlette required")
    
    data = await request.json()
    
    # Get client ID from header or generate
    client_id = request.headers.get("X-PyNext-Client-ID", str(uuid.uuid4()))
    
    try:
        await _subscribe_query(client_id, data)
        return JSONResponse({"query_id": data.get("id"), "status": "subscribed"})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)


async def handle_unsubscribe(request: Any) -> Any:
    """
    Unsubscribe from a query via POST.
    
    POST /_pynext/live/unsubscribe
    
    Body: { query_id }
    """
    try:
        from starlette.responses import JSONResponse
    except ImportError:
        raise RuntimeError("starlette required")
    
    data = await request.json()
    query_id = data.get("query_id")
    
    if not query_id:
        return JSONResponse({"error": "query_id required"}, status_code=400)
    
    await _unsubscribe_query(query_id)
    return JSONResponse({"status": "unsubscribed"})


async def handle_refresh(request: Any) -> Any:
    """
    Force refresh a query.
    
    POST /_pynext/live/refresh?query_id=xxx
    """
    try:
        from starlette.responses import JSONResponse
    except ImportError:
        raise RuntimeError("starlette required")
    
    query_id = request.query_params.get("query_id")
    
    if not query_id:
        return JSONResponse({"error": "query_id required"}, status_code=400)
    
    # TODO: Implement refresh logic
    return JSONResponse({"status": "refreshing"})


async def handle_stats(request: Any) -> Any:
    """
    Get live query statistics.
    
    GET /_pynext/live/stats
    """
    try:
        from starlette.responses import JSONResponse
    except ImportError:
        raise RuntimeError("starlette required")
    
    subscription_manager = get_subscription_manager()
    transport_manager = get_transport_manager()
    
    return JSONResponse({
        "subscriptions": subscription_manager.get_stats(),
        "transports": {
            "clients": transport_manager.client_count,
            "subscriptions": transport_manager.subscription_count,
        },
    })


# =============================================================================
# Router Creation
# =============================================================================

def create_live_routes():
    """
    Create Starlette routes for live queries.
    
    Usage:
        from starlette.applications import Starlette
        from pynext.server.live import create_live_routes
        
        app = Starlette(routes=create_live_routes())
    """
    try:
        from starlette.routing import Route, WebSocketRoute
    except ImportError:
        raise RuntimeError("starlette required for live query routes")
    
    config = get_server_config()
    
    return [
        Route(config.sse_path, handle_sse, methods=["GET"]),
        WebSocketRoute(config.ws_path, handle_websocket),
        Route("/_pynext/live/subscribe", handle_subscribe, methods=["POST"]),
        Route("/_pynext/live/unsubscribe", handle_unsubscribe, methods=["POST"]),
        Route("/_pynext/live/refresh", handle_refresh, methods=["POST"]),
        Route("/_pynext/live/stats", handle_stats, methods=["GET"]),
    ]


def create_live_router():
    """
    Create FastAPI router for live queries.
    
    Usage:
        from fastapi import FastAPI
        from pynext.server.live import create_live_router
        
        app = FastAPI()
        app.include_router(create_live_router())
    """
    try:
        from fastapi import APIRouter, WebSocket, Request
        from fastapi.responses import StreamingResponse, JSONResponse
    except ImportError:
        raise RuntimeError("fastapi required for live query router")
    
    router = APIRouter(prefix="/_pynext/live", tags=["live"])
    config = get_server_config()
    
    @router.get("/sse")
    async def sse_endpoint(request: Request):
        return await handle_sse(request)
    
    @router.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        await handle_websocket(websocket)
    
    @router.post("/subscribe")
    async def subscribe_endpoint(request: Request):
        return await handle_subscribe(request)
    
    @router.post("/unsubscribe")
    async def unsubscribe_endpoint(request: Request):
        return await handle_unsubscribe(request)
    
    @router.post("/refresh")
    async def refresh_endpoint(request: Request):
        return await handle_refresh(request)
    
    @router.get("/stats")
    async def stats_endpoint(request: Request):
        return await handle_stats(request)
    
    return router

