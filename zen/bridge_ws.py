#!/usr/bin/env python3
"""
WebSocket-based bridge server for faster communication.
"""
import asyncio
import json
import time
import uuid
from pathlib import Path
from typing import Dict, Set, Any

try:
    import websockets
    from websockets.server import WebSocketServerProtocol
except ImportError:
    print("Error: websockets library not installed")
    print("Install with: pip install websockets")
    exit(1)

HOST = "127.0.0.1"
PORT = 8765

# Store active WebSocket connections (browser clients)
active_connections: Set[WebSocketServerProtocol] = set()

# Pending requests from CLI
pending_requests: Dict[str, Dict[str, Any]] = {}

# Completed requests
completed_requests: Dict[str, Dict[str, Any]] = {}

# Cleanup old requests after 5 minutes
MAX_REQUEST_AGE = 300


def cleanup_old_requests():
    """Remove requests older than MAX_REQUEST_AGE seconds."""
    now = time.time()
    expired = [
        req_id for req_id, req in pending_requests.items()
        if now - req['timestamp'] > MAX_REQUEST_AGE
    ]
    for req_id in expired:
        del pending_requests[req_id]

    expired = [
        req_id for req_id, req in completed_requests.items()
        if now - req['timestamp'] > MAX_REQUEST_AGE
    ]
    for req_id in expired:
        del completed_requests[req_id]


async def handle_browser_connection(websocket: WebSocketServerProtocol):
    """Handle WebSocket connection from browser (userscript)."""
    active_connections.add(websocket)
    print(f"Browser connected: {websocket.remote_address}")

    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                message_type = data.get('type')

                if message_type == 'result':
                    # Browser sending back result of executed code
                    request_id = data.get('request_id')
                    if request_id and request_id in pending_requests:
                        del pending_requests[request_id]
                        completed_requests[request_id] = {
                            'ok': data.get('ok', False),
                            'result': data.get('result'),
                            'error': data.get('error'),
                            'url': data.get('url'),
                            'title': data.get('title'),
                            'timestamp': time.time()
                        }
                        print(f"Received result for request {request_id}")

                elif message_type == 'ping':
                    # Browser keepalive
                    await websocket.send(json.dumps({'type': 'pong'}))

            except json.JSONDecodeError:
                print(f"Invalid JSON from browser: {message}")
            except Exception as e:
                print(f"Error handling browser message: {e}")

    except websockets.exceptions.ConnectionClosed:
        print(f"Browser disconnected: {websocket.remote_address}")
    finally:
        active_connections.discard(websocket)


async def send_code_to_browser(code: str) -> str:
    """Send code to browser for execution. Returns request_id."""
    request_id = str(uuid.uuid4())
    pending_requests[request_id] = {
        'code': code,
        'timestamp': time.time()
    }

    # Send to all connected browsers
    message = json.dumps({
        'type': 'execute',
        'request_id': request_id,
        'code': code
    })

    if active_connections:
        await asyncio.gather(
            *[ws.send(message) for ws in active_connections],
            return_exceptions=True
        )
        print(f"Sent code to {len(active_connections)} browser(s)")
    else:
        print("Warning: No browsers connected")

    return request_id


async def get_result(request_id: str, timeout: float = 10.0) -> Dict[str, Any]:
    """Wait for result from browser."""
    start_time = time.time()

    while time.time() - start_time < timeout:
        if request_id in completed_requests:
            return completed_requests[request_id]

        await asyncio.sleep(0.1)

    # Timeout
    return {
        'ok': False,
        'error': f'Timeout: No response from browser after {timeout} seconds'
    }


# HTTP endpoint for CLI communication (backward compatible)
from aiohttp import web


async def handle_http_run(request):
    """HTTP endpoint: Submit code to run."""
    cleanup_old_requests()

    try:
        data = await request.json()
        code = data.get('code', '')

        if not code or not isinstance(code, str):
            return web.json_response(
                {'ok': False, 'error': 'missing code'},
                status=400
            )

        request_id = await send_code_to_browser(code)

        return web.json_response({
            'ok': True,
            'request_id': request_id
        })

    except Exception as e:
        return web.json_response(
            {'ok': False, 'error': str(e)},
            status=500
        )


async def handle_http_result(request):
    """HTTP endpoint: Get result of request."""
    request_id = request.query.get('request_id')

    if not request_id:
        return web.json_response(
            {'ok': False, 'error': 'missing request_id'},
            status=400
        )

    if request_id in completed_requests:
        return web.json_response(completed_requests[request_id])
    elif request_id in pending_requests:
        return web.json_response({'ok': False, 'status': 'pending'})
    else:
        return web.json_response(
            {'ok': False, 'error': 'unknown request_id'},
            status=404
        )


async def handle_http_health(request):
    """HTTP endpoint: Health check."""
    cleanup_old_requests()
    return web.json_response({
        'ok': True,
        'timestamp': time.time(),
        'connected_browsers': len(active_connections),
        'pending': len(pending_requests),
        'completed': len(completed_requests)
    })


async def start_http_server(app):
    """Start HTTP server for CLI communication."""
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, HOST, PORT)
    await site.start()
    print(f"HTTP server running on http://{HOST}:{PORT}")


async def main():
    """Start both WebSocket and HTTP servers."""
    print(f"Zen Bridge WebSocket Server")
    print(f"WebSocket: ws://{HOST}:{PORT + 1}")
    print(f"HTTP API: http://{HOST}:{PORT}")
    print("")

    # Setup HTTP server for CLI
    app = web.Application()
    app.router.add_post('/run', handle_http_run)
    app.router.add_get('/result', handle_http_result)
    app.router.add_get('/health', handle_http_health)

    # Start HTTP server
    await start_http_server(app)

    # Start WebSocket server for browser connections
    async with websockets.serve(handle_browser_connection, HOST, PORT + 1):
        print("Ready for connections!")
        await asyncio.Future()  # Run forever


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer stopped")
