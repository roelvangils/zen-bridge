"""
Execution commands for the Zen Browser Bridge CLI.

This module provides commands for executing JavaScript code in the browser:
- eval: Execute JavaScript code from arguments, files, or stdin
- exec: Execute JavaScript from a file
"""

from __future__ import annotations

import sys

import click

from zen.app.cli.base import builtin_open, format_output
from zen.services.bridge_executor import BridgeExecutor


@click.command()
@click.argument("code", required=False)
@click.option("-f", "--file", type=click.Path(exists=True), help="Execute code from file")
@click.option("-t", "--timeout", type=float, default=10.0, help="Timeout in seconds (default: 10)")
@click.option(
    "--format", type=click.Choice(["auto", "json", "raw"]), default="auto", help="Output format"
)
@click.option("--url", is_flag=True, help="Also print page URL")
@click.option("--title", is_flag=True, help="Also print page title")
def eval(code, file, timeout, format, url, title):
    """
    Execute JavaScript code in the active browser tab.

    Examples:

        zen eval "document.title"

        zen eval "alert('Hello from CLI!')"

        zen eval --file script.js

        echo "console.log('test')" | zen eval
    """
    executor = BridgeExecutor()

    # Read from stdin if no code or file provided
    if not code and not file:
        if not sys.stdin.isatty():
            code = sys.stdin.read()
        else:
            click.echo(
                "Error: No code provided. Use: zen eval CODE or zen eval --file FILE", err=True
            )
            sys.exit(1)

    try:
        if file:
            result = executor.execute_file(file, timeout=timeout)
        else:
            result = executor.execute(code, timeout=timeout)

        # Show metadata if requested
        if url and result.get("url"):
            click.echo(f"URL: {result['url']}", err=True)
        if title and result.get("title"):
            click.echo(f"Title: {result['title']}", err=True)

        # Show result
        output = format_output(result, format)
        click.echo(output)

        # Exit with error code if execution failed
        if not result.get("ok"):
            sys.exit(1)

    except (ConnectionError, TimeoutError, RuntimeError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@click.command()
@click.argument("filepath", type=click.Path(exists=True))
@click.option("-t", "--timeout", type=float, default=10.0, help="Timeout in seconds")
@click.option(
    "--format", type=click.Choice(["auto", "json", "raw"]), default="auto", help="Output format"
)
def exec(filepath, timeout, format):
    """
    Execute JavaScript from a file.

    Example:

        zen exec script.js
    """
    executor = BridgeExecutor()

    try:
        result = executor.execute_file(filepath, timeout=timeout)
        output = format_output(result, format)
        click.echo(output)

        if not result.get("ok"):
            sys.exit(1)

    except (ConnectionError, TimeoutError, RuntimeError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
