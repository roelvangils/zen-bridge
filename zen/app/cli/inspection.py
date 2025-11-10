"""
Inspection commands - Inspect elements, view details, and capture screenshots.

This module provides commands for element inspection and screenshot capture:
- inspect: Select and inspect elements
- inspected: View inspected element details
- screenshot: Capture element screenshots
"""

import base64
import json
import sys
from datetime import datetime
from pathlib import Path

import click

from zen.services.bridge_executor import BridgeExecutor
from zen.services.script_loader import ScriptLoader

# Save built-in open function before it gets shadowed by Click commands
_builtin_open = open


@click.command()
@click.argument("selector", required=False)
@click.pass_context
def inspect(ctx, selector):
    """
    Select an element and show its details.

    If no selector is provided, shows details of the currently selected element.

    Examples:
        zen inspect "h1"              # Select and show details
        zen inspect "#header"
        zen inspect ".main-content"
        zen inspect                   # Show currently selected element
    """
    executor = BridgeExecutor()
    executor.ensure_server_running()

    # If no selector provided, just show the currently marked element
    if not selector:
        # Redirect to 'inspected' command
        return ctx.invoke(inspected)

    # Mark the element
    mark_code = f"""
    (function() {{
        const el = document.querySelector('{selector}');
        if (!el) {{
            return {{ error: 'Element not found: {selector}' }};
        }}

        // Store reference
        window.__ZEN_INSPECTED_ELEMENT__ = el;

        // Highlight it briefly
        const originalOutline = el.style.outline;
        el.style.outline = '3px solid #0066ff';
        setTimeout(() => {{
            el.style.outline = originalOutline;
        }}, 1000);

        return {{ ok: true, message: 'Element marked for inspection' }};
    }})()
    """

    try:
        result = executor.execute(mark_code, timeout=60.0)

        if not result.get("ok"):
            click.echo(f"Error: {result.get('error')}", err=True)
            sys.exit(1)

        response = result.get("result", {})
        if response.get("error"):
            click.echo(f"Error: {response['error']}", err=True)
            sys.exit(1)

        click.echo(f"Selected element: {selector}")

        # Now show details immediately by calling inspected
        click.echo("")
        return ctx.invoke(inspected)

    except (ConnectionError, TimeoutError, RuntimeError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@click.command()
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def inspected(output_json):
    """
    Get information about the currently inspected element.

    Shows details about the element from DevTools inspection or from 'zen inspect'.

    To capture element from DevTools:
        1. Right-click element → Inspect
        2. In DevTools Console: zenStore()
        3. Run: zen inspected

    Or select programmatically:
        zen inspect "h1"
        zen inspected
    """
    executor = BridgeExecutor()
    loader = ScriptLoader()

    executor.ensure_server_running()

    # Load the get_inspected.js script
    try:
        code = loader.load_script_sync("get_inspected.js")
    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    try:
        result = executor.execute(code, timeout=60.0)

        if not result.get("ok"):
            click.echo(f"Error: {result.get('error')}", err=True)
            sys.exit(1)

        response = result.get("result", {})
        if response.get("error"):
            if output_json:
                click.echo(json.dumps({"error": response['error'], "hint": response.get("hint")}, indent=2))
            else:
                click.echo(f"Error: {response['error']}", err=True)
                if response.get("hint"):
                    click.echo(f"Hint: {response['hint']}", err=True)
            sys.exit(1)

        # JSON output
        if output_json:
            click.echo(json.dumps(response, indent=2))
            return

        # Display info
        click.echo(f"Tag:      <{response['tag']}>")
        click.echo(f"Selector: {response['selector']}")

        if response.get("parentTag"):
            click.echo(f"Parent:   <{response['parentTag']}>")

        if response.get("id"):
            click.echo(f"ID:       {response['id']}")

        if response.get("classes") and len(response["classes"]) > 0:
            click.echo(f"Classes:  {', '.join(response['classes'])}")

        if response.get("textContent"):
            text = response["textContent"]
            if len(text) > 60:
                text = text[:60] + "..."
            click.echo(f"Text:     {text}")

        # Dimensions
        dim = response["dimensions"]
        click.echo("\nDimensions:")
        click.echo(f"  Position: x={dim['left']}, y={dim['top']}")
        click.echo(f"  Size:     {dim['width']}×{dim['height']}px")
        click.echo(
            f"  Bounds:   top={dim['top']}, right={dim['right']}, bottom={dim['bottom']}, left={dim['left']}"
        )

        # Visibility
        vis = response.get("visibilityDetails", {})
        click.echo("\nVisibility:")
        click.echo(f"  Visible:     {'Yes' if response.get('visible') else 'No'}")
        click.echo(f"  In viewport: {'Yes' if vis.get('inViewport') else 'No'}")
        if vis.get("displayNone"):
            click.echo("  Issue:       display: none")
        if vis.get("visibilityHidden"):
            click.echo("  Issue:       visibility: hidden")
        if vis.get("opacityZero"):
            click.echo("  Issue:       opacity: 0")
        if vis.get("offScreen"):
            click.echo("  Issue:       positioned off-screen")

        # Accessibility
        a11y = response.get("accessibility", {})
        click.echo("\nAccessibility:")
        click.echo(f"  Role:            {a11y.get('role', 'N/A')}")

        # Accessible Name (computed)
        accessible_name = a11y.get("accessibleName", "")
        name_source = a11y.get("accessibleNameSource", "none")
        if accessible_name:
            # Truncate if too long
            display_name = (
                accessible_name if len(accessible_name) <= 50 else accessible_name[:50] + "..."
            )
            click.echo(f'  Accessible Name: "{display_name}"')
            click.echo(f"  Name computed from: {name_source}")
        else:
            click.echo("  Accessible Name: (none)")
            if name_source == "missing alt attribute":
                click.echo("  ⚠️  Warning: Image missing alt attribute")
            elif name_source == "none":
                click.echo("  ⚠️  Warning: No accessible name found")

        if a11y.get("ariaLabel"):
            click.echo(f"  ARIA Label:      {a11y['ariaLabel']}")
        if a11y.get("ariaLabelledBy"):
            click.echo(f"  ARIA LabelledBy: {a11y['ariaLabelledBy']}")
        if a11y.get("alt"):
            click.echo(f"  Alt text:        {a11y['alt']}")
        click.echo(f"  Focusable:       {'Yes' if a11y.get('focusable') else 'No'}")
        if a11y.get("tabIndex") is not None:
            click.echo(f"  Tab index:       {a11y['tabIndex']}")
        if a11y.get("disabled"):
            click.echo("  Disabled:        Yes")
        if a11y.get("ariaHidden"):
            click.echo(f"  ARIA Hidden:     {a11y['ariaHidden']}")

        # Semantic info
        semantic = response.get("semantic", {})
        if (
            semantic.get("isInteractive")
            or semantic.get("isFormElement")
            or semantic.get("isLandmark")
        ):
            click.echo("\nSemantic:")
            if semantic.get("isInteractive"):
                click.echo("  Interactive element")
            if semantic.get("isFormElement"):
                click.echo("  Form element")
            if semantic.get("isLandmark"):
                click.echo("  Landmark element")
            if semantic.get("hasClickHandler"):
                click.echo("  Has click handler")

        # Children
        click.echo("\nStructure:")
        click.echo(f"  Children: {response.get('childCount', 0)}")

        # Styles
        click.echo("\nStyles:")
        for key, value in response["styles"].items():
            click.echo(f"  {key}: {value}")

        # Attributes
        if response.get("attributes"):
            click.echo("\nAttributes:")
            for key, value in response["attributes"].items():
                if len(str(value)) > 50:
                    value = str(value)[:50] + "..."
                click.echo(f"  {key}: {value}")

    except (ConnectionError, TimeoutError, RuntimeError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@click.command()
@click.option(
    "--selector",
    "-s",
    required=True,
    help="CSS selector of element to screenshot (or use $0 for inspected element)",
)
@click.option("--output", "-o", type=click.Path(), default=None, help="Output file path")
def screenshot(selector, output):
    """
    Take a screenshot of a specific element.

    Captures a DOM element and saves it as a PNG image.
    Use $0 to screenshot the currently inspected element in DevTools.

    Examples:
        zen screenshot --selector "#main"
        zen screenshot -s ".hero-section" -o hero.png
        zen screenshot -s "$0" -o inspected.png
    """
    executor = BridgeExecutor()
    loader = ScriptLoader()

    executor.ensure_server_running()

    # Load screenshot script
    try:
        script = loader.load_script_sync("screenshot_element.js")
    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    # Replace selector placeholder
    escaped_selector = selector.replace("\\", "\\\\").replace('"', '\\"').replace("'", "\\'")
    code = script.replace("SELECTOR_PLACEHOLDER", f'"{escaped_selector}"')

    try:
        click.echo(f"Capturing element: {selector}")
        result = executor.execute(code, timeout=60.0)

        if not result.get("ok"):
            click.echo(f"Error: {result.get('error')}", err=True)
            sys.exit(1)

        response = result.get("result", {})
        if response.get("error"):
            click.echo(f"Error: {response['error']}", err=True)
            if response.get("details"):
                click.echo(f"Details: {response['details']}", err=True)
            sys.exit(1)

        # Get data URL and decode
        data_url = response.get("dataUrl")
        if not data_url:
            click.echo("Error: No image data received", err=True)
            sys.exit(1)

        # Extract base64 data
        if "," in data_url:
            base64_data = data_url.split(",", 1)[1]
        else:
            base64_data = data_url

        # Decode base64 to bytes
        try:
            image_data = base64.b64decode(base64_data)
        except Exception as e:
            click.echo(f"Error decoding image data: {e}", err=True)
            sys.exit(1)

        # Determine output path
        if output:
            output_path = Path(output)
        else:
            # Generate filename from selector and timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_selector = "".join(c if c.isalnum() else "_" for c in selector)
            filename = f"screenshot_{safe_selector}_{timestamp}.png"
            output_path = Path.cwd() / filename

        # Save image
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with _builtin_open(output_path, "wb") as f:
            f.write(image_data)

        size_kb = len(image_data) / 1024
        click.echo(f"Screenshot saved: {output_path}")
        click.echo(f"Size: {response.get('width')}x{response.get('height')}px ({size_kb:.1f} KB)")

    except (ConnectionError, TimeoutError, RuntimeError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
