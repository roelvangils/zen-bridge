"""
Content extraction and AI-powered analysis commands.

This module provides commands for extracting and analyzing page content:
- describe: AI-powered page description for screen reader users
- outline: Display heading structure as nested outline
- links: Extract and display links with optional enrichment
- summarize: AI-powered article summary

These commands use external AI tools (mods) and helper scripts for
content extraction.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import click

from zen.app.cli.base import builtin_open, get_ai_language
from zen.client import BridgeClient
from zen.services.ai_integration import get_ai_service
from zen.services.bridge_executor import get_executor
from zen.services.script_loader import ScriptLoader


@click.command()
@click.option(
    "--language", "--lang", type=str, default=None, help="Language for AI output (overrides config)"
)
@click.option("--debug", is_flag=True, help="Show the full prompt instead of calling AI")
def describe(language, debug):
    """
    Generate an AI-powered description of the page for screen reader users.

    Extracts page structure (landmarks, headings, links, images, forms) and
    uses AI to create a concise, natural description perfect for blind users
    to understand what the page offers at a glance.

    Examples:
        zen describe
    """
    client = BridgeClient()

    if not client.is_alive():
        click.echo("Error: Bridge server is not running. Start it with: zen server start", err=True)
        sys.exit(1)

    # Check if mods is available
    try:
        subprocess.run(["mods", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        click.echo("Error: 'mods' command not found. Please install mods first.", err=True)
        click.echo("Visit: https://github.com/charmbracelet/mods", err=True)
        sys.exit(1)

    # Load and execute the extraction script
    script_path = Path(__file__).parent.parent / "scripts" / "extract_page_structure.js"

    if not script_path.exists():
        click.echo(f"Error: Script not found: {script_path}", err=True)
        sys.exit(1)

    try:
        with builtin_open(script_path) as f:
            script = f.read()

        click.echo("Analyzing page structure...", err=True)
        result = client.execute(script, timeout=30.0)

        if not result.get("ok"):
            click.echo(f"Error: {result.get('error')}", err=True)
            sys.exit(1)

        # The script now returns a markdown-formatted string
        page_structure = result.get("result", "")

        if not page_structure or not isinstance(page_structure, str):
            click.echo("Error: No page structure extracted", err=True)
            sys.exit(1)

        # Extract page language from the structure for language detection
        # Look for "**Language:** xx" pattern
        page_lang = None
        lang_match = re.search(r"\*\*Language:\*\* (\w+)", page_structure)
        if lang_match:
            page_lang = lang_match.group(1)

        # Determine target language for AI
        target_lang = get_ai_language(language_override=language, page_lang=page_lang)

        # Read the prompt
        prompt_path = Path(__file__).parent.parent.parent / "prompts" / "describe.prompt"

        if not prompt_path.exists():
            click.echo(f"Error: Prompt file not found: {prompt_path}", err=True)
            sys.exit(1)

        with builtin_open(prompt_path) as f:
            prompt = f.read().strip()

        # Add language instruction if specified
        if target_lang:
            prompt = f"{prompt}\n\nIMPORTANT: Provide your response in {target_lang} language."

        # Combine prompt with page structure (now in Markdown format)
        full_input = f"{prompt}\n\n---\n\nPAGE STRUCTURE:\n\n{page_structure}"

        # Debug mode: show the full prompt instead of calling AI
        if debug:
            click.echo("=" * 80)
            click.echo("DEBUG: Full prompt that would be sent to AI")
            click.echo("=" * 80)
            click.echo()
            click.echo(full_input)
            click.echo()
            click.echo("=" * 80)
            return

        click.echo("Generating description...", err=True)

        # Call mods
        try:
            result = subprocess.run(
                ["mods"], input=full_input, text=True, capture_output=True, check=True
            )

            click.echo(result.stdout)

        except subprocess.CalledProcessError as e:
            click.echo(f"Error calling mods: {e}", err=True)
            if e.stderr:
                click.echo(e.stderr, err=True)
            sys.exit(1)

    except (ConnectionError, TimeoutError, RuntimeError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@click.command()
def outline():
    """
    Display the page's heading structure as a nested outline.

    Shows all headings (H1-H6 and ARIA headings) in a hierarchical view.
    Heading levels are shown in gray, text in white.

    Examples:
        zen outline
    """
    client = BridgeClient()

    if not client.is_alive():
        click.echo("Error: Bridge server is not running. Start it with: zen server start", err=True)
        sys.exit(1)

    # Load and execute the extract_outline script
    script_path = Path(__file__).parent.parent / "scripts" / "extract_outline.js"

    if not script_path.exists():
        click.echo(f"Error: Script not found: {script_path}", err=True)
        sys.exit(1)

    try:
        with builtin_open(script_path) as f:
            script = f.read()

        result = client.execute(script, timeout=30.0)

        if not result.get("ok"):
            click.echo(f"Error: {result.get('error')}", err=True)
            sys.exit(1)

        data = result.get("result", {})
        headings = data.get("headings", [])

        if not headings:
            click.echo("No headings found on this page.", err=True)
            sys.exit(0)

        # Display the outline with proper indentation
        for heading in headings:
            level = heading["level"]
            text = heading["text"]

            # Calculate indentation (3 spaces per level, starting at level 1)
            indent = "   " * (level - 1)

            # Format: H{level} in gray, text in white
            level_label = click.style(f"H{level}", fg="bright_black")
            heading_text = text

            # Truncate very long headings
            if len(heading_text) > 100:
                heading_text = heading_text[:97] + "..."

            click.echo(f"{indent}{level_label} {heading_text}")

        # Show summary
        click.echo("", err=True)
        click.echo(f"Total: {len(headings)} headings", err=True)

    except (ConnectionError, TimeoutError, RuntimeError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def _enrich_link_metadata(url: str) -> dict:
    """
    Fetch metadata for a single external link using curl.

    Returns dict with: http_status, mime_type, file_size, filename, page_title, page_language
    """
    enrichment = {
        "http_status": None,
        "mime_type": None,
        "file_size": None,
        "filename": None,
        "page_title": None,
        "page_language": None,
    }

    try:
        # First, do a HEAD request to get headers
        head_result = subprocess.run(
            ["curl", "-L", "-I", "-s", "-m", "5", "--user-agent", "zen-bridge/1.0", url],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if head_result.returncode != 0:
            return enrichment

        headers = head_result.stdout

        # Parse HTTP status code
        status_match = re.search(r"HTTP/[\d.]+ (\d+)", headers)
        if status_match:
            enrichment["http_status"] = int(status_match.group(1))

        # Parse Content-Type
        content_type_match = re.search(r"(?i)^Content-Type:\s*([^\r\n;]+)", headers, re.MULTILINE)
        if content_type_match:
            enrichment["mime_type"] = content_type_match.group(1).strip()

        # Parse Content-Length
        content_length_match = re.search(r"(?i)^Content-Length:\s*(\d+)", headers, re.MULTILINE)
        if content_length_match:
            enrichment["file_size"] = int(content_length_match.group(1))

        # Parse Content-Disposition for filename
        content_disp_match = re.search(
            r'(?i)^Content-Disposition:.*filename[*]?=["\']?([^"\'\r\n;]+)', headers, re.MULTILINE
        )
        if content_disp_match:
            enrichment["filename"] = content_disp_match.group(1).strip()

        # Parse Content-Language
        content_lang_match = re.search(
            r"(?i)^Content-Language:\s*([^\r\n;]+)", headers, re.MULTILINE
        )
        if content_lang_match:
            enrichment["page_language"] = content_lang_match.group(1).strip()

        # If this looks like HTML, fetch partial content to get title and lang
        mime_type = enrichment.get("mime_type", "").lower()
        if mime_type and ("html" in mime_type or mime_type == "text/html"):
            # Fetch first 16KB of content
            get_result = subprocess.run(
                [
                    "curl",
                    "-L",
                    "-s",
                    "-m",
                    "5",
                    "--user-agent",
                    "zen-bridge/1.0",
                    "--max-filesize",
                    "16384",
                    url,
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if get_result.returncode == 0:
                html_content = get_result.stdout

                # Extract page title
                title_match = re.search(r"<title[^>]*>([^<]+)</title>", html_content, re.IGNORECASE)
                if title_match:
                    # Decode HTML entities and clean up
                    title = title_match.group(1).strip()
                    title = re.sub(r"\s+", " ", title)  # Normalize whitespace
                    enrichment["page_title"] = title

                # Extract language from <html lang="...">
                if not enrichment["page_language"]:
                    lang_match = re.search(
                        r'<html[^>]+lang=["\']?([^"\'\s>]+)', html_content, re.IGNORECASE
                    )
                    if lang_match:
                        enrichment["page_language"] = lang_match.group(1).strip()

    except (subprocess.TimeoutExpired, subprocess.SubprocessError, Exception):
        # Silently fail - return partial data
        pass

    return enrichment


def _enrich_external_links(links: list) -> list:
    """
    Enrich external links with metadata using parallel curl requests.
    Only processes up to 50 external links.

    Returns the same list with enrichment data added to external links.
    """
    # Filter to get external links only
    external_links = [
        link for link in links if link.get("external") or link.get("type") == "external"
    ]

    # Check if we should skip enrichment
    if len(external_links) > 50:
        return links

    # Create a mapping of URL to link object
    url_to_link = {}
    urls_to_enrich = []

    for link in external_links:
        url = link.get("url") or link.get("href")
        if url:
            url_to_link[url] = link
            urls_to_enrich.append(url)

    # Fetch metadata in parallel
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_url = {executor.submit(_enrich_link_metadata, url): url for url in urls_to_enrich}

        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                enrichment = future.result()
                # Add enrichment data to the link object
                link_obj = url_to_link[url]
                link_obj.update(enrichment)
            except Exception:
                # Skip failed enrichments
                pass

    return links


@click.command()
@click.option("--only-internal", is_flag=True, help="Show only internal links (same domain)")
@click.option("--only-external", is_flag=True, help="Show only external links (different domain)")
@click.option("--alphabetically", is_flag=True, help="Sort links alphabetically")
@click.option("--only-urls", is_flag=True, help="Show only URLs without anchor text")
@click.option(
    "--json", "output_json", is_flag=True, help="Output as JSON with detailed link information"
)
@click.option(
    "--enrich-external",
    is_flag=True,
    help="Fetch additional metadata for external links (MIME type, file size, page title, language, HTTP status)",
)
def links(only_internal, only_external, alphabetically, only_urls, output_json, enrich_external):
    """
    Extract all links from the current page.

    By default, shows all links with their anchor text.
    Use filters to show only internal or external links.

    Examples:
        zen links                           # All links with anchor text
        zen links --only-internal           # Only links on same domain
        zen links --only-external           # Only links to other domains
        zen links --alphabetically          # Sort alphabetically
        zen links --only-urls               # Show only URLs
        zen links --only-external --only-urls  # External URLs only
        zen links --enrich-external         # Add metadata for external links
    """
    client = BridgeClient()

    if not client.is_alive():
        click.echo("Error: Bridge server is not running. Start it with: zen server start", err=True)
        sys.exit(1)

    # Check for conflicting flags
    if only_internal and only_external:
        click.echo("Error: Cannot use --only-internal and --only-external together", err=True)
        sys.exit(1)

    # Load and execute the extract_links script
    script_path = Path(__file__).parent.parent / "scripts" / "extract_links.js"

    if not script_path.exists():
        click.echo(f"Error: Script not found: {script_path}", err=True)
        sys.exit(1)

    try:
        with builtin_open(script_path) as f:
            script = f.read()

        result = client.execute(script, timeout=30.0)

        if not result.get("ok"):
            click.echo(f"Error: {result.get('error')}", err=True)
            sys.exit(1)

        data = result.get("result", {})
        all_links = data.get("links", [])
        domain = data.get("domain", "")

        if not all_links:
            click.echo("No links found on this page.", err=True)
            sys.exit(0)

        # Filter links
        filtered_links = all_links
        if only_internal:
            filtered_links = [link for link in all_links if link["type"] == "internal"]
        elif only_external:
            filtered_links = [link for link in all_links if link["type"] == "external"]

        if not filtered_links:
            filter_type = "internal" if only_internal else "external" if only_external else "total"
            click.echo(f"No {filter_type} links found.", err=True)
            sys.exit(0)

        # Enrich external links if requested
        if enrich_external:
            filtered_links = _enrich_external_links(filtered_links)

        # Sort if requested
        if alphabetically:
            if only_urls:
                # Sort by URL
                filtered_links.sort(key=lambda x: x["href"].lower())
            else:
                # Sort by anchor text
                filtered_links.sort(key=lambda x: x["text"].lower())

        # If JSON output is requested, output JSON and exit
        if output_json:
            output_data = {"links": filtered_links, "total": len(filtered_links), "domain": domain}
            click.echo(json.dumps(output_data, indent=2))
            return

        # Output links
        if only_urls:
            # Just print URLs, one per line
            for link in filtered_links:
                click.echo(link["href"])
        else:
            # Print with anchor text
            for link in filtered_links:
                text = link["text"]
                href = link["href"]
                # Truncate long text
                if len(text) > 60:
                    text = text[:57] + "..."
                # Show type indicator
                type_indicator = "↗" if link["type"] == "external" else "→"
                click.echo(f"{type_indicator} {text}")
                click.echo(f"  {href}")

                # Show enrichment data if available
                if enrich_external and link.get("type") == "external":
                    enrichment_lines = []

                    if link.get("http_status") is not None:
                        enrichment_lines.append(f"HTTP {link['http_status']}")

                    if link.get("mime_type"):
                        enrichment_lines.append(link["mime_type"])

                    if link.get("file_size") is not None:
                        # Format file size in human-readable format
                        size = link["file_size"]
                        if size < 1024:
                            size_str = f"{size} B"
                        elif size < 1024 * 1024:
                            size_str = f"{size / 1024:.1f} KB"
                        elif size < 1024 * 1024 * 1024:
                            size_str = f"{size / (1024 * 1024):.1f} MB"
                        else:
                            size_str = f"{size / (1024 * 1024 * 1024):.1f} GB"
                        enrichment_lines.append(size_str)

                    if link.get("filename"):
                        enrichment_lines.append(f"File: {link['filename']}")

                    if link.get("page_title"):
                        title = link["page_title"]
                        if len(title) > 60:
                            title = title[:57] + "..."
                        enrichment_lines.append(f"Title: {title}")

                    if link.get("page_language"):
                        enrichment_lines.append(f"Lang: {link['page_language']}")

                    if enrichment_lines:
                        click.echo(f"  {' | '.join(enrichment_lines)}")

                click.echo("")

        # Show summary
        total = len(all_links)
        shown = len(filtered_links)
        if only_internal or only_external:
            filter_type = "internal" if only_internal else "external"
            click.echo(f"Showing {shown} {filter_type} links (of {total} total)", err=True)
        else:
            click.echo(f"Total: {shown} links", err=True)

    except (ConnectionError, TimeoutError, RuntimeError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@click.command()
@click.option(
    "--format",
    type=click.Choice(["summary", "full"]),
    default="summary",
    help="Output format (summary or full article)",
)
@click.option(
    "--language", "--lang", type=str, default=None, help="Language for AI output (overrides config)"
)
@click.option("--debug", is_flag=True, help="Show the full prompt instead of calling AI")
def summarize(format, language, debug):
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
    script_path = Path(__file__).parent.parent / "scripts" / "extract_article.js"

    if not script_path.exists():
        click.echo(f"Error: Script not found: {script_path}", err=True)
        sys.exit(1)

    try:
        with builtin_open(script_path) as f:
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
        page_lang = article.get("lang")

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

        # Determine target language for AI
        target_lang = get_ai_language(language_override=language, page_lang=page_lang)

        # Generate summary using mods
        click.echo(f"Generating summary for: {title}", err=True)

        # Read the prompt file
        prompt_path = Path(__file__).parent.parent.parent / "prompts" / "summary.prompt"

        if not prompt_path.exists():
            click.echo(f"Error: Prompt file not found: {prompt_path}", err=True)
            sys.exit(1)

        with builtin_open(prompt_path) as f:
            prompt = f.read().strip()

        # Add language instruction if specified
        if target_lang:
            prompt = f"{prompt}\n\nIMPORTANT: Provide your response in {target_lang} language."

        # Prepare the input for mods
        full_input = f"{prompt}\n\nTitle: {title}\n\n{content}"

        # Debug mode: show the full prompt instead of calling AI
        if debug:
            click.echo("=" * 80)
            click.echo("DEBUG: Full prompt that would be sent to AI")
            click.echo("=" * 80)
            click.echo()
            if byline:
                click.echo(f"Article by: {byline}")
                click.echo()
            click.echo(full_input)
            click.echo()
            click.echo("=" * 80)
            return

        # Call mods
        try:
            result = subprocess.run(
                ["mods"], input=full_input, text=True, capture_output=True, check=True
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
