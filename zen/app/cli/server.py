"""Server management commands for the Zen bridge."""

import subprocess
import sys

import click

from zen.client import BridgeClient


@click.group()
def server():
    """Manage the bridge server."""
    pass


@server.command()
@click.option("-p", "--port", type=int, default=8765, help="Port to run on (default: 8765)")
@click.option("-d", "--daemon", is_flag=True, help="Run in background")
def start(port, daemon):
    """Start the bridge server."""
    client = BridgeClient(port=port)

    if client.is_alive():
        click.echo(f"Bridge server is already running on port {port}")
        return

    if daemon:
        # Run in background
        click.echo(f"Starting WebSocket bridge server in background on port {port}...")
        subprocess.Popen(
            [sys.executable, "-m", "zen.bridge_ws"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        # Wait a bit and check if it started
        import time

        time.sleep(0.5)
        if client.is_alive():
            click.echo(
                "WebSocket server started successfully on ports 8765 (HTTP) and 8766 (WebSocket)"
            )
        else:
            click.echo("Failed to start server", err=True)
            sys.exit(1)
    else:
        # Run in foreground
        from zen.bridge_ws import main as start_ws_server

        try:
            import asyncio

            asyncio.run(start_ws_server())
        except KeyboardInterrupt:
            click.echo("\nServer stopped")


@server.command()
def status():
    """Check bridge server status."""
    client = BridgeClient()

    if client.is_alive():
        status = client.get_status()
        if status:
            click.echo("Bridge server is running")
            click.echo(f"  Pending requests:   {status.get('pending', 0)}")
            click.echo(f"  Completed requests: {status.get('completed', 0)}")
        else:
            click.echo("Bridge server is running (status unavailable)")
    else:
        click.echo("Bridge server is not running")
        click.echo("Start it with: zen server start")
        sys.exit(1)


@server.command()
def stop():
    """Stop the bridge server."""
    click.echo("Note: Use Ctrl+C to stop the server if running in foreground")
    click.echo("For daemon mode, use: pkill -f 'zen.bridge_ws'")
