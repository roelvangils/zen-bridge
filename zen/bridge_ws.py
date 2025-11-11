#!/usr/bin/env python3
"""
WebSocket-based bridge server using aiohttp (more compatible).
"""

import asyncio
import json
import time
import uuid
from typing import Any

from pydantic import ValidationError

try:
    from aiohttp import web
except ImportError:
    print("Error: aiohttp library not installed")
    print("Install with: pip install aiohttp")
    exit(1)

from zen.domain.models import (
    ExecuteRequest,
    HealthResponse,
    Notification,
    NotificationsResponse,
    RunRequest,
    RunResponse,
    parse_incoming_message,
)
from zen.services.script_loader import ScriptLoader

HOST = "127.0.0.1"
PORT = 8765

# Store active WebSocket connections (browser clients)
active_connections: set = set()

# Track the most recently active connection
most_recent_connection = None

# Store browser info for each connection
browser_info: dict = {}

# Pending requests from CLI
pending_requests: dict[str, dict[str, Any]] = {}

# Completed requests
completed_requests: dict[str, dict[str, Any]] = {}

# Pending notifications (for control mode messages)
pending_notifications: list = []

# Cleanup old requests after 5 minutes
MAX_REQUEST_AGE = 300

# Script loader service (singleton)
script_loader = ScriptLoader()


def cleanup_old_requests():
    """Remove requests older than MAX_REQUEST_AGE seconds."""
    now = time.time()
    expired = [
        req_id
        for req_id, req in pending_requests.items()
        if now - req["timestamp"] > MAX_REQUEST_AGE
    ]
    for req_id in expired:
        del pending_requests[req_id]

    expired = [
        req_id
        for req_id, req in completed_requests.items()
        if now - req["timestamp"] > MAX_REQUEST_AGE
    ]
    for req_id in expired:
        del completed_requests[req_id]


async def websocket_handler(request):
    """Handle WebSocket connection from browser (userscript)."""
    global most_recent_connection
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    active_connections.add(ws)
    # Set this as the most recent connection
    most_recent_connection = ws
    print("Browser tab connected via WebSocket")
    print(f"Active connections: {len(active_connections)}")

    # Resend any pending requests to the newly connected browser
    # This handles the case where a page navigation disconnected mid-request
    if pending_requests:
        print(f"Resending {len(pending_requests)} pending request(s) to new connection")
        for request_id, req_data in list(pending_requests.items()):
            try:
                message = json.dumps(
                    {"type": "execute", "request_id": request_id, "code": req_data["code"]}
                )
                await ws.send_str(message)
                print(f"Resent pending request {request_id}")
            except Exception as e:
                print(f"Error resending request {request_id}: {e}")

    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)

                    # Validate incoming message with Pydantic
                    try:
                        validated_msg = parse_incoming_message(data)
                    except (ValidationError, ValueError) as e:
                        print(f"Invalid message from browser: {e}")
                        continue

                    message_type = validated_msg.type

                    # Mark this connection as most recent when it sends any message (except ping)
                    if message_type != "ping":
                        most_recent_connection = ws

                    if message_type == "result":
                        # Browser sending back result of executed code
                        # This connection is responding, so it's the active one
                        most_recent_connection = ws

                        request_id = data.get("request_id")
                        if request_id and request_id in pending_requests:
                            del pending_requests[request_id]
                            completed_requests[request_id] = {
                                "ok": data.get("ok", False),
                                "result": data.get("result"),
                                "error": data.get("error"),
                                "url": data.get("url"),
                                "title": data.get("title"),
                                "timestamp": time.time(),
                            }
                            print(f"Received result for request {request_id}")

                    elif message_type == "reinit_control":
                        # Browser requesting automatic reinitialization after page reload
                        config = data.get("config", {})
                        print("[Server] Auto-reinit requested from browser via WebSocket")

                        try:
                            # Use ScriptLoader service (async, cached)
                            placeholders = {
                                "ACTION_PLACEHOLDER": "start",
                                "KEY_DATA_PLACEHOLDER": "{}",
                                "CONFIG_PLACEHOLDER": json.dumps(config),
                            }
                            start_code = await script_loader.load_with_substitution_async(
                                "control.js", placeholders, use_cache=True
                            )

                            # Send back as an execute message
                            request_id = str(uuid.uuid4())
                            execute_msg = json.dumps(
                                {"type": "execute", "request_id": request_id, "code": start_code}
                            )
                            await ws.send_str(execute_msg)
                            print(f"[Server] Sent auto-reinit code (request {request_id[:8]})")

                        except FileNotFoundError:
                            print("[Server] ERROR: control.js not found")
                        except Exception as e:
                            print(f"[Server] Error in auto-reinit: {e}")

                    elif message_type == "refocus_notification":
                        # Browser sending refocus result notification
                        notification = {
                            "type": "refocus",
                            "success": data.get("success", False),
                            "message": data.get("message", ""),
                            "timestamp": time.time(),
                        }
                        pending_notifications.append(notification)
                        print(f"[Server] Refocus notification: {notification['message']}")

                    elif message_type == "ping":
                        # Browser keepalive
                        await ws.send_str(json.dumps({"type": "pong"}))

                    elif message_type == "browser_info":
                        # Store browser information
                        browser_info[ws] = {
                            "userAgent": data.get("userAgent", "Unknown"),
                            "browserName": data.get("browserName", "Unknown"),
                            "url": data.get("url", ""),
                            "title": data.get("title", "")
                        }
                        browser_name = data.get("browserName", "Unknown")
                        page_title = data.get("title", "")[:50]
                        print(f"Browser info received: {browser_name} - {page_title}")

                except json.JSONDecodeError:
                    print(f"Invalid JSON from browser: {msg.data}")
                except Exception as e:
                    print(f"Error handling browser message: {e}")

            elif msg.type == web.WSMsgType.ERROR:
                print(f"WebSocket connection closed with exception {ws.exception()}")

    finally:
        active_connections.discard(ws)
        browser_info.pop(ws, None)
        if most_recent_connection == ws:
            most_recent_connection = None
        print("Browser tab disconnected")
        print(f"Active connections: {len(active_connections)}")

    return ws


async def send_code_to_browser(code: str) -> str:
    """Send code to browser for execution. Returns request_id."""
    global most_recent_connection
    request_id = str(uuid.uuid4())
    pending_requests[request_id] = {"code": code, "timestamp": time.time()}

    # Send to most recent active browser only
    message = json.dumps({"type": "execute", "request_id": request_id, "code": code})

    # Use most recent connection if available, otherwise use any active connection
    target_ws = most_recent_connection if most_recent_connection in active_connections else None

    if not target_ws and active_connections:
        # Fallback to first available connection
        target_ws = next(iter(active_connections))
        most_recent_connection = target_ws

    if target_ws:
        try:
            await target_ws.send_str(message)
            # Get browser info if available
            info = browser_info.get(target_ws, {})
            browser_name = info.get("browserName", "Unknown browser")
            page_title = info.get("title", "")
            if page_title:
                print(f"[Server] Sent request {request_id[:8]} to {browser_name} - {page_title[:50]}")
            else:
                print(f"[Server] Sent request {request_id[:8]} to {browser_name}")
        except Exception as e:
            print(f"Error sending to browser: {e}")
            active_connections.discard(target_ws)
            browser_info.pop(target_ws, None)
            if most_recent_connection == target_ws:
                most_recent_connection = None
    else:
        print(f"[Server] WARNING: No browsers connected for request {request_id[:8]}")

    return request_id


async def handle_http_run(request):
    """HTTP endpoint: Submit code to run."""
    cleanup_old_requests()

    try:
        data = await request.json()
        code = data.get("code", "")

        if not code or not isinstance(code, str):
            return web.json_response({"ok": False, "error": "missing code"}, status=400)

        request_id = await send_code_to_browser(code)

        return web.json_response({"ok": True, "request_id": request_id})

    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)


async def handle_http_result(request):
    """HTTP endpoint: Get result of request."""
    request_id = request.query.get("request_id")

    if not request_id:
        return web.json_response({"ok": False, "error": "missing request_id"}, status=400)

    if request_id in completed_requests:
        return web.json_response(completed_requests[request_id])
    elif request_id in pending_requests:
        # Check if request is too old (>60 seconds) and no connections available
        req_age = time.time() - pending_requests[request_id]["timestamp"]
        if req_age > 60 and len(active_connections) == 0:
            # Request timed out with no browser connected
            del pending_requests[request_id]
            return web.json_response(
                {"ok": False, "error": "Request timeout: No browser connected"}
            )
        return web.json_response({"ok": False, "status": "pending"})
    else:
        return web.json_response({"ok": False, "error": "unknown request_id"}, status=404)


async def handle_http_reinit_control(request):
    """HTTP endpoint: Auto-reinitialize control mode after page reload."""
    try:
        data = await request.json()
        config = data.get("config", {})

        print("[Server] Auto-reinitialization requested from browser")

        # Use ScriptLoader service (async, cached)
        placeholders = {
            "ACTION_PLACEHOLDER": "start",
            "KEY_DATA_PLACEHOLDER": "{}",
            "CONFIG_PLACEHOLDER": json.dumps(config),
        }
        start_code = await script_loader.load_with_substitution_async(
            "control.js", placeholders, use_cache=True
        )

        # Send to browser via WebSocket
        request_id = await send_code_to_browser(start_code)

        print(f"[Server] Sent auto-reinit request {request_id[:8]}")

        return web.json_response({"ok": True, "request_id": request_id})

    except FileNotFoundError:
        return web.json_response({"ok": False, "error": "control.js not found"}, status=500)
    except Exception as e:
        print(f"[Server] Error in auto-reinit: {e}")
        return web.json_response({"ok": False, "error": str(e)}, status=500)


async def handle_http_notifications(request):
    """HTTP endpoint: Get pending notifications."""
    global pending_notifications

    # Get all pending notifications
    notifications = pending_notifications.copy()
    # Clear the list
    pending_notifications = []

    return web.json_response({"ok": True, "notifications": notifications})


async def handle_http_health(request):
    """HTTP endpoint: Health check."""
    cleanup_old_requests()
    return web.json_response(
        {
            "ok": True,
            "timestamp": time.time(),
            "connected_browsers": len(active_connections),
            "pending": len(pending_requests),
            "completed": len(completed_requests),
        }
    )


async def main():
    """Start HTTP and WebSocket server."""
    print("Zen Bridge WebSocket Server (aiohttp)")
    print(f"WebSocket: ws://{HOST}:{PORT + 1}/ws")
    print(f"HTTP API: http://{HOST}:{PORT}")
    print("")

    # Preload control.js into cache (async, no blocking!)
    try:
        await script_loader.preload_script_async("control.js")
        cached_scripts = script_loader.get_cached_scripts()
        print(f"✓ Preloaded {len(cached_scripts)} script(s): {', '.join(cached_scripts)}")
    except FileNotFoundError as e:
        print(f"✗ WARNING: {e}")
        print("  Auto-refocus will not work until file is available")
    print("")

    # Setup aiohttp app
    app = web.Application()

    # HTTP endpoints for CLI
    app.router.add_post("/run", handle_http_run)
    app.router.add_get("/result", handle_http_result)
    app.router.add_get("/notifications", handle_http_notifications)
    app.router.add_get("/health", handle_http_health)
    app.router.add_post("/reinit-control", handle_http_reinit_control)

    # WebSocket endpoint for browser
    app.router.add_get("/ws", websocket_handler)

    # Start server
    runner = web.AppRunner(app)
    await runner.setup()

    # HTTP server
    http_site = web.TCPSite(runner, HOST, PORT)
    await http_site.start()
    print(f"HTTP server running on http://{HOST}:{PORT}")

    # WebSocket server (same port, different path)
    ws_site = web.TCPSite(runner, HOST, PORT + 1)
    await ws_site.start()
    print(f"WebSocket server running on ws://{HOST}:{PORT + 1}/ws")
    print("Ready for connections!")

    # Keep running
    await asyncio.Event().wait()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer stopped")
