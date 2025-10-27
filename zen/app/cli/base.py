"""
Shared CLI utilities and base classes.

This module provides common functionality used across all CLI command modules:
- Output formatting
- Language detection
- Custom Click group classes
- Common imports and constants
"""

from __future__ import annotations

import json
from typing import Any

import click

from zen import config as zen_config
from zen.services.ai_integration import get_ai_service


# Save built-in functions before they get shadowed by Click commands
builtin_open = open
builtin_next = next


def format_output(result: dict[str, Any], format_type: str = "auto") -> str:
    """
    Format execution result for display.

    Args:
        result: Execution result dictionary with 'ok', 'result', 'error' keys
        format_type: Output format - "json", "raw", or "auto" (default)

    Returns:
        Formatted output string
    """
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


def get_ai_language(
    language_override: str | None = None,
    page_lang: str | None = None,
) -> str | None:
    """
    Determine the language for AI operations.

    This is a convenience wrapper around AIIntegrationService.get_target_language()
    for backward compatibility with existing code.

    Priority:
    1. language_override (from --language flag)
    2. config.json ai-language setting
    3. If "auto", detect from page_lang
    4. Default to None (let AI decide)

    Args:
        language_override: Language code from CLI flag
        page_lang: Detected page language

    Returns:
        Language code (e.g., "en", "nl", "fr") or None
    """
    ai_service = get_ai_service()
    return ai_service.get_target_language(
        language_override=language_override,
        page_lang=page_lang,
    )


class CustomGroup(click.Group):
    """
    Custom Click Group that shows all command options in help.

    This extends Click's default Group class to provide more detailed help
    output, including options for each subcommand.
    """

    def format_help(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        """Format the complete help output."""
        self.format_usage(ctx, formatter)
        self.format_help_text(ctx, formatter)
        self.format_options(ctx, formatter)
        self.format_commands_with_options(ctx, formatter)
        self.format_epilog(ctx, formatter)

    def format_commands_with_options(
        self,
        ctx: click.Context,
        formatter: click.HelpFormatter,
    ) -> None:
        """
        List all commands with their options.

        This provides a more detailed view than the default Click help,
        showing options for each subcommand in the main help output.
        """
        commands = self.list_commands(ctx)

        if len(commands):
            formatter.write_paragraph()
            formatter.write_text("Commands:")
            formatter.write_paragraph()

            for subcommand in commands:
                cmd = self.get_command(ctx, subcommand)
                if cmd is None:
                    continue

                # Write command name and description
                help_text = cmd.get_short_help_str(limit=80)
                formatter.write_text(f"  {subcommand}")
                if help_text:
                    formatter.write_text(f"    {help_text}")

                # Write command options
                params = [p for p in cmd.params if isinstance(p, click.Option)]
                if params:
                    for param in params:
                        opts = ", ".join(param.opts)
                        param_help = param.help or ""
                        default = ""
                        if param.default is not None and not isinstance(param.default, bool):
                            default = f" [default: {param.default}]"
                        formatter.write_text(f"      {opts}  {param_help}{default}")

                formatter.write_paragraph()
