"""Selection command - Get selected text from the browser."""

import json
import sys

import click

from zen.services.bridge_executor import BridgeExecutor
from zen.services.script_loader import ScriptLoader


@click.command()
@click.option("--raw", is_flag=True, help="Output only the text without formatting")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def selected(raw, output_json):
    """
    Get the current text selection in the browser.

    Returns the selected text along with metadata like position and container element.

    Examples:
        # Get selection with metadata:
        zen selected

        # Get just the raw text (no formatting):
        zen selected --raw
    """
    executor = BridgeExecutor()
    executor.ensure_server_running()

    # Load the get_selection.js script
    loader = ScriptLoader()
    try:
        code = loader.load_script_sync("get_selection.js")
    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    try:
        result = executor.execute(code, timeout=60.0)

        if not result.get("ok"):
            click.echo(f"Error: {result.get('error')}", err=True)
            sys.exit(1)

        response = result.get("result", {})

        if not response.get("hasSelection"):
            if output_json:
                click.echo(json.dumps({"hasSelection": False, "text": "", "length": 0}, indent=2))
            elif not raw:
                click.echo("No text selected")
                click.echo("Hint: Select some text in the browser first, then run: zen selected")
            sys.exit(0)

        text = response.get("text", "")

        # JSON mode: output all data as JSON
        if output_json:
            click.echo(json.dumps(response, indent=2))
            return

        # Raw mode: just print the text, nothing else
        if raw:
            click.echo(text, nl=False)
            return

        # Display selection info
        click.echo(f"Selected Text ({response.get('length', 0)} characters):")
        click.echo("")

        # Show text (with proper formatting for long selections)
        if len(text) <= 200:
            click.echo(f'"{text}"')
        else:
            # Show first 200 chars with ellipsis
            click.echo(f'"{text[:200]}..."')
            click.echo("")
            click.echo(f"(showing first 200 of {len(text)} characters)")

        # Position info
        pos = response.get("position", {})
        click.echo("\nPosition:")
        click.echo(f"  x={pos.get('x')}, y={pos.get('y')}")
        click.echo(f"  Size: {pos.get('width')}×{pos.get('height')}px")

        # Container element
        container = response.get("container", {})
        if container.get("tag"):
            click.echo("\nContainer:")
            click.echo(f"  Tag:   <{container['tag']}>")
            if container.get("id"):
                click.echo(f"  ID:    {container['id']}")
            if container.get("class"):
                click.echo(f"  Class: {container['class']}")

        # HTML if different from text
        html = response.get("html", "")
        if html and html.strip() != text.strip():
            click.echo("\nHTML:")
            if len(html) <= 200:
                click.echo(f"  {html}")
            else:
                click.echo(f"  {html[:200]}...")

    except (ConnectionError, TimeoutError, RuntimeError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
