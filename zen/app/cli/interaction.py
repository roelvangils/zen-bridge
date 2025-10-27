"""
Interaction commands for the Zen Browser Bridge CLI.

This module provides commands for browser interaction:
- send: Send keyboard input to elements
- click: Click on elements
- double-click: Double-click on elements
- right-click: Right-click (context menu) on elements
- wait: Wait for elements or conditions
"""

from __future__ import annotations

import sys

import click

from zen.app.cli.base import builtin_open
from zen.services.bridge_executor import BridgeExecutor
from zen.services.script_loader import ScriptLoader


@click.command()
@click.argument("text")
@click.option("--selector", "-s", help="CSS selector to focus before typing")
def send(text, selector):
    """
    Send text to the browser by typing it character by character.

    Types the given text into the currently focused input field,
    or into a specific element if --selector is provided.

    Examples:
        zen send "Hello World"
        zen send "test@example.com" --selector "input[type=email]"
    """
    executor = BridgeExecutor()
    executor.ensure_server_running()

    # Focus the element first if selector provided
    if selector:
        focus_code = f"""
        (function() {{
            const el = document.querySelector('{selector}');
            if (!el) {{
                return {{ error: 'Element not found: {selector}' }};
            }}
            el.focus();
            return {{ ok: true }};
        }})()
        """
        result = executor.execute(focus_code, timeout=60.0)
        if not result.get("ok") or result.get("result", {}).get("error"):
            error = result.get("error") or result.get("result", {}).get("error", "Unknown error")
            click.echo(f"Error focusing element: {error}", err=True)
            sys.exit(1)

    # Load and execute the send_keys script
    script_loader = ScriptLoader()
    try:
        script = script_loader.load_script_sync("send_keys.js")
    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    # Replace placeholder with properly escaped text
    # Escape quotes and backslashes for JavaScript
    escaped_text = text.replace("\\", "\\\\").replace('"', '\\"').replace("'", "\\'")
    code = script.replace("TEXT_PLACEHOLDER", f'"{escaped_text}"')

    try:
        result = executor.execute(code, timeout=60.0)

        if not result.get("ok"):
            click.echo(f"Error: {result.get('error')}", err=True)
            sys.exit(1)

        response = result.get("result", {})
        if response.get("error"):
            click.echo(f"Error: {response['error']}", err=True)
            if response.get("hint"):
                click.echo(f"Hint: {response['hint']}", err=True)
            sys.exit(1)

        click.echo(response.get("message", "Text sent successfully"))

    except (ConnectionError, TimeoutError, RuntimeError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@click.command(name="click")
@click.argument("selector", required=False, default="$0")
def click_element(selector):
    """
    Click on an element.

    Uses the stored element from 'zen inspect' by default, or specify a selector.

    Examples:
        # Click on stored element:
        zen inspect "button#submit"
        zen click

        # Click directly on element:
        zen click "button#submit"
        zen click ".primary-button"
    """
    _perform_click(selector, "click")


@click.command(name="double-click")
@click.argument("selector", required=False, default="$0")
def double_click(selector):
    """
    Double-click on an element.

    Uses the stored element from 'zen inspect' by default, or specify a selector.

    Examples:
        zen double-click "div.item"
        zen inspect "div.item"
        zen double-click
    """
    _perform_click(selector, "dblclick")


@click.command(name="doubleclick", hidden=True)
@click.argument("selector", required=False, default="$0")
def doubleclick_alias(selector):
    """Alias for double-click command."""
    _perform_click(selector, "dblclick")


@click.command(name="right-click")
@click.argument("selector", required=False, default="$0")
def right_click(selector):
    """
    Right-click (context menu) on an element.

    Uses the stored element from 'zen inspect' by default, or specify a selector.

    Examples:
        zen right-click "a.download-link"
        zen inspect "a.download-link"
        zen right-click
    """
    _perform_click(selector, "contextmenu")


@click.command(name="rightclick", hidden=True)
@click.argument("selector", required=False, default="$0")
def rightclick_alias(selector):
    """Alias for right-click command."""
    _perform_click(selector, "contextmenu")


def _perform_click(selector, click_type):
    """Helper function to perform click actions."""
    executor = BridgeExecutor()
    executor.ensure_server_running()

    # Load the click script
    script_loader = ScriptLoader()
    try:
        script = script_loader.load_script_sync("click_element.js")
    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    # Replace placeholders
    escaped_selector = selector.replace("\\", "\\\\").replace('"', '\\"').replace("'", "\\'")
    code = script.replace("SELECTOR_PLACEHOLDER", escaped_selector)
    code = code.replace("CLICK_TYPE_PLACEHOLDER", click_type)

    try:
        result = executor.execute(code, timeout=60.0)

        if not result.get("ok"):
            click.echo(f"Error: {result.get('error')}", err=True)
            sys.exit(1)

        response = result.get("result", {})

        if response.get("error"):
            click.echo(f"Error: {response['error']}", err=True)
            sys.exit(1)

        # Show confirmation
        action_name = {
            "click": "Clicked",
            "dblclick": "Double-clicked",
            "contextmenu": "Right-clicked",
        }.get(click_type, "Clicked")

        click.echo(f"{action_name}: {response.get('element', 'element')}")
        pos = response.get("position", {})
        if pos:
            click.echo(f"Position: x={pos.get('x')}, y={pos.get('y')}")

    except (ConnectionError, TimeoutError, RuntimeError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@click.command()
@click.argument("selector")
@click.option("--timeout", "-t", type=int, default=30, help="Timeout in seconds (default: 30)")
@click.option("--visible", is_flag=True, help="Wait for element to be visible")
@click.option("--hidden", is_flag=True, help="Wait for element to be hidden")
@click.option("--text", type=str, help="Wait for element to contain specific text")
def wait(selector, timeout, visible, hidden, text):
    """
    Wait for an element to appear, be visible, hidden, or contain text.

    By default, waits for element to exist in the DOM.

    Examples:
        # Wait for element to exist (up to 30 seconds):
        zen wait "button#submit"

        # Wait for element to be visible:
        zen wait ".modal" --visible

        # Wait for element to be hidden:
        zen wait ".loading-spinner" --hidden

        # Wait for element to contain text:
        zen wait "h1" --text "Success"

        # Custom timeout (10 seconds):
        zen wait "div.result" --timeout 10
    """
    executor = BridgeExecutor()
    executor.ensure_server_running()

    # Determine wait type
    if hidden:
        wait_type = "hidden"
    elif visible:
        wait_type = "visible"
    elif text:
        wait_type = "text"
    else:
        wait_type = "exists"

    # Load the wait script
    script_loader = ScriptLoader()
    try:
        script = script_loader.load_script_sync("wait_for.js")
    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    # Replace placeholders
    escaped_selector = selector.replace("\\", "\\\\").replace('"', '\\"').replace("'", "\\'")
    escaped_text = (text or "").replace("\\", "\\\\").replace('"', '\\"').replace("'", "\\'")
    timeout_ms = timeout * 1000

    code = script.replace("SELECTOR_PLACEHOLDER", escaped_selector)
    code = code.replace("WAIT_TYPE_PLACEHOLDER", wait_type)
    code = code.replace("TEXT_PLACEHOLDER", escaped_text)
    code = code.replace("TIMEOUT_PLACEHOLDER", str(timeout_ms))

    # Show waiting message
    wait_msg = {
        "exists": f"Waiting for element: {selector}",
        "visible": f"Waiting for element to be visible: {selector}",
        "hidden": f"Waiting for element to be hidden: {selector}",
        "text": f'Waiting for element to contain "{text}": {selector}',
    }.get(wait_type, f"Waiting for: {selector}")

    click.echo(wait_msg)

    try:
        # Use longer timeout for the request (add 5 seconds buffer)
        result = executor.execute(code, timeout=timeout + 5)

        if not result.get("ok"):
            click.echo(f"Error: {result.get('error')}", err=True)
            sys.exit(1)

        response = result.get("result", {})

        if response.get("error"):
            click.echo(f"Error: {response['error']}", err=True)
            sys.exit(1)

        if response.get("timeout"):
            click.echo(f"✗ Timeout: {response.get('message', 'Operation timed out')}", err=True)
            sys.exit(1)

        # Success!
        waited_sec = response.get("waited", 0) / 1000
        click.echo(f"✓ {response.get('status', 'Condition met')}")
        if response.get("element"):
            click.echo(f"  Element: {response['element']}")
        click.echo(f"  Waited: {waited_sec:.2f}s")

    except (ConnectionError, TimeoutError, RuntimeError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
