"""
Navigation commands for Zen Browser Bridge CLI.

This module provides commands for browser navigation:
- open: Navigate to a URL
- back: Go back in history
- forward: Go forward in history
- reload: Reload the current page
- previous/next/refresh: Hidden aliases for back/forward/reload
"""

import json
import sys

import click

from zen.services.bridge_executor import get_executor


# Save built-in functions before they get shadowed by Click commands
_builtin_open = open
_builtin_next = next


@click.command()
@click.argument("url")
@click.option("--wait", is_flag=True, help="Wait for page to finish loading")
@click.option(
    "--timeout",
    "-t",
    type=int,
    default=30,
    help="Timeout in seconds when using --wait (default: 30)",
)
def open(url, wait, timeout):
    """
    Navigate to a URL.

    Examples:
        # Navigate to a URL:
        zen open "https://example.com"

        # Navigate and wait for page load:
        zen open "https://example.com" --wait

        # Navigate with custom timeout:
        zen open "https://example.com" --wait --timeout 60
    """
    executor = get_executor()

    # Basic navigation code
    nav_code = f"""
        window.location.href = {json.dumps(url)};
        true;
    """

    # If wait flag is set, wait for page load
    if wait:
        nav_code = f"""
            (async () => {{
                window.location.href = {json.dumps(url)};

                // Wait for navigation to complete
                await new Promise((resolve, reject) => {{
                    const startTime = Date.now();
                    const timeoutMs = {timeout * 1000};

                    const checkLoad = () => {{
                        if (document.readyState === 'complete') {{
                            resolve();
                        }} else if (Date.now() - startTime > timeoutMs) {{
                            reject(new Error('Page load timeout'));
                        }} else {{
                            setTimeout(checkLoad, 100);
                        }}
                    }};

                    if (document.readyState === 'complete') {{
                        resolve();
                    }} else {{
                        window.addEventListener('load', resolve, {{ once: true }});
                        setTimeout(() => reject(new Error('Page load timeout')), timeoutMs);
                    }}
                }});

                return {{ ok: true, url: window.location.href }};
            }})();
        """

    click.echo(f"Opening: {url}")
    result = executor.execute(nav_code, timeout=timeout + 5 if wait else 10.0)

    executor.check_result_ok(result)

    if wait:
        response = result.get("result", {})
        if response.get("ok"):
            click.echo(f"✓ Page loaded: {response.get('url', url)}")
        else:
            click.echo("Navigation initiated")
    else:
        click.echo("✓ Navigation initiated")


@click.command()
def back():
    """
    Go back to the previous page in browser history.

    Example:
        zen back
    """
    executor = get_executor()

    code = "window.history.back(); true;"

    result = executor.execute(code, timeout=10.0)
    executor.check_result_ok(result)

    click.echo("✓ Navigated back")


@click.command(hidden=True)
def previous():
    """Alias for 'back' command."""
    ctx = click.get_current_context()
    ctx.invoke(back)


@click.command()
def forward():
    """
    Go forward to the next page in browser history.

    Example:
        zen forward
    """
    executor = get_executor()

    code = "window.history.forward(); true;"

    result = executor.execute(code, timeout=10.0)
    executor.check_result_ok(result)

    click.echo("✓ Navigated forward")


@click.command(hidden=True)
def next():
    """Alias for 'forward' command."""
    ctx = click.get_current_context()
    ctx.invoke(forward)


@click.command()
@click.option("--hard", is_flag=True, help="Hard reload (bypass cache)")
def reload(hard):
    """
    Reload the current page.

    Examples:
        # Normal reload:
        zen reload

        # Hard reload (bypass cache):
        zen reload --hard
    """
    executor = get_executor()

    if hard:
        code = "window.location.reload(true); true;"
        msg = "✓ Hard reload initiated"
    else:
        code = "window.location.reload(); true;"
        msg = "✓ Reload initiated"

    result = executor.execute(code, timeout=10.0)
    executor.check_result_ok(result)

    click.echo(msg)


@click.command(hidden=True)
@click.option("--hard", is_flag=True, help="Hard reload (bypass cache)")
def refresh(hard):
    """
    Reload the current page (alias for 'reload').

    Examples:
        # Normal reload:
        zen refresh

        # Hard reload (bypass cache):
        zen refresh --hard
    """
    # Just call the reload function
    ctx = click.get_current_context()
    ctx.invoke(reload, hard=hard)
