#!/usr/bin/env python3
"""
Zen Browser Bridge CLI - Execute JavaScript in your browser from the command line.
"""
import sys
import os
import json
import click
import subprocess
import signal
from pathlib import Path
from .client import BridgeClient
from . import __version__
from . import config as zen_config


def format_output(result: dict, format_type: str = "auto") -> str:
    """Format execution result for display."""
    if not result.get("ok"):
        error = result.get("error", "Unknown error")
        return f"Error: {error}"

    value = result.get("result")

    if format_type == "json":
        return json.dumps(value, indent=2)
    elif format_type == "raw":
        return str(value) if value is not None else ""
    else:  # auto
        if value is None:
            return "undefined"
        elif isinstance(value, str):
            return value
        elif isinstance(value, (dict, list)):
            return json.dumps(value, indent=2)
        else:
            return str(value)


@click.group()
@click.version_option(version=__version__)
def cli():
    """Zen Browser Bridge - Execute JavaScript in your browser from the CLI."""
    pass


@cli.command()
@click.argument("code", required=False)
@click.option("-f", "--file", type=click.Path(exists=True), help="Execute code from file")
@click.option("-t", "--timeout", type=float, default=10.0, help="Timeout in seconds (default: 10)")
@click.option("--format", type=click.Choice(["auto", "json", "raw"]), default="auto", help="Output format")
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
    client = BridgeClient()

    # Read from stdin if no code or file provided
    if not code and not file:
        if not sys.stdin.isatty():
            code = sys.stdin.read()
        else:
            click.echo("Error: No code provided. Use: zen eval CODE or zen eval --file FILE", err=True)
            sys.exit(1)

    try:
        if file:
            result = client.execute_file(file, timeout=timeout)
        else:
            result = client.execute(code, timeout=timeout)

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


@cli.command()
@click.argument("filepath", type=click.Path(exists=True))
@click.option("-t", "--timeout", type=float, default=10.0, help="Timeout in seconds")
@click.option("--format", type=click.Choice(["auto", "json", "raw"]), default="auto", help="Output format")
def exec(filepath, timeout, format):
    """
    Execute JavaScript from a file.

    Example:

        zen exec script.js
    """
    client = BridgeClient()

    try:
        result = client.execute_file(filepath, timeout=timeout)
        output = format_output(result, format)
        click.echo(output)

        if not result.get("ok"):
            sys.exit(1)

    except (ConnectionError, TimeoutError, RuntimeError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
def info():
    """Get information about the current browser tab."""
    client = BridgeClient()

    code = """
    ({
        url: location.href,
        title: document.title,
        domain: location.hostname,
        protocol: location.protocol,
        readyState: document.readyState,
        width: window.innerWidth,
        height: window.innerHeight
    })
    """

    try:
        result = client.execute(code)

        if result.get("ok"):
            data = result.get("result", {})

            # Get userscript version
            userscript_version = client.get_userscript_version() or 'unknown'

            click.echo(f"URL:      {data.get('url', 'N/A')}")
            click.echo(f"Title:    {data.get('title', 'N/A')}")
            click.echo(f"Domain:   {data.get('domain', 'N/A')}")
            click.echo(f"Protocol: {data.get('protocol', 'N/A')}")
            click.echo(f"State:    {data.get('readyState', 'N/A')}")
            click.echo(f"Size:     {data.get('width', 'N/A')}x{data.get('height', 'N/A')}")
            click.echo(f"")
            click.echo(f"Userscript version: {userscript_version}")
        else:
            click.echo(f"Error: {result.get('error')}", err=True)
            sys.exit(1)

    except (ConnectionError, TimeoutError, RuntimeError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.group()
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
            start_new_session=True
        )
        # Wait a bit and check if it started
        import time
        time.sleep(0.5)
        if client.is_alive():
            click.echo("WebSocket server started successfully on ports 8765 (HTTP) and 8766 (WebSocket)")
        else:
            click.echo("Failed to start server", err=True)
            sys.exit(1)
    else:
        # Run in foreground
        from .bridge_ws import main as start_ws_server
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


@cli.command()
def repl():
    """
    Start an interactive REPL session.

    Execute JavaScript interactively. Type 'exit' or press Ctrl+D to quit.
    """
    client = BridgeClient()

    if not client.is_alive():
        click.echo("Error: Bridge server is not running. Start it with: zen server start", err=True)
        sys.exit(1)

    click.echo("Zen Browser REPL - Type JavaScript code, 'exit' to quit")
    click.echo("")

    # Get initial page info
    try:
        result = client.execute("({url: location.href, title: document.title})")
        if result.get("ok"):
            data = result.get("result", {})
            click.echo(f"Connected to: {data.get('title', 'Unknown')} ({data.get('url', 'Unknown')})")
            click.echo("")
    except:
        pass

    while True:
        try:
            code = click.prompt("zen>", prompt_suffix=" ", default="", show_default=False)

            if not code.strip():
                continue

            if code.strip().lower() in ["exit", "quit"]:
                break

            try:
                result = client.execute(code, timeout=10.0)
                output = format_output(result, "auto")
                if output:
                    click.echo(output)
            except (ConnectionError, TimeoutError, RuntimeError) as e:
                click.echo(f"Error: {e}", err=True)

        except (EOFError, KeyboardInterrupt):
            click.echo("")
            break

    click.echo("Goodbye!")


@cli.command()
@click.argument("selector")
@click.option("-c", "--color", default="red", help="Outline color (default: red)")
@click.option("--clear", is_flag=True, help="Clear all highlights")
def highlight(selector, color, clear):
    """
    Highlight elements matching a CSS selector on the page.

    Adds a 2px dashed outline around matching elements.

    Examples:

        zen highlight "h1, h2"

        zen highlight ".error" --color orange

        zen highlight "a" --clear
    """
    client = BridgeClient()

    if not client.is_alive():
        click.echo("Error: Bridge server is not running. Start it with: zen server start", err=True)
        sys.exit(1)

    if clear:
        # Clear all highlights
        code = """
        document.querySelectorAll('[data-zen-highlight]').forEach(el => {
            el.style.outline = '';
            el.removeAttribute('data-zen-highlight');
        });
        'Highlights cleared'
        """
    else:
        # Add highlights
        code = f"""
        (function(selector, color) {{
            const elements = document.querySelectorAll(selector);

            if (elements.length === 0) {{
                return `No elements found matching: ${{selector}}`;
            }}

            // Clear previous highlights
            document.querySelectorAll('[data-zen-highlight]').forEach(el => {{
                el.style.outline = '';
                el.removeAttribute('data-zen-highlight');
            }});

            // Add new highlights
            elements.forEach((el, index) => {{
                el.style.outline = `2px dashed ${{color}}`;
                el.setAttribute('data-zen-highlight', index);
            }});

            return `Highlighted ${{elements.length}} element(s) matching: ${{selector}}`;
        }})('{selector}', '{color}')
        """

    try:
        result = client.execute(code, timeout=10.0)
        output = format_output(result, "auto")
        click.echo(output)

        if not result.get("ok"):
            sys.exit(1)

    except (ConnectionError, TimeoutError, RuntimeError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
def userscript():
    """Display the userscript that needs to be installed in your browser."""
    script_path = Path(__file__).parent.parent / "userscript.js"

    if script_path.exists():
        click.echo(f"Userscript location: {script_path}")
        click.echo("")
        click.echo("To install:")
        click.echo("1. Install a userscript manager (Tampermonkey, Greasemonkey, Violentmonkey)")
        click.echo("2. Create a new script and paste the contents of userscript.js")
        click.echo("3. Save and enable the script")
        click.echo("")
        click.echo("Or use: cat userscript.js | pbcopy  (to copy to clipboard on macOS)")
    else:
        click.echo(f"Error: userscript.js not found at {script_path}", err=True)
        sys.exit(1)


@cli.command()
@click.option("-o", "--output", type=click.Path(), default=None, help="Output directory (default: ~/Downloads/<domain>)")
@click.option("--list", "list_only", is_flag=True, help="Only list files without downloading")
@click.option("-t", "--timeout", type=float, default=30.0, help="Timeout in seconds (default: 30)")
def download(output, list_only, timeout):
    """
    Find and download files from the current page.

    Discovers images, PDFs, videos, audio files, documents and archives.
    Uses interactive selection with gum choose.

    Examples:

        zen download

        zen download --output ~/Downloads

        zen download --list
    """
    import requests
    import os

    client = BridgeClient()

    if not client.is_alive():
        click.echo("Error: Bridge server is not running. Start it with: zen server start", err=True)
        sys.exit(1)

    # Execute the find_downloads script
    script_path = Path(__file__).parent / "scripts" / "find_downloads.js"

    if not script_path.exists():
        click.echo(f"Error: find_downloads.js script not found at {script_path}", err=True)
        sys.exit(1)

    click.echo("Scanning page for downloadable files...")

    try:
        result = client.execute_file(str(script_path), timeout=timeout)

        if not result.get("ok"):
            click.echo(f"Error: {result.get('error')}", err=True)
            sys.exit(1)

        result_data = result.get("result", {})

        # Handle new format with url and files
        if isinstance(result_data, dict) and 'files' in result_data:
            files_by_category = result_data['files']
            page_url = result_data.get('url', '')
        else:
            # Fallback for old format
            files_by_category = result_data
            page_url = ""

        # Count total files
        total_files = sum(len(files) for files in files_by_category.values())

        if total_files == 0:
            click.echo("No downloadable files found on this page.")
            return

        # Determine output directory
        if output is None:
            # Default: ~/Downloads/<domain>
            try:
                from urllib.parse import urlparse
                domain = urlparse(page_url).hostname or "unknown"
                domain = domain.replace('www.', '')  # Remove www. prefix
                downloads_dir = Path.home() / "Downloads" / domain
            except Exception:
                downloads_dir = Path.home() / "Downloads" / "zen-downloads"
        else:
            downloads_dir = Path(output)

        # Build options list for gum choose
        options = []
        option_map = {}  # Map display text to actual data

        # Category labels (lowercase)
        category_names = {
            'images': 'images',
            'pdfs': 'PDF documents',
            'videos': 'videos',
            'audio': 'audio files',
            'documents': 'documents',
            'archives': 'archives'
        }

        # Add "Download all" options per category
        for category, files in files_by_category.items():
            if files:
                count = len(files)
                display = f"Download all {category_names.get(category, category)} ({count} files)"
                options.append(display)
                option_map[display] = {'type': 'category', 'category': category, 'files': files}

        # Add separator
        if options:
            separator = "─" * 60
            options.append(separator)
            option_map[separator] = {'type': 'separator'}

        # Add individual files grouped by category
        for category, files in files_by_category.items():
            if files:
                # Add category header
                header = f"--- {category_names.get(category, category.upper())} ---"
                options.append(header)
                option_map[header] = {'type': 'header'}

                # Add individual files
                for file_info in files:
                    filename = file_info['filename']
                    url = file_info['url']

                    # Try to get file size if in list mode
                    display = f"  {filename}"
                    options.append(display)
                    option_map[display] = {
                        'type': 'file',
                        'filename': filename,
                        'url': url,
                        'category': category
                    }

        # List only mode
        if list_only:
            click.echo(f"\nFound {total_files} downloadable files:\n")
            for option in options:
                if option_map.get(option, {}).get('type') not in ['separator', 'category']:
                    click.echo(option)
            return

        # Simple numbered list selection
        click.echo(f"\nFound {total_files} files. Select what to download:\n")

        # Build simple menu
        menu_options = []

        # Find largest image if we have images
        largest_image = None
        if 'images' in files_by_category and files_by_category['images']:
            images_with_dims = [img for img in files_by_category['images']
                              if img.get('width', 0) > 0 and img.get('height', 0) > 0]
            if images_with_dims:
                # Find image with largest area
                largest_image = max(images_with_dims,
                                  key=lambda img: img.get('width', 0) * img.get('height', 0))

        # Add largest image option first
        if largest_image:
            width = largest_image.get('width', 0)
            height = largest_image.get('height', 0)
            menu_options.append({
                'text': f"Download the largest image ({width}×{height}px)",
                'data': {'type': 'file', 'files': [largest_image]}
            })

        # Add category download options
        for category, files in files_by_category.items():
            if files:
                count = len(files)
                menu_options.append({
                    'text': f"Download all {category_names.get(category, category)} ({count} files)",
                    'data': {'type': 'category', 'category': category, 'files': files}
                })

        # Display menu
        for i, opt in enumerate(menu_options, 1):
            click.echo(f" {i}. {opt['text']}")

        click.echo(f"\nFiles will be saved to:")
        click.echo(f"{downloads_dir}\n")

        try:
            choice = click.prompt("Enter number to download (0 to cancel)", type=int, default=0)

            if choice == 0:
                click.echo("Cancelled.")
                return

            if choice < 1 or choice > len(menu_options):
                click.echo("Invalid selection.")
                return

            selected_data = menu_options[choice - 1]['data']

        except (KeyboardInterrupt, EOFError):
            click.echo("\nCancelled.")
            return
        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            return

        # Process selection (selected_data already set above)
        if not selected_data:
            click.echo("Invalid selection.")
            return

        # Prepare download list
        files_to_download = []

        if selected_data['type'] == 'category':
            # Download all files in category
            files_to_download = selected_data['files']
            click.echo(f"\nDownloading {len(files_to_download)} files...")
        elif selected_data['type'] == 'file':
            # Download file(s) - can be a list
            files_to_download = selected_data['files']
            click.echo(f"\nDownloading {len(files_to_download)} file(s)...")

        # Create output directory if needed
        downloads_dir.mkdir(parents=True, exist_ok=True)

        # Download files
        success_count = 0
        for file_info in files_to_download:
            filename = file_info['filename']
            url = file_info['url']
            output_path = downloads_dir / filename

            try:
                click.echo(f"  Downloading {filename}...")
                response = requests.get(url, timeout=30)
                response.raise_for_status()

                with open(output_path, 'wb') as f:
                    f.write(response.content)

                file_size = len(response.content)
                size_mb = file_size / (1024 * 1024)
                if size_mb >= 1:
                    size_str = f"{size_mb:.1f} MB"
                else:
                    size_str = f"{file_size / 1024:.1f} KB"

                click.echo(f"    Saved to {output_path} ({size_str})")
                success_count += 1

            except Exception as e:
                click.echo(f"    Error downloading {filename}: {e}", err=True)

        click.echo(f"\nDownloaded {success_count} of {len(files_to_download)} files successfully.")

    except (ConnectionError, TimeoutError, RuntimeError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("text")
@click.option("--selector", "-s", default=None, help="CSS selector of element to type into")
def send(text, selector):
    """
    Send text to the browser by typing it character by character.

    Types the given text into the currently focused input field,
    or into a specific element if --selector is provided.

    Examples:
        zen send "Hello World"
        zen send "test@example.com" --selector "input[type=email]"
    """
    client = BridgeClient()

    if not client.is_alive():
        click.echo("Error: Bridge server is not running. Start it with: zen server start", err=True)
        sys.exit(1)

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
        result = client.execute(focus_code, timeout=60.0)
        if not result.get("ok") or result.get("result", {}).get("error"):
            error = result.get("error") or result.get("result", {}).get("error", "Unknown error")
            click.echo(f"Error focusing element: {error}", err=True)
            sys.exit(1)

    # Load and execute the send_keys script
    script_path = Path(__file__).parent / "scripts" / "send_keys.js"
    with open(script_path) as f:
        script = f.read()

    # Replace placeholder with properly escaped text
    # Escape quotes and backslashes for JavaScript
    escaped_text = text.replace('\\', '\\\\').replace('"', '\\"').replace("'", "\\'")
    code = script.replace('TEXT_PLACEHOLDER', f'"{escaped_text}"')

    try:
        result = client.execute(code, timeout=60.0)

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


@cli.command()
@click.argument("selector", required=False)
def inspect(selector):
    """
    Select an element and show its details.

    If no selector is provided, shows details of the currently selected element.

    Examples:
        zen inspect "h1"              # Select and show details
        zen inspect "#header"
        zen inspect ".main-content"
        zen inspect                   # Show currently selected element
    """
    client = BridgeClient()

    if not client.is_alive():
        click.echo("Error: Bridge server is not running. Start it with: zen server start", err=True)
        sys.exit(1)

    # If no selector provided, just show the currently marked element
    if not selector:
        # Redirect to 'inspected' command
        return inspected.callback()

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
        result = client.execute(mark_code, timeout=60.0)

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
        return inspected.callback()

    except (ConnectionError, TimeoutError, RuntimeError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
def inspected():
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
    client = BridgeClient()

    if not client.is_alive():
        click.echo("Error: Bridge server is not running. Start it with: zen server start", err=True)
        sys.exit(1)

    # Load the get_inspected.js script
    script_path = os.path.join(os.path.dirname(__file__), 'scripts', 'get_inspected.js')

    try:
        with open(script_path, 'r') as f:
            code = f.read()
    except FileNotFoundError:
        click.echo(f"Error: Script not found: {script_path}", err=True)
        sys.exit(1)

    try:
        result = client.execute(code, timeout=60.0)

        if not result.get("ok"):
            click.echo(f"Error: {result.get('error')}", err=True)
            sys.exit(1)

        response = result.get("result", {})
        if response.get("error"):
            click.echo(f"Error: {response['error']}", err=True)
            if response.get("hint"):
                click.echo(f"Hint: {response['hint']}", err=True)
            sys.exit(1)

        # Display info
        click.echo(f"Tag:      <{response['tag']}>")
        click.echo(f"Selector: {response['selector']}")

        if response.get('parentTag'):
            click.echo(f"Parent:   <{response['parentTag']}>")

        if response.get('id'):
            click.echo(f"ID:       {response['id']}")

        if response.get('classes') and len(response['classes']) > 0:
            click.echo(f"Classes:  {', '.join(response['classes'])}")

        if response.get('textContent'):
            text = response['textContent']
            if len(text) > 60:
                text = text[:60] + '...'
            click.echo(f"Text:     {text}")

        # Dimensions
        dim = response['dimensions']
        click.echo(f"\nDimensions:")
        click.echo(f"  Position: x={dim['left']}, y={dim['top']}")
        click.echo(f"  Size:     {dim['width']}×{dim['height']}px")
        click.echo(f"  Bounds:   top={dim['top']}, right={dim['right']}, bottom={dim['bottom']}, left={dim['left']}")

        # Visibility
        vis = response.get('visibilityDetails', {})
        click.echo(f"\nVisibility:")
        click.echo(f"  Visible:     {'Yes' if response.get('visible') else 'No'}")
        click.echo(f"  In viewport: {'Yes' if vis.get('inViewport') else 'No'}")
        if vis.get('displayNone'):
            click.echo(f"  Issue:       display: none")
        if vis.get('visibilityHidden'):
            click.echo(f"  Issue:       visibility: hidden")
        if vis.get('opacityZero'):
            click.echo(f"  Issue:       opacity: 0")
        if vis.get('offScreen'):
            click.echo(f"  Issue:       positioned off-screen")

        # Accessibility
        a11y = response.get('accessibility', {})
        click.echo(f"\nAccessibility:")
        click.echo(f"  Role:            {a11y.get('role', 'N/A')}")

        # Accessible Name (computed)
        accessible_name = a11y.get('accessibleName', '')
        name_source = a11y.get('accessibleNameSource', 'none')
        if accessible_name:
            # Truncate if too long
            display_name = accessible_name if len(accessible_name) <= 50 else accessible_name[:50] + '...'
            click.echo(f"  Accessible Name: \"{display_name}\"")
            click.echo(f"  Name computed from: {name_source}")
        else:
            click.echo(f"  Accessible Name: (none)")
            if name_source == 'missing alt attribute':
                click.echo(f"  ⚠️  Warning: Image missing alt attribute")
            elif name_source == 'none':
                click.echo(f"  ⚠️  Warning: No accessible name found")

        if a11y.get('ariaLabel'):
            click.echo(f"  ARIA Label:      {a11y['ariaLabel']}")
        if a11y.get('ariaLabelledBy'):
            click.echo(f"  ARIA LabelledBy: {a11y['ariaLabelledBy']}")
        if a11y.get('alt'):
            click.echo(f"  Alt text:        {a11y['alt']}")
        click.echo(f"  Focusable:       {'Yes' if a11y.get('focusable') else 'No'}")
        if a11y.get('tabIndex') is not None:
            click.echo(f"  Tab index:       {a11y['tabIndex']}")
        if a11y.get('disabled'):
            click.echo(f"  Disabled:        Yes")
        if a11y.get('ariaHidden'):
            click.echo(f"  ARIA Hidden:     {a11y['ariaHidden']}")

        # Semantic info
        semantic = response.get('semantic', {})
        if semantic.get('isInteractive') or semantic.get('isFormElement') or semantic.get('isLandmark'):
            click.echo(f"\nSemantic:")
            if semantic.get('isInteractive'):
                click.echo(f"  Interactive element")
            if semantic.get('isFormElement'):
                click.echo(f"  Form element")
            if semantic.get('isLandmark'):
                click.echo(f"  Landmark element")
            if semantic.get('hasClickHandler'):
                click.echo(f"  Has click handler")

        # Children
        click.echo(f"\nStructure:")
        click.echo(f"  Children: {response.get('childCount', 0)}")

        # Styles
        click.echo(f"\nStyles:")
        for key, value in response['styles'].items():
            click.echo(f"  {key}: {value}")

        # Attributes
        if response.get('attributes'):
            click.echo(f"\nAttributes:")
            for key, value in response['attributes'].items():
                if len(str(value)) > 50:
                    value = str(value)[:50] + '...'
                click.echo(f"  {key}: {value}")

    except (ConnectionError, TimeoutError, RuntimeError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command(name="click")
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


@cli.command(name="double-click")
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


@cli.command(name="doubleclick")
@click.argument("selector", required=False, default="$0")
def doubleclick_alias(selector):
    """Alias for double-click command."""
    _perform_click(selector, "dblclick")


@cli.command(name="right-click")
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


@cli.command(name="rightclick")
@click.argument("selector", required=False, default="$0")
def rightclick_alias(selector):
    """Alias for right-click command."""
    _perform_click(selector, "contextmenu")


def _perform_click(selector, click_type):
    """Helper function to perform click actions."""
    client = BridgeClient()

    if not client.is_alive():
        click.echo("Error: Bridge server is not running. Start it with: zen server start", err=True)
        sys.exit(1)

    # Load the click script
    script_path = os.path.join(os.path.dirname(__file__), 'scripts', 'click_element.js')

    try:
        with open(script_path, 'r') as f:
            script = f.read()
    except FileNotFoundError:
        click.echo(f"Error: Script not found: {script_path}", err=True)
        sys.exit(1)

    # Replace placeholders
    escaped_selector = selector.replace('\\', '\\\\').replace('"', '\\"').replace("'", "\\'")
    code = script.replace('SELECTOR_PLACEHOLDER', escaped_selector)
    code = code.replace('CLICK_TYPE_PLACEHOLDER', click_type)

    try:
        result = client.execute(code, timeout=60.0)

        if not result.get("ok"):
            click.echo(f"Error: {result.get('error')}", err=True)
            sys.exit(1)

        response = result.get("result", {})

        if response.get("error"):
            click.echo(f"Error: {response['error']}", err=True)
            sys.exit(1)

        # Show confirmation
        action_name = {
            'click': 'Clicked',
            'dblclick': 'Double-clicked',
            'contextmenu': 'Right-clicked'
        }.get(click_type, 'Clicked')

        click.echo(f"{action_name}: {response.get('element', 'element')}")
        pos = response.get('position', {})
        if pos:
            click.echo(f"Position: x={pos.get('x')}, y={pos.get('y')}")

    except (ConnectionError, TimeoutError, RuntimeError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
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
    client = BridgeClient()

    if not client.is_alive():
        click.echo("Error: Bridge server is not running. Start it with: zen server start", err=True)
        sys.exit(1)

    # Determine wait type
    if hidden:
        wait_type = 'hidden'
    elif visible:
        wait_type = 'visible'
    elif text:
        wait_type = 'text'
    else:
        wait_type = 'exists'

    # Load the wait script
    script_path = os.path.join(os.path.dirname(__file__), 'scripts', 'wait_for.js')

    try:
        with open(script_path, 'r') as f:
            script = f.read()
    except FileNotFoundError:
        click.echo(f"Error: Script not found: {script_path}", err=True)
        sys.exit(1)

    # Replace placeholders
    escaped_selector = selector.replace('\\', '\\\\').replace('"', '\\"').replace("'", "\\'")
    escaped_text = (text or '').replace('\\', '\\\\').replace('"', '\\"').replace("'", "\\'")
    timeout_ms = timeout * 1000

    code = script.replace('SELECTOR_PLACEHOLDER', escaped_selector)
    code = code.replace('WAIT_TYPE_PLACEHOLDER', wait_type)
    code = code.replace('TEXT_PLACEHOLDER', escaped_text)
    code = code.replace('TIMEOUT_PLACEHOLDER', str(timeout_ms))

    # Show waiting message
    wait_msg = {
        'exists': f'Waiting for element: {selector}',
        'visible': f'Waiting for element to be visible: {selector}',
        'hidden': f'Waiting for element to be hidden: {selector}',
        'text': f'Waiting for element to contain "{text}": {selector}'
    }.get(wait_type, f'Waiting for: {selector}')

    click.echo(wait_msg)

    try:
        # Use longer timeout for the request (add 5 seconds buffer)
        result = client.execute(code, timeout=timeout + 5)

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
        waited_sec = response.get('waited', 0) / 1000
        click.echo(f"✓ {response.get('status', 'Condition met')}")
        if response.get('element'):
            click.echo(f"  Element: {response['element']}")
        click.echo(f"  Waited: {waited_sec:.2f}s")

    except (ConnectionError, TimeoutError, RuntimeError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.group()
def cookies():
    """Manage browser cookies."""
    pass


@cookies.command(name="list")
def cookies_list():
    """
    List all cookies for the current page.

    Example:
        zen cookies list
    """
    _execute_cookie_action('list')


@cookies.command(name="get")
@click.argument("name")
def cookies_get(name):
    """
    Get the value of a specific cookie.

    Example:
        zen cookies get session_id
    """
    _execute_cookie_action('get', cookie_name=name)


@cookies.command(name="set")
@click.argument("name")
@click.argument("value")
@click.option("--max-age", type=int, help="Max age in seconds")
@click.option("--expires", type=str, help="Expiration date (e.g., 'Wed, 21 Oct 2025 07:28:00 GMT')")
@click.option("--path", type=str, default="/", help="Cookie path (default: /)")
@click.option("--domain", type=str, help="Cookie domain")
@click.option("--secure", is_flag=True, help="Secure flag (HTTPS only)")
@click.option("--same-site", type=click.Choice(['Strict', 'Lax', 'None'], case_sensitive=False), help="SameSite attribute")
def cookies_set(name, value, max_age, expires, path, domain, secure, same_site):
    """
    Set a cookie.

    Examples:
        zen cookies set session_id abc123
        zen cookies set token xyz --max-age 3600
        zen cookies set user_pref dark --path / --secure
    """
    options = {
        'path': path
    }
    if max_age:
        options['maxAge'] = max_age
    if expires:
        options['expires'] = expires
    if domain:
        options['domain'] = domain
    if secure:
        options['secure'] = True
    if same_site:
        options['sameSite'] = same_site

    _execute_cookie_action('set', cookie_name=name, cookie_value=value, options=options)


@cookies.command(name="delete")
@click.argument("name")
def cookies_delete(name):
    """
    Delete a specific cookie.

    Example:
        zen cookies delete session_id
    """
    _execute_cookie_action('delete', cookie_name=name)


@cookies.command(name="clear")
def cookies_clear():
    """
    Clear all cookies for the current page.

    Example:
        zen cookies clear
    """
    _execute_cookie_action('clear')


def _execute_cookie_action(action, cookie_name='', cookie_value='', options=None):
    """Helper function to execute cookie actions."""
    client = BridgeClient()

    if not client.is_alive():
        click.echo("Error: Bridge server is not running. Start it with: zen server start", err=True)
        sys.exit(1)

    # Load the cookies script
    script_path = os.path.join(os.path.dirname(__file__), 'scripts', 'cookies.js')

    try:
        with open(script_path, 'r') as f:
            script = f.read()
    except FileNotFoundError:
        click.echo(f"Error: Script not found: {script_path}", err=True)
        sys.exit(1)

    # Replace placeholders
    options_json = json.dumps(options if options else {})
    code = script.replace('ACTION_PLACEHOLDER', action)
    code = code.replace('NAME_PLACEHOLDER', cookie_name)
    code = code.replace('VALUE_PLACEHOLDER', cookie_value)
    code = code.replace('OPTIONS_PLACEHOLDER', options_json)

    try:
        result = client.execute(code, timeout=60.0)

        if not result.get("ok"):
            click.echo(f"Error: {result.get('error')}", err=True)
            sys.exit(1)

        response = result.get("result", {})

        if response.get("error"):
            click.echo(f"Error: {response['error']}", err=True)
            sys.exit(1)

        # Display results based on action
        if action == 'list':
            cookies_dict = response.get('cookies', {})
            count = response.get('count', 0)

            if count == 0:
                click.echo("No cookies found")
            else:
                click.echo(f"Cookies ({count}):\n")
                for name, value in cookies_dict.items():
                    # Truncate long values
                    display_value = value if len(value) <= 60 else value[:60] + '...'
                    click.echo(f"  {name} = {display_value}")

        elif action == 'get':
            name = response.get('name')
            value = response.get('value')
            exists = response.get('exists')

            if exists:
                click.echo(f"{name} = {value}")
            else:
                click.echo(f"Cookie not found: {name}", err=True)
                sys.exit(1)

        elif action == 'set':
            click.echo(f"✓ Cookie set: {response.get('name')} = {response.get('value')}")

        elif action == 'delete':
            click.echo(f"✓ Cookie deleted: {response.get('name')}")

        elif action == 'clear':
            deleted = response.get('deleted', 0)
            click.echo(f"✓ Cleared {deleted} cookie(s)")

    except (ConnectionError, TimeoutError, RuntimeError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--raw", is_flag=True, help="Output only the text without formatting")
def selected(raw):
    """
    Get the current text selection in the browser.

    Returns the selected text along with metadata like position and container element.

    Examples:
        # Get selection with metadata:
        zen selected

        # Get just the raw text (no formatting):
        zen selected --raw
    """
    client = BridgeClient()

    if not client.is_alive():
        click.echo("Error: Bridge server is not running. Start it with: zen server start", err=True)
        sys.exit(1)

    # Load the get_selection.js script
    script_path = os.path.join(os.path.dirname(__file__), 'scripts', 'get_selection.js')

    try:
        with open(script_path, 'r') as f:
            code = f.read()
    except FileNotFoundError:
        click.echo(f"Error: Script not found: {script_path}", err=True)
        sys.exit(1)

    try:
        result = client.execute(code, timeout=60.0)

        if not result.get("ok"):
            click.echo(f"Error: {result.get('error')}", err=True)
            sys.exit(1)

        response = result.get("result", {})

        if not response.get('hasSelection'):
            if not raw:
                click.echo("No text selected")
                click.echo("Hint: Select some text in the browser first, then run: zen selected")
            sys.exit(0)

        text = response.get('text', '')

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
        pos = response.get('position', {})
        click.echo(f"\nPosition:")
        click.echo(f"  x={pos.get('x')}, y={pos.get('y')}")
        click.echo(f"  Size: {pos.get('width')}×{pos.get('height')}px")

        # Container element
        container = response.get('container', {})
        if container.get('tag'):
            click.echo(f"\nContainer:")
            click.echo(f"  Tag:   <{container['tag']}>")
            if container.get('id'):
                click.echo(f"  ID:    {container['id']}")
            if container.get('class'):
                click.echo(f"  Class: {container['class']}")

        # HTML if different from text
        html = response.get('html', '')
        if html and html.strip() != text.strip():
            click.echo(f"\nHTML:")
            if len(html) <= 200:
                click.echo(f"  {html}")
            else:
                click.echo(f"  {html[:200]}...")

    except (ConnectionError, TimeoutError, RuntimeError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--selector", "-s", required=True, help="CSS selector of element to screenshot (or use $0 for inspected element)")
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
    import base64
    from datetime import datetime

    client = BridgeClient()

    if not client.is_alive():
        click.echo("Error: Bridge server is not running. Start it with: zen server start", err=True)
        sys.exit(1)

    # Load screenshot script
    script_path = Path(__file__).parent / "scripts" / "screenshot_element.js"
    with open(script_path) as f:
        script = f.read()

    # Replace selector placeholder
    escaped_selector = selector.replace('\\', '\\\\').replace('"', '\\"').replace("'", "\\'")
    code = script.replace('SELECTOR_PLACEHOLDER', f'"{escaped_selector}"')

    try:
        click.echo(f"Capturing element: {selector}")
        result = client.execute(code, timeout=60.0)

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
        if ',' in data_url:
            base64_data = data_url.split(',', 1)[1]
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
        with open(output_path, 'wb') as f:
            f.write(image_data)

        size_kb = len(image_data) / 1024
        click.echo(f"Screenshot saved: {output_path}")
        click.echo(f"Size: {response.get('width')}x{response.get('height')}px ({size_kb:.1f} KB)")

    except (ConnectionError, TimeoutError, RuntimeError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.group()
def watch():
    """Watch browser events in real-time."""
    pass


@watch.command()
def input():
    """
    Watch keyboard input in real-time.

    Streams all keyboard events from the browser to the terminal.
    Press Ctrl+C to stop watching.

    Example:
        zen watch input
    """
    client = BridgeClient()

    if not client.is_alive():
        click.echo("Error: Bridge server is not running. Start it with: zen server start", err=True)
        sys.exit(1)

    # Start watching keyboard
    script_path = Path(__file__).parent / "scripts" / "watch_keyboard.js"
    with open(script_path) as f:
        watch_code = f.read()

    try:
        result = client.execute(watch_code, timeout=60.0)

        if not result.get("ok"):
            click.echo(f"Error starting keyboard watcher: {result.get('error')}", err=True)
            sys.exit(1)

        click.echo("Watching keyboard input... (Press Ctrl+C to stop)")
        click.echo("")

        # Now continuously poll for keyboard events
        # We'll use a loop that executes code to check for new events
        poll_code = """
        (function() {
            if (!window.__ZEN_KEYBOARD_EVENTS__) {
                window.__ZEN_KEYBOARD_EVENTS__ = [];
            }
            const events = window.__ZEN_KEYBOARD_EVENTS__.splice(0);
            return events;
        })()
        """

        # Set up signal handler for Ctrl+C
        def stop_watching(sig, frame):
            cleanup_code = """
            (function() {
                const watchId = '__ZEN_KEYBOARD_WATCH__';
                if (window[watchId]) {
                    document.removeEventListener('keydown', window[watchId], true);
                    delete window[watchId];
                }
                if (window.__ZEN_KEYBOARD_EVENTS__) {
                    delete window.__ZEN_KEYBOARD_EVENTS__;
                }
                return 'Keyboard watcher stopped';
            })()
            """
            client.execute(cleanup_code, timeout=2.0)
            click.echo("\n\nStopped watching keyboard input.")
            sys.exit(0)

        signal.signal(signal.SIGINT, stop_watching)

        # Poll for events
        import time
        while True:
            result = client.execute(poll_code, timeout=1.0)
            if result.get("ok"):
                events = result.get("result", [])
                for event in events:
                    click.echo(event, nl=False)
                    sys.stdout.flush()

            time.sleep(0.1)  # Poll every 100ms

    except Exception as e:
        click.echo(f"\nError: {e}", err=True)
        sys.exit(1)


@cli.command()
def control():
    """
    Control the browser remotely from your terminal.

    All keyboard input from your terminal will be sent directly to the browser,
    allowing you to navigate, type, and interact with the page remotely.

    Supports:
    - Regular text input
    - Special keys (arrows, Enter, Tab, Escape, etc.)
    - Modifier keys (Ctrl, Alt, Shift, Cmd)

    Press Ctrl+D to exit control mode.

    Example:
        zen control
    """
    import sys
    import tty
    import termios
    import select

    client = BridgeClient()

    if not client.is_alive():
        click.echo("Error: Bridge server is not running. Start it with: zen server start", err=True)
        sys.exit(1)

    # Load configuration
    control_config = zen_config.get_control_config()
    config_json = json.dumps(control_config)

    # Load control script
    script_path = Path(__file__).parent / "scripts" / "control.js"

    try:
        with open(script_path) as f:
            script_template = f.read()
    except FileNotFoundError:
        click.echo(f"Error: Script not found: {script_path}", err=True)
        sys.exit(1)

    # Start control mode
    start_code = script_template.replace('ACTION_PLACEHOLDER', 'start')
    start_code = start_code.replace('KEY_DATA_PLACEHOLDER', '{}')
    start_code = start_code.replace('CONFIG_PLACEHOLDER', config_json)

    try:
        result = client.execute(start_code, timeout=60.0)

        if not result.get("ok"):
            click.echo(f"Error starting control mode: {result.get('error')}", err=True)
            sys.exit(1)

        response = result.get("result", {})
        title = response.get('title', 'Unknown')

        click.echo(f"Now controlling: {title}")
        click.echo("Press Ctrl+D to exit\n")

        # Save terminal settings
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)

        try:
            # Put terminal in raw mode
            tty.setraw(fd)

            while True:
                # Check for notifications before reading input
                # Use select with timeout to allow polling
                readable, _, _ = select.select([sys.stdin], [], [], 0.1)  # 100ms timeout

                if not readable:
                    # No input available, check for notifications
                    try:
                        import requests
                        resp = requests.get(f'http://{client.host}:{client.port}/notifications', timeout=0.5)
                        if resp.status_code == 200:
                            data = resp.json()
                            if data.get('ok') and data.get('notifications'):
                                for notification in data['notifications']:
                                    if notification['type'] == 'refocus':
                                        message = notification['message']
                                        sys.stderr.write(f"\r\n{message}\r\n")
                                        sys.stderr.flush()
                                        # Speak if speak-all is enabled
                                        if control_config.get('speak-all'):
                                            try:
                                                subprocess.run(['say', message], check=False, timeout=5)
                                            except Exception:
                                                pass
                    except Exception:
                        # Silently ignore notification check errors
                        pass
                    continue

                # Read one character
                char = sys.stdin.read(1)

                # Handle Ctrl+D (EOF)
                if char == '\x04':  # Ctrl+D
                    break

                # Map character to key data
                key_data = {}

                # Special key mappings
                if char == '\x1b':  # Escape sequence
                    # Read next characters for arrow keys, etc.
                    next_char = sys.stdin.read(1)
                    if next_char == '[':
                        arrow = sys.stdin.read(1)
                        if arrow == 'A':
                            key_data = {'key': 'ArrowUp', 'code': 'ArrowUp'}
                        elif arrow == 'B':
                            key_data = {'key': 'ArrowDown', 'code': 'ArrowDown'}
                        elif arrow == 'C':
                            key_data = {'key': 'ArrowRight', 'code': 'ArrowRight'}
                        elif arrow == 'D':
                            key_data = {'key': 'ArrowLeft', 'code': 'ArrowLeft'}
                        elif arrow == 'Z':
                            # Shift+Tab
                            key_data = {'key': 'Tab', 'code': 'Tab', 'shift': True}
                        else:
                            # Unknown sequence, skip
                            continue
                    else:
                        # Just Escape key
                        key_data = {'key': 'Escape', 'code': 'Escape'}
                elif char == '\r' or char == '\n':
                    key_data = {'key': 'Enter', 'code': 'Enter'}
                elif char == '\t':
                    key_data = {'key': 'Tab', 'code': 'Tab'}
                elif char == '\x7f':  # Backspace
                    key_data = {'key': 'Backspace', 'code': 'Backspace'}
                elif ord(char) < 32:  # Control character
                    # Handle Ctrl+letter combinations
                    letter = chr(ord(char) + 96)
                    key_data = {'key': letter, 'code': f'Key{letter.upper()}', 'ctrl': True}
                else:
                    # Regular character
                    key_data = {'key': char, 'code': f'Key{char.upper()}' if char.isalpha() else ''}

                # Send key to browser
                send_code = script_template.replace('ACTION_PLACEHOLDER', 'send')
                send_code = send_code.replace('KEY_DATA_PLACEHOLDER', json.dumps(key_data))
                send_code = send_code.replace('CONFIG_PLACEHOLDER', config_json)

                result = client.execute(send_code, timeout=60.0)

                # Check if control needs reinitialization (e.g., after page reload)
                # The browser returns {ok: true, result: {ok: false, needsRestart: true}}
                if result.get("ok"):
                    response = result.get("result", {})
                    if isinstance(response, dict) and response.get("needsRestart"):
                        # Auto-restart control mode
                        # Write directly to stderr (works in raw mode)
                        sys.stderr.write("\r\n🔄 Reinitializing after navigation...\r\n")
                        sys.stderr.flush()

                        restart_result = client.execute(start_code, timeout=60.0)
                        if control_config.get('verbose-logging'):
                            sys.stderr.write(f"[CLI] Restart: {restart_result.get('ok')}\r\n")
                            sys.stderr.flush()

                        # Retry the key send
                        result = client.execute(send_code, timeout=60.0)

                        if result.get("ok"):
                            sys.stderr.write("✅ Control restored!\r\n")
                            sys.stderr.flush()

                if result.get("ok"):
                    # Check if we should speak the accessible name
                    response = result.get("result", {})
                    if control_config.get('speak-name') and 'accessibleName' in response:
                        accessible_name = response.get('accessibleName', '').strip()
                        role = response.get('role', '')

                        if accessible_name:
                            # Build the text to speak
                            speak_text = accessible_name

                            # Optionally announce role
                            if control_config.get('announce-role') and role:
                                speak_text = f"{role}, {speak_text}"

                            # Use macOS say command
                            try:
                                subprocess.run(['say', speak_text], check=False, timeout=5)
                            except Exception:
                                # Silently ignore if say command fails
                                pass

                    # Display verbose messages if enabled
                    if control_config.get('verbose'):
                        # Check for opening message (when pressing Enter on links/buttons)
                        if 'message' in response:
                            message = response['message']
                            sys.stderr.write(f"\r\n{message}\r\n")
                            sys.stderr.flush()
                            if control_config.get('speak-all'):
                                try:
                                    subprocess.run(['say', message], check=False, timeout=5)
                                except Exception:
                                    pass

                        # Check for "opened" message (right after click)
                        if 'openedMessage' in response:
                            message = response['openedMessage']
                            sys.stderr.write(f"{message}\r\n")
                            sys.stderr.flush()
                            if control_config.get('speak-all'):
                                try:
                                    subprocess.run(['say', message], check=False, timeout=5)
                                except Exception:
                                    pass

                        # Check for refocus message (after page navigation)
                        if 'refocusMessage' in response:
                            message = response['refocusMessage']
                            sys.stderr.write(f"{message}\r\n")
                            sys.stderr.flush()
                            if control_config.get('speak-all'):
                                try:
                                    subprocess.run(['say', message], check=False, timeout=5)
                                except Exception:
                                    pass
                else:
                    # Silently ignore errors, keep going
                    pass

        finally:
            # Restore terminal settings
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

            # Stop control mode
            stop_code = script_template.replace('ACTION_PLACEHOLDER', 'stop')
            stop_code = stop_code.replace('KEY_DATA_PLACEHOLDER', '{}')
            stop_code = stop_code.replace('CONFIG_PLACEHOLDER', config_json)
            client.execute(stop_code, timeout=2.0)

            click.echo("\n\nControl mode ended.")

    except Exception as e:
        # Make sure to restore terminal
        try:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        except:
            pass
        click.echo(f"\nError: {e}", err=True)
        sys.exit(1)


@watch.command()
def all():
    """
    Watch all user interactions - keyboard, focus, and accessible names.

    Features:
    - Groups regular typing on single lines
    - Shows special keys (Tab, Enter, arrows, modifiers) on separate lines
    - Displays accessible name when tabbing to focusable elements

    Press Ctrl+C to stop watching.

    Example:
        zen watch all
    """
    client = BridgeClient()

    if not client.is_alive():
        click.echo("Error: Bridge server is not running. Start it with: zen server start", err=True)
        sys.exit(1)

    # Load watch_all script
    script_path = Path(__file__).parent / "scripts" / "watch_all.js"

    try:
        with open(script_path) as f:
            script_template = f.read()
    except FileNotFoundError:
        click.echo(f"Error: Script not found: {script_path}", err=True)
        sys.exit(1)

    # Start watching
    start_code = script_template.replace('ACTION_PLACEHOLDER', 'start')

    try:
        result = client.execute(start_code, timeout=60.0)

        if not result.get("ok"):
            click.echo(f"Error starting watcher: {result.get('error')}", err=True)
            sys.exit(1)

        click.echo("Watching all interactions... (Press Ctrl+C to stop)")
        click.echo("")

        # Poll code
        poll_code = script_template.replace('ACTION_PLACEHOLDER', 'poll')

        # Cleanup code
        stop_code = script_template.replace('ACTION_PLACEHOLDER', 'stop')

        # Set up signal handler for Ctrl+C
        def stop_watching(sig, frame):
            client.execute(stop_code, timeout=2.0)
            click.echo("\n\nStopped watching.")
            sys.exit(0)

        signal.signal(signal.SIGINT, stop_watching)

        # Poll for events
        import time
        while True:
            result = client.execute(poll_code, timeout=1.0)
            if result.get("ok"):
                response = result.get("result", {})
                if response.get("hasEvents"):
                    events = response.get("events", [])
                    for event in events:
                        event_type = event.get('type')

                        if event_type == 'text':
                            # Regular text - print on same line
                            click.echo(event.get('content', ''))

                        elif event_type == 'key':
                            # Special key - print with brackets
                            click.echo(f"[{event.get('content', '')}]")

                        elif event_type == 'focus':
                            # Focus change - show accessible name
                            accessible_name = event.get('accessibleName', '')
                            element = event.get('element', '')
                            role = event.get('role', '')

                            if accessible_name and accessible_name != element:
                                click.echo(f"→ Focus: {accessible_name} {element}")
                            else:
                                click.echo(f"→ Focus: {element}")

            time.sleep(0.1)  # Poll every 100ms

    except Exception as e:
        click.echo(f"\nError: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--format", type=click.Choice(["summary", "full"]), default="summary", help="Output format (summary or full article)")
def summarize(format):
    """
    Summarize the current article using AI.

    Extracts article content using Mozilla Readability and generates
    a concise summary using the mods command.

    Examples:
        zen summarize                    # Get AI summary
        zen summarize --format full      # Show full extracted article
    """
    client = BridgeClient()

    if not client.is_alive():
        click.echo("Error: Bridge server is not running. Start it with: zen server start", err=True)
        sys.exit(1)

    # Check if mods is available
    if format == "summary":
        try:
            subprocess.run(["mods", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            click.echo("Error: 'mods' command not found. Please install mods first.", err=True)
            click.echo("Visit: https://github.com/charmbracelet/mods", err=True)
            sys.exit(1)

    # Load and execute the extract_article script
    script_path = Path(__file__).parent / "scripts" / "extract_article.js"

    if not script_path.exists():
        click.echo(f"Error: Script not found: {script_path}", err=True)
        sys.exit(1)

    try:
        with open(script_path) as f:
            script = f.read()

        click.echo("Extracting article content...", err=True)
        result = client.execute(script, timeout=30.0)

        if not result.get("ok"):
            click.echo(f"Error: {result.get('error')}", err=True)
            sys.exit(1)

        article = result.get("result", {})

        if article.get("error"):
            click.echo(f"Error: {article['error']}", err=True)
            sys.exit(1)

        title = article.get("title", "Untitled")
        content = article.get("content", "")
        byline = article.get("byline", "")

        if not content:
            click.echo("Error: No content extracted. This page may not be an article.", err=True)
            sys.exit(1)

        # If full format, just show the extracted article
        if format == "full":
            click.echo(f"Title: {title}")
            if byline:
                click.echo(f"By: {byline}")
            click.echo("")
            click.echo(content)
            return

        # Generate summary using mods
        click.echo(f"Generating summary for: {title}", err=True)

        # Read the prompt file
        prompt_path = Path(__file__).parent.parent / "prompts" / "summary.prompt"

        if not prompt_path.exists():
            click.echo(f"Error: Prompt file not found: {prompt_path}", err=True)
            sys.exit(1)

        with open(prompt_path) as f:
            prompt = f.read().strip()

        # Prepare the input for mods
        full_input = f"{prompt}\n\nTitle: {title}\n\n{content}"

        # Call mods
        try:
            result = subprocess.run(
                ["mods"],
                input=full_input,
                text=True,
                capture_output=True,
                check=True
            )

            if byline:
                click.echo(f"By: {byline}")
                click.echo("")
            click.echo(result.stdout)

        except subprocess.CalledProcessError as e:
            click.echo(f"Error calling mods: {e}", err=True)
            if e.stderr:
                click.echo(e.stderr, err=True)
            sys.exit(1)

    except (ConnectionError, TimeoutError, RuntimeError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
