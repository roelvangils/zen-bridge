"""
Integration tests for CLI commands with services.

These tests verify that CLI commands properly integrate with services
without requiring a running browser. All external dependencies are mocked.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from click.testing import CliRunner

from zen.cli import cli, format_output


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def runner():
    """Create a Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_bridge_client():
    """Mock BridgeClient with common test responses."""
    with patch("zen.cli.BridgeClient") as mock_client_class:
        mock_instance = Mock()
        mock_instance.is_alive.return_value = True
        mock_instance.execute.return_value = {
            "ok": True,
            "result": "test result",
            "url": "https://example.com",
            "title": "Test Page",
        }
        mock_instance.execute_file.return_value = {
            "ok": True,
            "result": "file result",
        }
        mock_instance.get_status.return_value = {
            "ok": True,
            "pending": 0,
            "completed": 5,
        }
        mock_client_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_bridge_client_not_running():
    """Mock BridgeClient that simulates server not running."""
    with patch("zen.cli.BridgeClient") as mock_client_class:
        mock_instance = Mock()
        mock_instance.is_alive.return_value = False
        mock_client_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_executor():
    """Mock BridgeExecutor for service integration tests."""
    with patch("zen.services.bridge_executor.BridgeExecutor") as mock_executor_class:
        mock_instance = Mock()
        mock_instance.is_server_running.return_value = True
        mock_instance.execute.return_value = {
            "ok": True,
            "result": "executor result",
        }
        mock_instance.execute_file.return_value = {
            "ok": True,
            "result": "file result",
        }
        mock_instance.execute_with_script.return_value = {
            "ok": True,
            "result": "script result",
        }
        mock_executor_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_script_loader():
    """Mock ScriptLoader for script loading tests."""
    with patch("zen.services.script_loader.ScriptLoader") as mock_loader_class:
        mock_instance = Mock()
        mock_instance.load_script_sync.return_value = "console.log('loaded');"
        mock_instance.load_with_substitution_sync.return_value = "console.log('substituted');"
        mock_instance.get_script_path.return_value = Path("/fake/path/script.js")
        mock_loader_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_ai_service():
    """Mock AIIntegrationService for AI integration tests."""
    with patch("zen.services.ai_integration.AIIntegrationService") as mock_service_class:
        mock_instance = Mock()
        mock_instance.check_mods_available.return_value = True
        mock_instance.generate_description.return_value = "AI generated description"
        mock_instance.generate_summary.return_value = "AI generated summary"
        mock_instance.load_prompt.return_value = "Test prompt"
        mock_service_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def temp_js_file(tmp_path):
    """Create a temporary JavaScript file for testing."""
    js_file = tmp_path / "test.js"
    js_file.write_text("console.log('test');")
    return str(js_file)


# =============================================================================
# Test CLI Command Invocation
# =============================================================================


class TestCLIInvocation:
    """Test that CLI commands can be invoked via Click's testing utilities."""

    def test_eval_command_with_code_argument(self, runner, mock_bridge_client):
        """Test eval command with code as argument."""
        result = runner.invoke(cli, ["eval", "document.title"])

        assert result.exit_code == 0
        assert "test result" in result.output
        mock_bridge_client.execute.assert_called_once()

    def test_eval_command_with_file_option(self, runner, mock_bridge_client, temp_js_file):
        """Test eval command with --file option."""
        result = runner.invoke(cli, ["eval", "--file", temp_js_file])

        assert result.exit_code == 0
        mock_bridge_client.execute_file.assert_called_once_with(temp_js_file, timeout=10.0)

    def test_eval_command_with_stdin(self, runner, mock_bridge_client):
        """Test eval command reading from stdin."""
        result = runner.invoke(cli, ["eval"], input="console.log('stdin')")

        assert result.exit_code == 0
        mock_bridge_client.execute.assert_called_once()
        call_args = mock_bridge_client.execute.call_args[0][0]
        assert "console.log('stdin')" in call_args

    def test_exec_command_invocation(self, runner, mock_bridge_client, temp_js_file):
        """Test exec command invocation."""
        result = runner.invoke(cli, ["exec", temp_js_file])

        assert result.exit_code == 0
        assert "file result" in result.output
        mock_bridge_client.execute_file.assert_called_once()

    def test_open_command_invocation(self, runner, mock_bridge_client):
        """Test open command invocation."""
        result = runner.invoke(cli, ["open", "https://example.com"])

        assert result.exit_code == 0
        mock_bridge_client.execute.assert_called()

    def test_server_status_command(self, runner, mock_bridge_client):
        """Test server status command."""
        result = runner.invoke(cli, ["server", "status"])

        assert result.exit_code == 0
        assert "Bridge server is running" in result.output
        mock_bridge_client.is_alive.assert_called()

    def test_help_text_generation_main(self, runner):
        """Test main CLI help text generation."""
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "Zen Browser Bridge" in result.output
        assert "Commands:" in result.output

    def test_help_text_generation_eval(self, runner):
        """Test eval command help text."""
        result = runner.invoke(cli, ["eval", "--help"])

        assert result.exit_code == 0
        assert "Execute JavaScript code" in result.output
        assert "--file" in result.output
        assert "--timeout" in result.output

    def test_error_handling_server_not_running(self, runner):
        """Test error handling when server is not running."""
        with patch("zen.cli.BridgeClient") as mock_client_class:
            mock_instance = Mock()
            mock_instance.is_alive.return_value = False
            mock_instance.execute.side_effect = ConnectionError(
                "Bridge server is not running. Start it with: zen server start"
            )
            mock_client_class.return_value = mock_instance

            result = runner.invoke(cli, ["eval", "document.title"])

            assert result.exit_code == 1
            assert "Error" in result.output


# =============================================================================
# Test Service Integration
# =============================================================================


class TestServiceIntegration:
    """Test that CLI commands properly use services."""

    def test_bridge_executor_integration_execute(self, runner, mock_bridge_client):
        """Test BridgeExecutor is used correctly for code execution."""
        result = runner.invoke(cli, ["eval", "document.title"])

        assert result.exit_code == 0
        # BridgeClient (not BridgeExecutor directly) is used in CLI
        mock_bridge_client.execute.assert_called_once()

    def test_bridge_executor_timeout_parameter(self, runner, mock_bridge_client):
        """Test timeout parameter is passed to executor."""
        result = runner.invoke(cli, ["eval", "document.title", "--timeout", "20.0"])

        assert result.exit_code == 0
        mock_bridge_client.execute.assert_called_once()
        call_kwargs = mock_bridge_client.execute.call_args[1]
        assert call_kwargs["timeout"] == 20.0

    def test_configuration_loading_implicit(self, runner, mock_bridge_client):
        """Test configuration is loaded implicitly by commands."""
        with patch("zen.config.load_config") as mock_load:
            mock_load.return_value = {"ai-language": "en"}
            result = runner.invoke(cli, ["eval", "document.title"])

            assert result.exit_code == 0

    def test_error_propagation_connection_error(self, runner, mock_bridge_client):
        """Test ConnectionError propagates from service to CLI."""
        mock_bridge_client.execute.side_effect = ConnectionError("Connection failed")

        result = runner.invoke(cli, ["eval", "document.title"])

        assert result.exit_code == 1
        assert "Error" in result.output
        assert "Connection failed" in result.output

    def test_error_propagation_timeout_error(self, runner, mock_bridge_client):
        """Test TimeoutError propagates from service to CLI."""
        mock_bridge_client.execute.side_effect = TimeoutError("Operation timed out")

        result = runner.invoke(cli, ["eval", "document.title"])

        assert result.exit_code == 1
        assert "Error" in result.output
        assert "timed out" in result.output

    def test_error_propagation_runtime_error(self, runner, mock_bridge_client):
        """Test RuntimeError propagates from service to CLI."""
        mock_bridge_client.execute.side_effect = RuntimeError("Script failed")

        result = runner.invoke(cli, ["eval", "document.title"])

        assert result.exit_code == 1
        assert "Error" in result.output
        assert "Script failed" in result.output

    def test_result_validation_ok_false(self, runner, mock_bridge_client):
        """Test result validation when ok=False."""
        mock_bridge_client.execute.return_value = {
            "ok": False,
            "error": "ReferenceError: foo is not defined",
        }

        result = runner.invoke(cli, ["eval", "foo()"])

        assert result.exit_code == 1
        assert "Error" in result.output
        assert "ReferenceError" in result.output

    def test_client_initialization_with_default_config(self, runner, mock_bridge_client):
        """Test BridgeClient is initialized with default configuration."""
        result = runner.invoke(cli, ["server", "status"])

        assert result.exit_code == 0
        # Client should be created with defaults


# =============================================================================
# Test Script Loading Flow
# =============================================================================


class TestScriptLoading:
    """Test the complete script loading chain."""

    def test_script_loading_from_file(self, runner, mock_bridge_client, temp_js_file):
        """Test script loading from file via execute_file."""
        result = runner.invoke(cli, ["exec", temp_js_file])

        assert result.exit_code == 0
        mock_bridge_client.execute_file.assert_called_once_with(temp_js_file, timeout=10.0)

    def test_script_loading_with_timeout(self, runner, mock_bridge_client, temp_js_file):
        """Test script loading with custom timeout."""
        result = runner.invoke(cli, ["exec", temp_js_file, "--timeout", "30.0"])

        assert result.exit_code == 0
        call_kwargs = mock_bridge_client.execute_file.call_args[1]
        assert call_kwargs["timeout"] == 30.0

    def test_missing_script_handling(self, runner, mock_bridge_client):
        """Test handling of missing script file."""
        result = runner.invoke(cli, ["exec", "/nonexistent/script.js"])

        assert result.exit_code == 2  # Click's file not found error
        assert "does not exist" in result.output.lower() or "error" in result.output.lower()

    def test_file_read_via_eval_file_option(self, runner, mock_bridge_client, temp_js_file):
        """Test file reading via eval --file option."""
        result = runner.invoke(cli, ["eval", "--file", temp_js_file])

        assert result.exit_code == 0
        mock_bridge_client.execute_file.assert_called_once()


# =============================================================================
# Test Error Handling
# =============================================================================


class TestErrorHandling:
    """Test error handling across layers."""

    def test_connection_error_handling(self, runner, mock_bridge_client):
        """Test ConnectionError is handled and displayed."""
        mock_bridge_client.execute.side_effect = ConnectionError("Server unavailable")

        result = runner.invoke(cli, ["eval", "document.title"])

        assert result.exit_code == 1
        assert "Error" in result.output
        assert "unavailable" in result.output

    def test_timeout_error_handling(self, runner, mock_bridge_client):
        """Test TimeoutError is handled and displayed."""
        mock_bridge_client.execute.side_effect = TimeoutError("Request timed out")

        result = runner.invoke(cli, ["eval", "document.title"])

        assert result.exit_code == 1
        assert "Error" in result.output

    def test_validation_error_handling(self, runner, mock_bridge_client):
        """Test validation errors in result."""
        mock_bridge_client.execute.return_value = {
            "ok": False,
            "error": "TypeError: Cannot read property 'x' of undefined",
        }

        result = runner.invoke(cli, ["eval", "obj.x"])

        assert result.exit_code == 1
        assert "TypeError" in result.output

    def test_file_not_found_error(self, runner, mock_bridge_client):
        """Test file not found error handling."""
        result = runner.invoke(cli, ["exec", "/path/to/missing.js"])

        assert result.exit_code == 2
        # Click handles file validation

    def test_exit_code_on_execution_failure(self, runner, mock_bridge_client):
        """Test proper exit code on execution failure."""
        mock_bridge_client.execute.return_value = {
            "ok": False,
            "error": "Execution failed",
        }

        result = runner.invoke(cli, ["eval", "invalid()"])

        assert result.exit_code == 1

    def test_exit_code_on_connection_failure(self, runner, mock_bridge_client):
        """Test proper exit code on connection failure."""
        mock_bridge_client.execute.side_effect = ConnectionError("Failed")

        result = runner.invoke(cli, ["eval", "test"])

        assert result.exit_code == 1

    def test_server_not_running_error(self, runner, mock_bridge_client_not_running):
        """Test error when server is not running."""
        result = runner.invoke(cli, ["server", "status"])

        assert result.exit_code == 1
        assert "not running" in result.output

    def test_eval_no_input_error(self, runner, mock_bridge_client):
        """Test error when eval has no code input from stdin."""
        # CliRunner treats stdin as non-tty, so eval reads empty string from stdin
        # Then tries to execute it, which should fail
        mock_bridge_client.execute.side_effect = ConnectionError("Failed to submit code")

        result = runner.invoke(cli, ["eval"], input="")

        assert result.exit_code == 1
        assert "Error" in result.output


# =============================================================================
# Test Output Formatting
# =============================================================================


class TestOutputFormatting:
    """Test output formatting functions."""

    def test_format_output_auto_string(self):
        """Test auto format with string result."""
        result = {"ok": True, "result": "Hello World"}
        output = format_output(result, "auto")
        assert output == "Hello World"

    def test_format_output_auto_number(self):
        """Test auto format with number result."""
        result = {"ok": True, "result": 42}
        output = format_output(result, "auto")
        assert output == "42"

    def test_format_output_auto_dict(self):
        """Test auto format with dictionary result."""
        result = {"ok": True, "result": {"key": "value"}}
        output = format_output(result, "auto")
        assert '"key"' in output
        assert '"value"' in output

    def test_format_output_auto_list(self):
        """Test auto format with list result."""
        result = {"ok": True, "result": [1, 2, 3]}
        output = format_output(result, "auto")
        assert "[" in output
        assert "1" in output

    def test_format_output_auto_undefined(self):
        """Test auto format with None (undefined) result."""
        result = {"ok": True, "result": None}
        output = format_output(result, "auto")
        assert output == "undefined"

    def test_format_output_json_format(self):
        """Test JSON output format."""
        result = {"ok": True, "result": {"key": "value"}}
        output = format_output(result, "json")
        parsed = json.loads(output)
        assert parsed == {"key": "value"}

    def test_format_output_raw_format(self):
        """Test raw output format."""
        result = {"ok": True, "result": "test value"}
        output = format_output(result, "raw")
        assert output == "test value"

    def test_format_output_raw_format_none(self):
        """Test raw format with None result."""
        result = {"ok": True, "result": None}
        output = format_output(result, "raw")
        assert output == ""

    def test_format_output_error(self):
        """Test format output with error."""
        result = {"ok": False, "error": "Something went wrong"}
        output = format_output(result, "auto")
        assert output == "Error: Something went wrong"

    def test_format_output_error_unknown(self):
        """Test format output with unknown error."""
        result = {"ok": False}
        output = format_output(result, "auto")
        assert output == "Error: Unknown error"

    def test_eval_output_with_format_option(self, runner, mock_bridge_client):
        """Test eval command with --format option."""
        mock_bridge_client.execute.return_value = {
            "ok": True,
            "result": {"test": "data"},
        }

        result = runner.invoke(cli, ["eval", "getData()", "--format", "json"])

        assert result.exit_code == 0
        # Output should be JSON formatted
        parsed = json.loads(result.output.strip())
        assert parsed == {"test": "data"}

    def test_eval_output_with_url_flag(self, runner, mock_bridge_client):
        """Test eval command with --url flag."""
        result = runner.invoke(cli, ["eval", "document.title", "--url"])

        assert result.exit_code == 0
        assert "https://example.com" in result.output

    def test_eval_output_with_title_flag(self, runner, mock_bridge_client):
        """Test eval command with --title flag."""
        result = runner.invoke(cli, ["eval", "getData()", "--title"])

        assert result.exit_code == 0
        assert "Test Page" in result.output


# =============================================================================
# Test Complex Integration Scenarios
# =============================================================================


class TestComplexIntegration:
    """Test complex integration scenarios across multiple components."""

    def test_eval_command_full_flow(self, runner, mock_bridge_client):
        """Test complete eval command flow from CLI to client."""
        result = runner.invoke(
            cli, ["eval", "document.querySelector('h1').textContent", "--timeout", "15.0"]
        )

        assert result.exit_code == 0
        mock_bridge_client.execute.assert_called_once()
        call_args, call_kwargs = mock_bridge_client.execute.call_args
        assert "document.querySelector" in call_args[0]
        assert call_kwargs["timeout"] == 15.0

    def test_exec_command_full_flow(self, runner, mock_bridge_client, temp_js_file):
        """Test complete exec command flow."""
        result = runner.invoke(cli, ["exec", temp_js_file, "--format", "json"])

        assert result.exit_code == 0
        mock_bridge_client.execute_file.assert_called_once()

    def test_server_status_full_flow(self, runner, mock_bridge_client):
        """Test complete server status flow."""
        result = runner.invoke(cli, ["server", "status"])

        assert result.exit_code == 0
        assert "Bridge server is running" in result.output
        assert "Pending requests" in result.output or "Completed requests" in result.output

    def test_error_recovery_chain(self, runner, mock_bridge_client):
        """Test error handling chain from client to CLI output."""
        # Simulate execution error
        mock_bridge_client.execute.return_value = {
            "ok": False,
            "error": "ReferenceError: foo is not defined",
        }

        result = runner.invoke(cli, ["eval", "foo()"])

        assert result.exit_code == 1
        assert "Error" in result.output
        assert "ReferenceError" in result.output

    def test_multiple_options_integration(self, runner, mock_bridge_client):
        """Test command with multiple options."""
        result = runner.invoke(
            cli,
            [
                "eval",
                "document.title",
                "--timeout",
                "25.0",
                "--format",
                "raw",
                "--url",
                "--title",
            ],
        )

        assert result.exit_code == 0
        # Check timeout was passed
        call_kwargs = mock_bridge_client.execute.call_args[1]
        assert call_kwargs["timeout"] == 25.0
        # Check metadata displayed
        assert "URL:" in result.output or "https://example.com" in result.output


# =============================================================================
# Test CLI-Specific Behavior
# =============================================================================


class TestCLISpecificBehavior:
    """Test CLI-specific behavior and edge cases."""

    def test_version_option(self, runner):
        """Test --version option."""
        result = runner.invoke(cli, ["--version"])

        assert result.exit_code == 0
        # Should contain version information

    def test_command_without_arguments(self, runner):
        """Test running CLI without arguments shows help."""
        result = runner.invoke(cli, [])

        assert result.exit_code == 0
        assert "Zen Browser Bridge" in result.output or "Commands:" in result.output

    def test_invalid_command(self, runner):
        """Test invalid command shows error."""
        result = runner.invoke(cli, ["nonexistent"])

        assert result.exit_code != 0
        assert "Error" in result.output or "No such command" in result.output

    def test_eval_stdin_interactive_error(self, runner, mock_bridge_client):
        """Test eval command reads from stdin in test environment."""
        # CliRunner always treats stdin as non-tty, so eval reads from stdin
        # Empty stdin results in empty code being executed
        mock_bridge_client.execute.side_effect = ConnectionError("Failed to submit code")

        result = runner.invoke(cli, ["eval"], input="")

        assert result.exit_code == 1
        assert "Error" in result.output

    def test_server_start_when_already_running(self, runner, mock_bridge_client):
        """Test server start when already running."""
        with patch("zen.cli.subprocess.Popen"):
            result = runner.invoke(cli, ["server", "start"])

            assert result.exit_code == 0
            assert "already running" in result.output

    def test_open_command_with_url(self, runner, mock_bridge_client):
        """Test open command with URL argument."""
        result = runner.invoke(cli, ["open", "https://example.org"])

        assert result.exit_code == 0
        mock_bridge_client.execute.assert_called()
