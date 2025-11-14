"""
Storage command group - Manage browser storage (localStorage and sessionStorage).

This module provides commands for storage management:
- list: List all storage items
- get: Get a specific item by key
- set: Set an item with key-value
- delete: Delete a specific item
- clear: Clear all items
"""

from __future__ import annotations

import json
import sys

import click

from inspekt.services.bridge_executor import get_executor
from inspekt.services.script_loader import ScriptLoader


@click.group()
def storage():
    """Manage browser storage (localStorage and sessionStorage)."""
    pass


@storage.command(name="list")
@click.option(
    "--type",
    "storage_type",
    type=click.Choice(["local", "session", "all"], case_sensitive=False),
    default="all",
    help="Storage type to list (default: all)"
)
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def storage_list(storage_type, output_json):
    """
    List all storage items.

    Examples:
        inspekt storage list
        inspekt storage list --type=local
        inspekt storage list --type=session --json
    """
    if storage_type == "all":
        # List both types
        local_result = _execute_storage_action("local", "list", output_json=False)
        session_result = _execute_storage_action("session", "list", output_json=False)

        if output_json:
            output_data = {
                "localStorage": local_result.get("items", {}),
                "localStorageCount": local_result.get("count", 0),
                "sessionStorage": session_result.get("items", {}),
                "sessionStorageCount": session_result.get("count", 0)
            }
            click.echo(json.dumps(output_data, indent=2))
        else:
            _display_list_result(local_result, "localStorage")
            click.echo()  # Blank line separator
            _display_list_result(session_result, "sessionStorage")
    else:
        result = _execute_storage_action(storage_type, "list", output_json=output_json)
        if output_json:
            click.echo(json.dumps(result, indent=2))
        else:
            storage_name = "localStorage" if storage_type == "local" else "sessionStorage"
            _display_list_result(result, storage_name)


@storage.command(name="get")
@click.argument("key")
@click.option(
    "--type",
    "storage_type",
    type=click.Choice(["local", "session"], case_sensitive=False),
    default="local",
    help="Storage type (default: local)"
)
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def storage_get(key, storage_type, output_json):
    """
    Get the value of a specific storage item.

    Examples:
        inspekt storage get user_token
        inspekt storage get session_data --type=session
        inspekt storage get preferences --type=local --json
    """
    result = _execute_storage_action(storage_type, "get", key=key, output_json=output_json)

    if output_json:
        click.echo(json.dumps(result, indent=2))
        if not result.get("exists"):
            sys.exit(1)
    elif result.get("exists"):
        value = result.get("value")
        # Try to pretty-print JSON values
        try:
            parsed = json.loads(value)
            click.echo(json.dumps(parsed, indent=2))
        except (json.JSONDecodeError, TypeError):
            click.echo(value)
    else:
        storage_name = "localStorage" if storage_type == "local" else "sessionStorage"
        click.echo(f"Key not found in {storage_name}: {key}", err=True)
        sys.exit(1)


@storage.command(name="set")
@click.argument("key")
@click.argument("value")
@click.option(
    "--type",
    "storage_type",
    type=click.Choice(["local", "session"], case_sensitive=False),
    default="local",
    help="Storage type (default: local)"
)
def storage_set(key, value, storage_type):
    """
    Set a storage item.

    Examples:
        inspekt storage set user_token abc123
        inspekt storage set session_data '{"user":"john"}' --type=session
        inspekt storage set preferences '{"theme":"dark"}' --type=local
    """
    result = _execute_storage_action(storage_type, "set", key=key, value=value)
    storage_name = "localStorage" if storage_type == "local" else "sessionStorage"
    click.echo(f"✓ Item set in {storage_name}: {result.get('key')}")


@storage.command(name="delete")
@click.argument("key")
@click.option(
    "--type",
    "storage_type",
    type=click.Choice(["local", "session"], case_sensitive=False),
    default="local",
    help="Storage type (default: local)"
)
def storage_delete(key, storage_type):
    """
    Delete a specific storage item.

    Examples:
        inspekt storage delete user_token
        inspekt storage delete session_data --type=session
    """
    result = _execute_storage_action(storage_type, "delete", key=key)
    storage_name = "localStorage" if storage_type == "local" else "sessionStorage"
    click.echo(f"✓ Item deleted from {storage_name}: {result.get('key')}")


@storage.command(name="clear")
@click.option(
    "--type",
    "storage_type",
    type=click.Choice(["local", "session", "all"], case_sensitive=False),
    default="all",
    help="Storage type to clear (default: all)"
)
@click.option("--force", is_flag=True, help="Skip confirmation prompt")
def storage_clear(storage_type, force):
    """
    Clear all storage items.

    Examples:
        inspekt storage clear --type=local
        inspekt storage clear --type=session --force
        inspekt storage clear --force  # Clear both
    """
    if not force:
        storage_name = {
            "local": "localStorage",
            "session": "sessionStorage",
            "all": "localStorage and sessionStorage"
        }[storage_type]

        if not click.confirm(f"Are you sure you want to clear all items from {storage_name}?"):
            click.echo("Cancelled")
            return

    if storage_type == "all":
        local_result = _execute_storage_action("local", "clear")
        session_result = _execute_storage_action("session", "clear")
        local_count = local_result.get("deleted", 0)
        session_count = session_result.get("deleted", 0)
        click.echo(f"✓ Cleared {local_count} item(s) from localStorage")
        click.echo(f"✓ Cleared {session_count} item(s) from sessionStorage")
    else:
        result = _execute_storage_action(storage_type, "clear")
        deleted = result.get("deleted", 0)
        storage_name = "localStorage" if storage_type == "local" else "sessionStorage"
        click.echo(f"✓ Cleared {deleted} item(s) from {storage_name}")


def _execute_storage_action(storage_type, action, key="", value="", output_json=False):
    """Helper function to execute storage actions."""
    executor = get_executor()
    loader = ScriptLoader()

    # Determine script name based on storage type
    script_name = "localStorage.js" if storage_type == "local" else "sessionStorage.js"

    # Load the storage script
    try:
        script = loader.load_script_sync(script_name)
    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    # Replace placeholders
    code = script.replace("ACTION_PLACEHOLDER", action)
    code = code.replace("KEY_PLACEHOLDER", key)
    code = code.replace("VALUE_PLACEHOLDER", value)

    result = executor.execute(code, timeout=60.0)

    if not result.get("ok"):
        click.echo(f"Error: {result.get('error')}", err=True)
        sys.exit(1)

    response = result.get("result", {})

    if not response.get("ok"):
        click.echo(f"Error: {response.get('error')}", err=True)
        sys.exit(1)

    return response


def _display_list_result(result, storage_name):
    """Display list results in human-readable format."""
    items = result.get("items", {})
    count = result.get("count", 0)

    if count == 0:
        click.echo(f"{storage_name}: No items found")
    else:
        click.echo(f"{storage_name} ({count} items):\n")
        for key, value in items.items():
            # Truncate long values
            display_value = value if len(str(value)) <= 60 else str(value)[:60] + "..."
            click.echo(f"  {key} = {display_value}")
