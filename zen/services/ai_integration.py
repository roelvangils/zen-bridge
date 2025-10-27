"""
AI Integration Service - Language detection and AI tool orchestration.

This service handles:
- Language detection from page content and configuration
- Prompt file loading and formatting
- Integration with external AI tools (mods, etc.)
- Debug mode for prompt inspection
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import click

from zen import config as zen_config


class AIIntegrationService:
    """Service for AI-powered content analysis and language handling."""

    def __init__(self, prompts_dir: Path | None = None):
        """
        Initialize the AI integration service.

        Args:
            prompts_dir: Directory containing prompt files (default: project_root/prompts/)
        """
        if prompts_dir is None:
            # Default to project_root/prompts/
            current_file = Path(__file__)
            self.prompts_dir = current_file.parent.parent.parent / "prompts"
        else:
            self.prompts_dir = Path(prompts_dir)

    def get_target_language(
        self,
        language_override: str | None = None,
        page_lang: str | None = None,
    ) -> str | None:
        """
        Determine the language for AI operations.

        Priority:
        1. language_override (from --language flag)
        2. config.json ai-language setting
        3. If "auto", detect from page_lang
        4. Default to None (let AI decide)

        Args:
            language_override: Language code from CLI flag (e.g., "en", "nl", "fr")
            page_lang: Detected page language

        Returns:
            Language code or None to let AI decide
        """
        # Priority 1: CLI flag override
        if language_override:
            return language_override

        # Priority 2: Config file
        config = zen_config.load_config()
        config_lang = config.get("ai-language", "auto")

        # If config specifies a language (not "auto"), use it
        if config_lang and config_lang != "auto":
            return config_lang

        # Priority 3: Auto-detect from page
        if page_lang:
            return page_lang

        # Default: let AI decide
        return None

    def extract_page_language(self, content: str) -> str | None:
        """
        Extract page language from content string.

        Looks for patterns like:
        - "**Language:** xx"
        - "lang": "xx"

        Args:
            content: Content string (markdown or JSON)

        Returns:
            Language code or None if not found
        """
        # Try markdown pattern first
        match = re.search(r"\*\*Language:\*\*\s*(\w+)", content)
        if match:
            return match.group(1)

        # Try JSON pattern
        match = re.search(r'"lang"\s*:\s*"(\w+)"', content)
        if match:
            return match.group(1)

        return None

    def check_mods_available(self) -> bool:
        """
        Check if the 'mods' AI tool is available.

        Returns:
            True if mods is installed and accessible
        """
        try:
            subprocess.run(
                ["mods", "--version"],
                capture_output=True,
                check=True,
                timeout=5.0,
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def ensure_mods_available(self) -> None:
        """
        Ensure mods is available, exit with error if not.

        Exits:
            sys.exit(1) if mods is not installed
        """
        if not self.check_mods_available():
            click.echo("Error: 'mods' command not found. Please install mods first.", err=True)
            click.echo("Visit: https://github.com/charmbracelet/mods", err=True)
            sys.exit(1)

    def load_prompt(self, prompt_name: str) -> str:
        """
        Load a prompt file from the prompts directory.

        Args:
            prompt_name: Name of prompt file (e.g., "describe.prompt", "summary.prompt")

        Returns:
            Prompt content as string

        Raises:
            SystemExit: If prompt file not found
        """
        prompt_path = self.prompts_dir / prompt_name
        if not prompt_path.exists():
            click.echo(f"Error: Prompt file not found: {prompt_path}", err=True)
            sys.exit(1)

        try:
            with open(prompt_path, encoding="utf-8") as f:
                return f.read().strip()
        except IOError as e:
            click.echo(f"Error reading prompt file: {e}", err=True)
            sys.exit(1)

    def format_prompt(
        self,
        base_prompt: str,
        content: str,
        target_lang: str | None = None,
        extra_instructions: str | None = None,
    ) -> str:
        """
        Format a complete prompt with language instructions and content.

        Args:
            base_prompt: Base prompt template
            content: Content to analyze
            target_lang: Target language code (optional)
            extra_instructions: Additional instructions to append (optional)

        Returns:
            Formatted prompt ready for AI tool
        """
        prompt_parts = [base_prompt]

        # Add language instruction if specified
        if target_lang:
            prompt_parts.append(
                f"\n\nIMPORTANT: Provide your response in {target_lang} language."
            )

        # Add extra instructions if provided
        if extra_instructions:
            prompt_parts.append(f"\n\n{extra_instructions}")

        # Add content separator
        prompt_parts.append("\n\n---\n\n")

        # Add content
        prompt_parts.append(content)

        return "".join(prompt_parts)

    def call_mods(
        self,
        prompt: str,
        timeout: float = 60.0,
        additional_args: list[str] | None = None,
    ) -> str:
        """
        Call the mods AI tool with the given prompt.

        Args:
            prompt: Complete prompt to send to mods
            timeout: Maximum time to wait for response in seconds
            additional_args: Additional CLI arguments for mods

        Returns:
            AI response text

        Raises:
            SystemExit: If mods call fails
        """
        cmd = ["mods"]
        if additional_args:
            cmd.extend(additional_args)

        try:
            result = subprocess.run(
                cmd,
                input=prompt,
                text=True,
                capture_output=True,
                check=True,
                timeout=timeout,
            )
            return result.stdout

        except subprocess.TimeoutExpired:
            click.echo(f"Error: mods timed out after {timeout} seconds", err=True)
            sys.exit(1)

        except subprocess.CalledProcessError as e:
            click.echo(f"Error calling mods: {e}", err=True)
            if e.stderr:
                click.echo(e.stderr, err=True)
            sys.exit(1)

    def show_debug_prompt(self, prompt: str) -> None:
        """
        Display a formatted debug view of the prompt.

        Args:
            prompt: The prompt to display
        """
        click.echo("=" * 80)
        click.echo("DEBUG: Full prompt that would be sent to AI")
        click.echo("=" * 80)
        click.echo()
        click.echo(prompt)
        click.echo()
        click.echo("=" * 80)

    def generate_description(
        self,
        page_structure: str,
        language_override: str | None = None,
        debug: bool = False,
    ) -> str | None:
        """
        Generate an AI-powered page description.

        Args:
            page_structure: Extracted page structure (markdown format)
            language_override: Optional language override
            debug: If True, show prompt instead of calling AI

        Returns:
            AI-generated description or None if debug mode
        """
        # Extract page language
        page_lang = self.extract_page_language(page_structure)

        # Determine target language
        target_lang = self.get_target_language(
            language_override=language_override,
            page_lang=page_lang,
        )

        # Load and format prompt
        base_prompt = self.load_prompt("describe.prompt")
        full_prompt = self.format_prompt(
            base_prompt=base_prompt,
            content=f"PAGE STRUCTURE:\n\n{page_structure}",
            target_lang=target_lang,
        )

        # Debug mode: show prompt
        if debug:
            self.show_debug_prompt(full_prompt)
            return None

        # Call AI
        click.echo("Generating description...", err=True)
        return self.call_mods(full_prompt)

    def generate_summary(
        self,
        article: dict[str, Any],
        language_override: str | None = None,
        debug: bool = False,
    ) -> str | None:
        """
        Generate an AI-powered article summary.

        Args:
            article: Extracted article data (title, content, byline, lang)
            language_override: Optional language override
            debug: If True, show prompt instead of calling AI

        Returns:
            AI-generated summary or None if debug mode
        """
        title = article.get("title", "Untitled")
        content = article.get("content", "")
        page_lang = article.get("lang")

        # Determine target language
        target_lang = self.get_target_language(
            language_override=language_override,
            page_lang=page_lang,
        )

        # Load and format prompt
        base_prompt = self.load_prompt("summary.prompt")
        full_prompt = self.format_prompt(
            base_prompt=base_prompt,
            content=f"Title: {title}\n\n{content}",
            target_lang=target_lang,
        )

        # Debug mode: show prompt
        if debug:
            self.show_debug_prompt(full_prompt)
            return None

        # Call AI
        click.echo(f"Generating summary for: {title}", err=True)
        return self.call_mods(full_prompt)


# Global service instance (lazy-initialized)
_default_service: AIIntegrationService | None = None


def get_ai_service(prompts_dir: Path | None = None) -> AIIntegrationService:
    """
    Get the default AI integration service instance (singleton pattern).

    Args:
        prompts_dir: Optional custom prompts directory

    Returns:
        Shared AIIntegrationService instance
    """
    global _default_service
    if _default_service is None:
        _default_service = AIIntegrationService(prompts_dir=prompts_dir)
    return _default_service
