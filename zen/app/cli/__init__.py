"""
Zen Browser Bridge CLI - Main entry point.

This module assembles all CLI commands from individual command modules
and creates the main CLI group with Click.
"""

from __future__ import annotations

import click

from zen import __version__
from zen.app.cli.base import CustomGroup

# Import command modules
from zen.app.cli import cookies as cookies_module
from zen.app.cli import exec as exec_module
from zen.app.cli import extraction as extraction_module
from zen.app.cli import inspection as inspection_module
from zen.app.cli import interaction as interaction_module
from zen.app.cli import navigation as navigation_module
from zen.app.cli import selection as selection_module
from zen.app.cli import server as server_module
from zen.app.cli import util as util_module
from zen.app.cli import watch as watch_module


@click.group(cls=CustomGroup)
@click.version_option(version=__version__)
def cli():
    """Zen Browser Bridge - Execute JavaScript in your browser from the CLI."""
    pass


# ============================================================================
# Register Commands
# ============================================================================

# Execution commands (from exec.py)
cli.add_command(exec_module.eval, name="eval")
cli.add_command(exec_module.exec, name="exec")

# Navigation commands (from navigation.py)
cli.add_command(navigation_module.open, name="open")
cli.add_command(navigation_module.back, name="back")
cli.add_command(navigation_module.forward, name="forward")
cli.add_command(navigation_module.reload, name="reload")
cli.add_command(navigation_module.previous, name="previous")  # hidden alias for back
cli.add_command(navigation_module.next, name="next")  # hidden alias for forward
cli.add_command(navigation_module.refresh, name="refresh")  # hidden alias for reload

# Cookie management commands (from cookies.py)
cli.add_command(cookies_module.cookies, name="cookies")  # group

# Interaction commands (from interaction.py)
cli.add_command(interaction_module.type_text, name="type")
cli.add_command(interaction_module.paste, name="paste")
cli.add_command(interaction_module.send, name="send")  # deprecated, kept for backward compatibility
cli.add_command(interaction_module.click_element, name="click")
cli.add_command(interaction_module.double_click, name="double-click")
cli.add_command(interaction_module.doubleclick_alias, name="doubleclick")  # hidden alias
cli.add_command(interaction_module.right_click, name="right-click")
cli.add_command(interaction_module.rightclick_alias, name="rightclick")  # hidden alias
cli.add_command(interaction_module.wait, name="wait")

# Inspection commands (from inspection.py)
cli.add_command(inspection_module.inspect, name="inspect")
cli.add_command(inspection_module.inspected, name="inspected")
cli.add_command(inspection_module.screenshot, name="screenshot")

# Selection commands (from selection.py)
cli.add_command(selection_module.selection, name="selection")  # group with text/html/markdown subcommands
cli.add_command(selection_module.selected, name="selected")  # deprecated, kept for backward compatibility

# Server management commands (from server.py)
cli.add_command(server_module.server, name="server")  # group

# Content extraction commands (from extraction.py)
cli.add_command(extraction_module.describe, name="describe")
cli.add_command(extraction_module.do, name="do")
cli.add_command(extraction_module.outline, name="outline")
cli.add_command(extraction_module.links, name="links")
cli.add_command(extraction_module.summarize, name="summarize")

# Watch commands (from watch.py)
cli.add_command(watch_module.watch, name="watch")  # group
cli.add_command(watch_module.control, name="control")

# Utility commands (from util.py)
cli.add_command(util_module.info, name="info")
cli.add_command(util_module.repl, name="repl")
cli.add_command(util_module.userscript, name="userscript")
cli.add_command(util_module.download, name="download")


# ============================================================================
# Export main CLI
# ============================================================================

def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()


__all__ = ["cli", "main"]
