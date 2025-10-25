#!/usr/bin/env python3
"""
Zen Browser Bridge CLI - Execute JavaScript in your browser from the command line.
"""
import sys
import json
import click
import subprocess
import signal
from pathlib import Path
from .client import BridgeClient
from . import __version__


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
            click.echo(f"URL:      {data.get('url', 'N/A')}")
            click.echo(f"Title:    {data.get('title', 'N/A')}")
            click.echo(f"Domain:   {data.get('domain', 'N/A')}")
            click.echo(f"Protocol: {data.get('protocol', 'N/A')}")
            click.echo(f"State:    {data.get('readyState', 'N/A')}")
            click.echo(f"Size:     {data.get('width', 'N/A')}x{data.get('height', 'N/A')}")
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
        click.echo(f"Starting bridge server in background on port {port}...")
        subprocess.Popen(
            [sys.executable, "-m", "zen.bridge"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        # Wait a bit and check if it started
        import time
        time.sleep(0.5)
        if client.is_alive():
            click.echo("Server started successfully")
        else:
            click.echo("Failed to start server", err=True)
            sys.exit(1)
    else:
        # Run in foreground
        from .bridge import start_server
        try:
            start_server(port=port)
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
    click.echo("For daemon mode, use: pkill -f 'zen.bridge'")


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
            # Download single file
            files_to_download = [selected_data]
            click.echo(f"\nDownloading 1 file...")

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


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
