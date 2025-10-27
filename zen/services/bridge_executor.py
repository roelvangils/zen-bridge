"""
Bridge Executor Service - Standardized execution flow for browser commands.

This service wraps the BridgeClient to provide:
- Consistent error handling
- Retry logic with exponential backoff
- Result formatting and validation
- Version checking
- Connection pooling (future enhancement)
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any

import click

from zen.client import BridgeClient


class BridgeExecutor:
    """Service for executing commands via the bridge with standardized error handling."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8765,
        max_retries: int = 3,
        retry_delay: float = 0.5,
    ):
        """
        Initialize the bridge executor.

        Args:
            host: Bridge server host (default: localhost)
            port: Bridge server port (default: 8765)
            max_retries: Maximum number of retry attempts on transient failures
            retry_delay: Initial delay between retries in seconds (exponential backoff)
        """
        self.host = host
        self.port = port
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._client: BridgeClient | None = None

    @property
    def client(self) -> BridgeClient:
        """Lazy-initialize the bridge client."""
        if self._client is None:
            self._client = BridgeClient(host=self.host, port=self.port)
        return self._client

    def is_server_running(self) -> bool:
        """
        Check if bridge server is running.

        Returns:
            True if server is alive, False otherwise
        """
        return self.client.is_alive()

    def ensure_server_running(self) -> None:
        """
        Ensure bridge server is running, exit with error if not.

        Exits:
            sys.exit(1) if server is not running
        """
        if not self.is_server_running():
            click.echo(
                "Error: Bridge server is not running. Start it with: zen server start",
                err=True,
            )
            sys.exit(1)

    def execute(
        self,
        code: str,
        timeout: float = 10.0,
        retry_on_timeout: bool = False,
    ) -> dict[str, Any]:
        """
        Execute JavaScript code in browser with error handling and optional retries.

        Args:
            code: JavaScript code to execute
            timeout: Maximum time to wait for result in seconds
            retry_on_timeout: If True, retry on TimeoutError

        Returns:
            Dictionary with execution result:
            {
                "ok": bool,
                "result": Any,  # Present if ok=True
                "error": str,   # Present if ok=False
                "url": str,     # Present for some commands
                "title": str,   # Present for some commands
            }

        Raises:
            SystemExit: If execution fails after retries
        """
        self.ensure_server_running()

        retries = self.max_retries if retry_on_timeout else 1
        delay = self.retry_delay

        for attempt in range(retries):
            try:
                result = self.client.execute(code, timeout=timeout)
                return result

            except TimeoutError as e:
                if attempt < retries - 1:
                    click.echo(
                        f"Timeout on attempt {attempt + 1}/{retries}, retrying in {delay:.1f}s...",
                        err=True,
                    )
                    time.sleep(delay)
                    delay *= 2  # Exponential backoff
                    continue
                else:
                    click.echo(f"Error: {e}", err=True)
                    sys.exit(1)

            except (ConnectionError, RuntimeError) as e:
                click.echo(f"Error: {e}", err=True)
                sys.exit(1)

        # Should not reach here
        click.echo("Error: Execution failed after retries", err=True)
        sys.exit(1)

    def execute_file(
        self,
        filepath: str | Path,
        timeout: float = 10.0,
        retry_on_timeout: bool = False,
    ) -> dict[str, Any]:
        """
        Execute JavaScript from a file.

        Args:
            filepath: Path to JavaScript file
            timeout: Maximum time to wait for result in seconds
            retry_on_timeout: If True, retry on TimeoutError

        Returns:
            Dictionary with execution result

        Raises:
            SystemExit: If file read or execution fails
        """
        try:
            with open(filepath, encoding="utf-8") as f:
                code = f.read()
        except (FileNotFoundError, IOError) as e:
            click.echo(f"Error reading file {filepath}: {e}", err=True)
            sys.exit(1)

        return self.execute(code, timeout=timeout, retry_on_timeout=retry_on_timeout)

    def execute_with_script(
        self,
        script_name: str,
        substitutions: dict[str, str] | None = None,
        timeout: float = 10.0,
        retry_on_timeout: bool = False,
    ) -> dict[str, Any]:
        """
        Execute a helper script with template substitutions.

        Args:
            script_name: Name of script file in zen/scripts/
            substitutions: Dictionary of placeholder -> value substitutions
            timeout: Maximum time to wait for result in seconds
            retry_on_timeout: If True, retry on TimeoutError

        Returns:
            Dictionary with execution result

        Raises:
            SystemExit: If script not found or execution fails
        """
        # Locate script file
        from zen.services.script_loader import ScriptLoader

        loader = ScriptLoader()
        try:
            code = loader.load_script_sync(script_name, substitutions=substitutions)
        except FileNotFoundError as e:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)

        return self.execute(code, timeout=timeout, retry_on_timeout=retry_on_timeout)

    def check_result_ok(self, result: dict[str, Any]) -> None:
        """
        Check if result is successful, exit with error if not.

        Args:
            result: Execution result dictionary

        Exits:
            sys.exit(1) if result["ok"] is False
        """
        if not result.get("ok"):
            error = result.get("error", "Unknown error")
            click.echo(f"Error: {error}", err=True)
            sys.exit(1)

    def get_status(self) -> dict[str, Any] | None:
        """
        Get bridge server status.

        Returns:
            Status dictionary or None if server not running
        """
        return self.client.get_status()

    def check_userscript_version(self, show_warning: bool = True) -> str | None:
        """
        Check if userscript version matches expected version.

        Args:
            show_warning: If True, print warning when versions don't match

        Returns:
            Warning message if versions don't match, None otherwise
        """
        return self.client.check_userscript_version(show_warning=show_warning)


# Global executor instance (lazy-initialized)
_default_executor: BridgeExecutor | None = None


def get_executor(
    host: str = "127.0.0.1",
    port: int = 8765,
    max_retries: int = 3,
) -> BridgeExecutor:
    """
    Get the default executor instance (singleton pattern).

    Args:
        host: Bridge server host
        port: Bridge server port
        max_retries: Maximum retry attempts

    Returns:
        Shared BridgeExecutor instance
    """
    global _default_executor
    if _default_executor is None:
        _default_executor = BridgeExecutor(
            host=host, port=port, max_retries=max_retries
        )
    return _default_executor
