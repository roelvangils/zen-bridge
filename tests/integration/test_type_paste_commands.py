"""
Integration tests for type and paste commands.

These tests verify that the type and paste commands work correctly
with different options and scenarios.
"""

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from inspekt.cli import cli


@pytest.fixture
def runner():
    """Create a Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_bridge_client_for_typing():
    """Mock BridgeClient configured for typing/pasting tests."""
    with patch("inspekt.cli.BridgeClient") as mock_client_class:
        mock_instance = Mock()
        mock_instance.is_alive.return_value = True

        # Mock successful typing response
        mock_instance.execute.return_value = {
            "ok": True,
            "result": {
                "ok": True,
                "message": "Typed 11 character(s): \"Hello World\"",
                "element": "INPUT",
                "length": 11,
                "mode": "typed"
            }
        }

        mock_client_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_bridge_client_not_running():
    """Mock BridgeClient that simulates server not running."""
    with patch("inspekt.cli.BridgeClient") as mock_client_class:
        mock_instance = Mock()
        mock_instance.is_alive.return_value = False
        mock_client_class.return_value = mock_instance
        yield mock_instance


class TestTypeCommand:
    """Test the type command functionality."""

    def test_type_basic_text(self, runner, mock_bridge_client_for_typing):
        """Test typing basic text without options."""
        result = runner.invoke(cli, ["type", "Hello World"])

        assert result.exit_code == 0
        assert "Typed" in result.output or "character" in result.output
        mock_bridge_client_for_typing.execute.assert_called()

    def test_type_with_selector(self, runner, mock_bridge_client_for_typing):
        """Test typing with a CSS selector."""
        result = runner.invoke(cli, ["type", "test@example.com", "--selector", "input[type=email]"])

        assert result.exit_code == 0
        # Should have called execute twice: once for focus, once for typing
        assert mock_bridge_client_for_typing.execute.call_count >= 2

    def test_type_with_speed_fastest(self, runner, mock_bridge_client_for_typing):
        """Test typing with fastest speed (default)."""
        result = runner.invoke(cli, ["type", "Quick text", "--speed", "fastest"])

        assert result.exit_code == 0
        # Verify the script was called with delay 0
        call_args = mock_bridge_client_for_typing.execute.call_args[0][0]
        assert "DELAY_PLACEHOLDER" not in call_args
        assert ", 0, false," in call_args  # Check for delay=0, clearFirst=false

    def test_type_with_custom_speed(self, runner, mock_bridge_client_for_typing):
        """Test typing with custom characters per second."""
        result = runner.invoke(cli, ["type", "Slow text", "--speed", "5"])

        assert result.exit_code == 0
        # Verify the script was called with delay 200ms (1000ms / 5 chars per second)
        call_args = mock_bridge_client_for_typing.execute.call_args[0][0]
        assert ", 200, false," in call_args  # Check for delay=200, clearFirst=false

    def test_type_with_invalid_speed(self, runner, mock_bridge_client_for_typing):
        """Test typing with invalid speed value."""
        result = runner.invoke(cli, ["type", "Text", "--speed", "invalid"])

        assert result.exit_code != 0
        assert "Invalid speed value" in result.output

    def test_type_with_negative_speed(self, runner, mock_bridge_client_for_typing):
        """Test typing with negative speed value."""
        result = runner.invoke(cli, ["type", "Text", "--speed", "-5"])

        assert result.exit_code != 0
        assert "Speed must be a positive number" in result.output

    def test_type_with_special_characters(self, runner, mock_bridge_client_for_typing):
        """Test typing text with special characters."""
        special_text = 'Hello "World" & <script>alert("test")</script>'
        result = runner.invoke(cli, ["type", special_text])

        assert result.exit_code == 0
        # Verify JSON encoding was used
        call_args = mock_bridge_client_for_typing.execute.call_args[0][0]
        # Should contain properly escaped JSON
        assert json.dumps(special_text) in call_args

    def test_type_server_not_running(self, runner, mock_bridge_client_not_running):
        """Test type command when server is not running."""
        result = runner.invoke(cli, ["type", "Hello"])

        assert result.exit_code != 0
        assert "Bridge server is not running" in result.output

    def test_type_with_element_focus_error(self, runner):
        """Test type command when element focus fails."""
        with patch("inspekt.cli.BridgeClient") as mock_client_class:
            mock_instance = Mock()
            mock_instance.is_alive.return_value = True
            # Focus fails
            mock_instance.execute.return_value = {
                "ok": True,
                "result": {
                    "error": "Element not found: #nonexistent"
                }
            }
            mock_client_class.return_value = mock_instance

            result = runner.invoke(cli, ["type", "test", "--selector", "#nonexistent"])

            assert result.exit_code != 0
            assert "Error focusing element" in result.output


class TestPasteCommand:
    """Test the paste command functionality."""

    def test_paste_basic_text(self, runner, mock_bridge_client_for_typing):
        """Test pasting basic text."""
        # Update mock to return pasted mode
        mock_bridge_client_for_typing.execute.return_value = {
            "ok": True,
            "result": {
                "ok": True,
                "message": "Pasted 11 character(s): \"Hello World\"",
                "element": "INPUT",
                "length": 11,
                "mode": "pasted"
            }
        }

        result = runner.invoke(cli, ["paste", "Hello World"])

        assert result.exit_code == 0
        assert "Pasted" in result.output or "character" in result.output
        mock_bridge_client_for_typing.execute.assert_called()

    def test_paste_with_selector(self, runner, mock_bridge_client_for_typing):
        """Test pasting with a CSS selector."""
        mock_bridge_client_for_typing.execute.return_value = {
            "ok": True,
            "result": {
                "ok": True,
                "message": "Pasted text",
                "element": "TEXTAREA",
                "mode": "pasted"
            }
        }

        result = runner.invoke(cli, ["paste", "Quick paste", "--selector", "textarea.content"])

        assert result.exit_code == 0
        # Should have called execute twice: once for focus, once for pasting
        assert mock_bridge_client_for_typing.execute.call_count >= 2

    def test_paste_uses_fastest_speed(self, runner, mock_bridge_client_for_typing):
        """Test that paste command uses fastest speed (delay 0)."""
        result = runner.invoke(cli, ["paste", "Instant text"])

        assert result.exit_code == 0
        # Verify the script was called with delay 0
        call_args = mock_bridge_client_for_typing.execute.call_args[0][0]
        assert ", 0, false," in call_args  # Check for delay=0, clearFirst=false

    def test_paste_large_text(self, runner, mock_bridge_client_for_typing):
        """Test pasting large text."""
        large_text = "Lorem ipsum " * 1000
        mock_bridge_client_for_typing.execute.return_value = {
            "ok": True,
            "result": {
                "ok": True,
                "message": f"Pasted {len(large_text)} character(s)",
                "element": "TEXTAREA",
                "mode": "pasted"
            }
        }

        result = runner.invoke(cli, ["paste", large_text])

        assert result.exit_code == 0


class TestTypeScriptGeneration:
    """Test that the type command generates correct JavaScript."""

    def test_script_uses_json_encoding(self, runner, mock_bridge_client_for_typing):
        """Test that special characters are properly JSON-encoded."""
        test_cases = [
            'Text with "quotes"',
            "Text with 'apostrophes'",
            'Text with\nnewlines',
            'Text with\ttabs',
            'Text with \\ backslashes',
        ]

        for text in test_cases:
            runner.invoke(cli, ["type", text])
            call_args = mock_bridge_client_for_typing.execute.call_args[0][0]
            # Verify the text was JSON-encoded
            assert json.dumps(text) in call_args
            mock_bridge_client_for_typing.reset_mock()

    def test_script_includes_delay_parameter(self, runner, mock_bridge_client_for_typing):
        """Test that the script includes the delay parameter."""
        result = runner.invoke(cli, ["type", "test", "--speed", "10"])

        call_args = mock_bridge_client_for_typing.execute.call_args[0][0]
        # Should have delay of 100ms (1000/10)
        assert "100)" in call_args
        assert "TEXT_PLACEHOLDER" not in call_args
        assert "DELAY_PLACEHOLDER" not in call_args
