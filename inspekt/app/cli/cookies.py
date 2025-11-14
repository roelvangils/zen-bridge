"""
Cookies command group - Manage browser cookies.

This module provides commands for cookie management:
- list: List all cookies for the current page
- get: Get a specific cookie by name
- set: Set a cookie with various options
- delete: Delete a specific cookie
- clear: Clear all cookies
"""

from __future__ import annotations

import json
import sys

import click

from inspekt.services.bridge_executor import get_executor
from inspekt.services.script_loader import ScriptLoader


@click.group()
def cookies():
    """Manage browser cookies."""
    pass


@cookies.command(name="list")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def cookies_list(output_json):
    """
    List all cookies for the current page.

    Example:
        zen cookies list
        zen cookies list --json
    """
    _execute_cookie_action("list", output_json=output_json)


@cookies.command(name="get")
@click.argument("name")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def cookies_get(name, output_json):
    """
    Get the value of a specific cookie.

    Example:
        zen cookies get session_id
        zen cookies get session_id --json
    """
    _execute_cookie_action("get", cookie_name=name, output_json=output_json)


@cookies.command(name="set")
@click.argument("name")
@click.argument("value")
@click.option("--max-age", type=int, help="Max age in seconds")
@click.option("--expires", type=str, help="Expiration date (e.g., 'Wed, 21 Oct 2025 07:28:00 GMT')")
@click.option("--path", type=str, default="/", help="Cookie path (default: /)")
@click.option("--domain", type=str, help="Cookie domain")
@click.option("--secure", is_flag=True, help="Secure flag (HTTPS only)")
@click.option(
    "--same-site",
    type=click.Choice(["Strict", "Lax", "None"], case_sensitive=False),
    help="SameSite attribute",
)
def cookies_set(name, value, max_age, expires, path, domain, secure, same_site):
    """
    Set a cookie.

    Examples:
        zen cookies set session_id abc123
        zen cookies set token xyz --max-age 3600
        zen cookies set user_pref dark --path / --secure
    """
    options = {"path": path}
    if max_age:
        options["maxAge"] = max_age
    if expires:
        options["expires"] = expires
    if domain:
        options["domain"] = domain
    if secure:
        options["secure"] = True
    if same_site:
        options["sameSite"] = same_site

    _execute_cookie_action("set", cookie_name=name, cookie_value=value, options=options)


@cookies.command(name="delete")
@click.argument("name")
def cookies_delete(name):
    """
    Delete a specific cookie.

    Example:
        zen cookies delete session_id
    """
    _execute_cookie_action("delete", cookie_name=name)


@cookies.command(name="clear")
def cookies_clear():
    """
    Clear all cookies for the current page.

    Example:
        zen cookies clear
    """
    _execute_cookie_action("clear")


def _execute_cookie_action(action, cookie_name="", cookie_value="", options=None, output_json=False):
    """Helper function to execute cookie actions."""
    executor = get_executor()
    loader = ScriptLoader()

    # Load the cookies script
    try:
        script = loader.load_script_sync("cookies.js")
    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    # Replace placeholders
    options_json = json.dumps(options if options else {})
    code = script.replace("ACTION_PLACEHOLDER", action)
    code = code.replace("NAME_PLACEHOLDER", cookie_name)
    code = code.replace("VALUE_PLACEHOLDER", cookie_value)
    code = code.replace("OPTIONS_PLACEHOLDER", options_json)

    result = executor.execute(code, timeout=60.0)

    if not result.get("ok"):
        click.echo(f"Error: {result.get('error')}", err=True)
        sys.exit(1)

    response = result.get("result", {})

    if response.get("error"):
        click.echo(f"Error: {response['error']}", err=True)
        sys.exit(1)

    # Display results based on action
    if action == "list":
        cookies_dict = response.get("cookies", {})
        count = response.get("count", 0)

        if output_json:
            output_data = {
                "cookies": cookies_dict,
                "count": count
            }
            click.echo(json.dumps(output_data, indent=2))
        elif count == 0:
            click.echo("No cookies found")
        else:
            click.echo(f"Cookies ({count}):\n")
            for name, value in cookies_dict.items():
                # Truncate long values
                display_value = value if len(value) <= 60 else value[:60] + "..."
                click.echo(f"  {name} = {display_value}")

    elif action == "get":
        name = response.get("name")
        value = response.get("value")
        exists = response.get("exists")

        if output_json:
            output_data = {
                "name": name,
                "value": value,
                "exists": exists
            }
            click.echo(json.dumps(output_data, indent=2))
            if not exists:
                sys.exit(1)
        elif exists:
            click.echo(f"{name} = {value}")
        else:
            click.echo(f"Cookie not found: {name}", err=True)
            sys.exit(1)

    elif action == "set":
        click.echo(f"✓ Cookie set: {response.get('name')} = {response.get('value')}")

    elif action == "delete":
        click.echo(f"✓ Cookie deleted: {response.get('name')}")

    elif action == "clear":
        deleted = response.get("deleted", 0)
        click.echo(f"✓ Cleared {deleted} cookie(s)")
