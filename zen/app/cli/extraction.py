"""
Content extraction and AI-powered analysis commands.

This module provides commands for extracting and analyzing page content:
- describe: AI-powered page description for screen reader users
- do: AI-powered action matching for natural language navigation
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
from zen.services.action_cache import ActionCache
from zen.services.action_matcher import ActionMatcher
from zen.services.content_cache import ContentCache
from zen.services.ai_integration import get_ai_service
from zen.services.bridge_executor import get_executor
from zen.services.script_loader import ScriptLoader


def _parse_page_structure(markdown_structure: str) -> dict:
    """Parse markdown page structure to extract data for fingerprinting."""
    data = {}

    # Extract title
    title_match = re.search(r"\*\*Title:\*\* (.+)", markdown_structure)
    data["title"] = title_match.group(1) if title_match else ""

    # Extract headings
    headings = []
    for match in re.finditer(r"^(#{1,6})\s+(.+)$", markdown_structure, re.MULTILINE):
        level = len(match.group(1))
        text = match.group(2).strip()
        headings.append({"level": level, "text": text})
    data["headings"] = headings

    # Extract landmarks (look for sections like ### Landmarks)
    landmarks = []
    landmarks_section = re.search(r"###\s+Landmarks\s*\n(.+?)(?:\n#{1,3}\s|$)", markdown_structure, re.DOTALL)
    if landmarks_section:
        for line in landmarks_section.group(1).split("\n"):
            if line.strip().startswith("-"):
                # Extract landmark role (e.g., "- navigation")
                role = line.strip().lstrip("- ").split()[0].lower()
                landmarks.append({"role": role})
    data["landmarks"] = landmarks

    # Extract counts
    link_match = re.search(r"(\d+)\s+links?", markdown_structure)
    data["linkCount"] = int(link_match.group(1)) if link_match else 0

    button_match = re.search(r"(\d+)\s+buttons?", markdown_structure)
    data["buttonCount"] = int(button_match.group(1)) if button_match else 0

    image_match = re.search(r"(\d+)\s+images?", markdown_structure)
    data["imageCount"] = int(image_match.group(1)) if image_match else 0

    # Extract main text excerpt (first paragraph or content)
    text_match = re.search(r"###\s+Main Content\s*\n(.+?)(?:\n#{1,3}\s|$)", markdown_structure, re.DOTALL)
    if text_match:
        data["mainText"] = text_match.group(1).strip()[:200]
    else:
        data["mainText"] = ""

    return data


@click.command()
@click.option(
    "--language", "--lang", type=str, default=None, help="Language for AI output (overrides config)"
)
@click.option("--debug", is_flag=True, help="Show the full prompt instead of calling AI")
@click.option("--force-refresh", is_flag=True, help="Force refresh, bypass cache")
def describe(language, debug, force_refresh):
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
    script_path = Path(__file__).parent.parent.parent / "scripts" / "extract_page_structure.js"

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

        # Extract URL and parse structure for caching
        url_match = re.search(r"\*\*URL:\*\* (.+)", page_structure)
        current_url = url_match.group(1) if url_match else ""

        # Parse page structure for fingerprinting
        page_data = _parse_page_structure(page_structure)

        # Try cache first (unless force refresh or debug mode)
        content_cache = ContentCache()
        cached_result = None

        if not force_refresh and not debug and content_cache.is_enabled("describe"):
            fingerprint = content_cache.create_describe_fingerprint(page_data)
            cached_result = content_cache.get_cached_content(current_url, "describe", fingerprint, target_lang or "auto")

            if cached_result:
                similarity = cached_result["similarity"]
                age_seconds = cached_result["age_seconds"]

                # Format age
                if age_seconds < 3600:
                    age_str = f"{age_seconds // 60} minutes ago"
                elif age_seconds < 86400:
                    age_str = f"{age_seconds // 3600} hours ago"
                else:
                    age_str = f"{age_seconds // 86400} days ago"

                click.echo(click.style(f"✓ Using cached description (similarity: {similarity:.0%}, cached {age_str}) [CACHED]", fg="cyan", bold=True), err=True)
                click.echo()
                click.echo(cached_result["output"])
                return

        # Read the prompt
        prompt_path = Path(__file__).parent.parent.parent.parent / "prompts" / "describe.prompt"

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

        if force_refresh:
            click.echo("Generating fresh description... [AI - Force Refresh]", err=True)
        else:
            click.echo("Generating description... [AI]", err=True)

        # Call mods
        try:
            result = subprocess.run(
                ["mods"], input=full_input, text=True, capture_output=True, check=True
            )

            output = result.stdout

            # Store in cache for future use
            if content_cache.is_enabled("describe") and current_url:
                fingerprint = content_cache.create_describe_fingerprint(page_data)
                content_cache.store_content(current_url, "describe", fingerprint, output, target_lang or "auto")
                click.echo(click.style("✓ Description cached for future use", fg="green"), err=True)
                click.echo()

            click.echo(output)

        except subprocess.CalledProcessError as e:
            click.echo(f"Error calling mods: {e}", err=True)
            if e.stderr:
                click.echo(e.stderr, err=True)
            sys.exit(1)

    except (ConnectionError, TimeoutError, RuntimeError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def _execute_element_action(client: BridgeClient, action_id: str, element: dict):
    """Helper function to execute an action on an element."""
    # Step 1: Get element info and highlight it
    inspect_script = f"""
(function() {{
    const element = document.querySelector('.{action_id}');
    if (!element) {{
        return {{ ok: false, error: 'Element not found' }};
    }}

    // Scroll element into view
    element.scrollIntoView({{ behavior: 'smooth', block: 'center' }});

    // Highlight briefly
    const originalOutline = element.style.outline;
    element.style.outline = '3px solid #00ff00';

    setTimeout(() => {{
        element.style.outline = originalOutline;
    }}, 500);

    const result = {{
        ok: true,
        element: {{
            tag: element.tagName.toLowerCase(),
            text: element.textContent.trim().substring(0, 100),
            href: element.href || null
        }},
        action: 'click'
    }};

    // Determine action type based on element
    if (element.href) {{
        // Parse URLs to get path
        try {{
            const currentUrl = new URL(window.location.href);
            const targetUrl = new URL(element.href);

            result.action = 'navigate';
            result.element.path = targetUrl.pathname + targetUrl.search + targetUrl.hash;
            result.element.isExternal = currentUrl.origin !== targetUrl.origin;
        }} catch (e) {{
            // If URL parsing fails, keep as click
        }}
    }}

    return result;
}})();
"""

    # Get element info first
    result = client.execute(inspect_script, timeout=10.0)

    if not result.get("ok"):
        click.echo(click.style(f"✗ Failed to execute action: {result.get('error')}", fg="red"), err=True)
        sys.exit(1)

    action_result = result.get("result", {})
    element_info = action_result.get("element", {})
    action_type = action_result.get("action", "click")

    # Step 2: Execute the action (navigate or click)
    if action_type == "navigate":
        # Navigate using window.location.href
        navigate_script = f"""
(function() {{
    const element = document.querySelector('.{action_id}');
    if (element && element.href) {{
        window.location.href = element.href;
    }}
    return {{ ok: true }};
}})();
"""
        client.execute(navigate_script, timeout=5.0)

        # Show navigation info
        click.echo(click.style("✓ Action executed successfully!", fg="green", bold=True))
        path = element_info.get("path", "")
        is_external = element_info.get("isExternal", False)

        if is_external:
            click.echo(f"  Navigated to: {element_info.get('href')}")
        else:
            click.echo(f"  Navigated to: {path}")

        if element_info.get('text'):
            click.echo(f"  Text: {element_info.get('text')}")
    else:
        # Regular click for non-links
        click_script = f"""
(function() {{
    const element = document.querySelector('.{action_id}');
    if (element) {{
        element.click();
    }}
    return {{ ok: true }};
}})();
"""
        client.execute(click_script, timeout=5.0)

        # Show click info
        click.echo(click.style("✓ Action executed successfully!", fg="green", bold=True))
        click.echo(f"  Clicked: <{element_info.get('tag')}>")
        if element_info.get('text'):
            click.echo(f"  Text: {element_info.get('text')}")


@click.command()
@click.argument("instruction", type=str)
@click.option("--debug", is_flag=True, help="Show the full prompt instead of calling AI")
@click.option("--no-execute", is_flag=True, help="Show matches but don't execute any actions")
@click.option("--force-ai", is_flag=True, help="Force AI matching, bypass cache and literal matching")
def do(instruction, debug, no_execute, force_ai):
    """
    Find and execute actionable elements matching a natural language instruction.

    This command analyzes the page for clickable elements (links, buttons, forms)
    and uses AI to match them with your instruction. It adds temporary classes
    to actionable elements and returns a ranked list of matches with probability
    scores.

    If the top match has a probability >= 75%, it automatically executes the action.
    For lower confidence matches, it asks for confirmation before executing.

    The element is briefly highlighted in green before clicking, and you'll see
    confirmation of what was clicked.

    Examples:
        zen do "Go to the homepage"          # Auto-executes if high confidence
        zen do "Click the login button"      # Asks for confirmation if lower confidence
        zen do "Search for products"
        zen do "Submit form" --no-execute    # Just show matches, don't execute
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
    script_path = Path(__file__).parent.parent.parent / "scripts" / "extract_actionable_elements.js"

    if not script_path.exists():
        click.echo(f"Error: Script not found: {script_path}", err=True)
        sys.exit(1)

    try:
        with builtin_open(script_path) as f:
            script = f.read()

        click.echo("Analyzing page for actionable elements...", err=True)
        result = client.execute(script, timeout=30.0)

        if not result.get("ok"):
            click.echo(f"Error: {result.get('error')}", err=True)
            sys.exit(1)

        # Get the extracted data
        page_data = result.get("result", {})

        if not page_data or not isinstance(page_data, dict):
            click.echo("Error: No page data extracted", err=True)
            sys.exit(1)

        actionable_elements = page_data.get("actionableElements", [])
        total_actions = page_data.get("totalActions", 0)

        if total_actions == 0:
            click.echo("No actionable elements found on this page.", err=True)
            sys.exit(0)

        click.echo(f"Found {total_actions} actionable elements", err=True)

        # Initialize cache and matcher
        cache = ActionCache()
        matcher = ActionMatcher(cache.config)

        # Get current URL
        current_url = page_data.get("pageUrl", "")

        # Normalize the action
        action_normalized = cache.normalize_action(instruction)

        # Variables to track matching method and result
        matched_element = None
        match_method = None
        match_score = 0.0

        # WATERFALL APPROACH: Try multiple strategies before falling back to AI
        if not force_ai:
            click.echo(f"Searching for matches (action: '{action_normalized}')...", err=True)

            # 1. TRY CACHE
            if cache.is_enabled():
                fingerprint = cache.calculate_page_fingerprint(page_data)
                cached_action = cache.get_cached_action(current_url, action_normalized, fingerprint)

                if cached_action:
                    # Try to find element using cached identifier
                    cached_id = cached_action["identifier"]
                    for el in actionable_elements:
                        if (el.get("type") == cached_id.get("type") and
                            el.get("text") == cached_id.get("text") and
                            el.get("href") == cached_id.get("href")):
                            matched_element = el
                            match_method = "CACHED"
                            match_score = 1.0
                            click.echo(click.style(f"✓ Found cached match (similarity: {cached_action['similarity']:.0%})", fg="cyan", bold=True), err=True)
                            break

            # 2. TRY LITERAL MATCHING
            if not matched_element:
                literal_match = matcher.find_literal_match(action_normalized, actionable_elements)
                if literal_match:
                    matched_element = literal_match["element"]
                    match_method = "LITERAL"
                    match_score = literal_match["score"]
                    click.echo(click.style(f"✓ Found literal match (score: {match_score:.0%})", fg="cyan", bold=True), err=True)

            # 3. TRY COMMON ACTIONS
            if not matched_element:
                common_match = matcher.find_common_action_match(action_normalized, actionable_elements)
                if common_match:
                    matched_element = common_match["element"]
                    match_method = "COMMON"
                    match_score = common_match["score"]
                    click.echo(click.style(f"✓ Found common action match (score: {match_score:.0%})", fg="cyan", bold=True), err=True)

            # 4. TRY ADVANCED MATCHING (Fuzzy + Synonyms)
            if not matched_element:
                # Try fuzzy matching
                fuzzy_match = matcher.find_fuzzy_match(action_normalized, actionable_elements)
                if fuzzy_match:
                    matched_element = fuzzy_match["element"]
                    match_method = "FUZZY"
                    match_score = fuzzy_match["score"]
                    click.echo(click.style(f"✓ Found fuzzy match (score: {match_score:.0%})", fg="cyan", bold=True), err=True)

            if not matched_element:
                # Try synonym matching
                synonym_match = matcher.find_synonym_match(action_normalized, actionable_elements)
                if synonym_match:
                    matched_element = synonym_match["element"]
                    match_method = "SYNONYM"
                    match_score = synonym_match["score"]
                    click.echo(click.style(f"✓ Found synonym match (score: {match_score:.0%})", fg="cyan", bold=True), err=True)

        # If we found a match without AI, skip to execution
        if matched_element and not debug:
            # Determine execution based on match score
            should_execute = False

            if match_score >= 1.0:
                # Perfect match - auto-execute
                click.echo(click.style(f"Perfect match! Executing action... [{match_method}]", fg="green", bold=True))
                should_execute = True
            elif match_score >= 0.8:
                # Good match - ask for confirmation
                click.echo()
                click.echo(click.style(f"Found match (confidence: {match_score:.0%}) [{match_method}]", fg="yellow", bold=True))
                click.echo(f"  → {matched_element.get('type')}: {matched_element.get('text', 'N/A')[:80]}")
                if matched_element.get('href'):
                    click.echo(f"  → URL: {matched_element.get('href')}")
                click.echo()

                if not no_execute and click.confirm("Execute action?", default=True):
                    should_execute = True
                else:
                    click.echo("Action cancelled.")
            else:
                # Low confidence - fall back to AI
                matched_element = None
                click.echo(click.style(f"Match confidence too low ({match_score:.0%}), falling back to AI...", fg="yellow"), err=True)

            # Execute if approved
            if should_execute and not no_execute:
                click.echo()
                click.echo("Executing action...", err=True)

                # Get the action ID for this element
                action_id = matched_element.get("actionId")

                # Execute using the existing execution logic (will add below)
                # For now, set a flag to skip AI and use this element
                _execute_element_action(client, action_id, matched_element)

                # Store in cache for future use
                if cache.is_enabled() and match_method != "CACHED":
                    cache.store_action(current_url, instruction, action_normalized, matched_element, page_data)
                    click.echo(click.style("✓ Action cached for future use", fg="green"), err=True)

                return  # Exit successfully without calling AI

        # If no match found or --force-ai, continue to AI
        if not matched_element or force_ai:
            if force_ai:
                click.echo(click.style("Forcing AI matching (--force-ai)...", fg="yellow"), err=True)
            else:
                click.echo(click.style("No automatic match found, using AI...", fg="yellow"), err=True)

        # Read the prompt
        prompt_path = Path(__file__).parent.parent.parent.parent / "prompts" / "do.prompt"

        if not prompt_path.exists():
            click.echo(f"Error: Prompt file not found: {prompt_path}", err=True)
            sys.exit(1)

        with builtin_open(prompt_path) as f:
            prompt = f.read().strip()

        # Format the page data for the AI
        page_structure = {
            "pageTitle": page_data.get("pageTitle"),
            "pageUrl": page_data.get("pageUrl"),
            "language": page_data.get("language"),
            "landmarks": page_data.get("landmarks", []),
            "headings": page_data.get("headings", []),
            "actionableElements": actionable_elements
        }

        # Combine prompt with instruction and page data
        full_input = f"{prompt}\n\n---\n\nUSER INSTRUCTION:\n{instruction}\n\n---\n\nPAGE DATA:\n{json.dumps(page_structure, indent=2)}"

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

        click.echo("Finding matching actions...", err=True)

        # Call mods
        try:
            result = subprocess.run(
                ["mods"], input=full_input, text=True, capture_output=True, check=True
            )

            # Parse the JSON response
            raw_output = result.stdout.strip()
            try:
                response = json.loads(raw_output)
            except json.JSONDecodeError:
                # Try to strip markdown code blocks (```json ... ```)
                if raw_output.startswith("```"):
                    # Remove opening ```json or ``` and closing ```
                    lines = raw_output.split("\n")
                    if lines[0].startswith("```"):
                        lines = lines[1:]  # Remove first line
                    if lines and lines[-1].strip() == "```":
                        lines = lines[:-1]  # Remove last line
                    raw_output = "\n".join(lines).strip()

                    try:
                        response = json.loads(raw_output)
                    except json.JSONDecodeError as e:
                        click.echo(f"Error: AI returned invalid JSON even after stripping markdown: {e}", err=True)
                        click.echo("Raw response:", err=True)
                        click.echo(result.stdout, err=True)
                        sys.exit(1)
                else:
                    click.echo(f"Error: AI returned invalid JSON", err=True)
                    click.echo("Raw response:", err=True)
                    click.echo(result.stdout, err=True)
                    sys.exit(1)

            # Output the results
            click.echo()
            click.echo(f"Interpretation: {response.get('interpretation', 'N/A')}")
            click.echo()

            matches = response.get("matches", [])
            if not matches:
                click.echo("No matching actions found.")
                sys.exit(0)

            click.echo(f"Found {len(matches)} matching action(s):")
            click.echo()

            for i, match in enumerate(matches, 1):
                action_id = match.get("actionId")
                probability = match.get("probability", 0)
                reasoning = match.get("reasoning", "")

                # Find the full element details
                element = next((el for el in actionable_elements if el.get("actionId") == action_id), None)

                click.echo(f"{i}. {action_id} (probability: {probability:.0%})")
                if element:
                    click.echo(f"   Type: {element.get('type')}")
                    click.echo(f"   Text: {element.get('text', 'N/A')[:100]}")
                    if element.get('href'):
                        click.echo(f"   URL: {element.get('href')}")
                    if element.get('context'):
                        ctx = element['context']
                        if ctx.get('type') == 'heading':
                            click.echo(f"   Context: Under heading '{ctx.get('text', '')[:50]}'")
                        elif ctx.get('type') == 'landmark':
                            click.echo(f"   Context: In {ctx.get('role')} landmark")
                click.echo(f"   Reasoning: {reasoning}")
                click.echo()

            # Check if we should auto-execute or ask for confirmation
            if not no_execute:
                top_match = matches[0]
                top_probability = top_match.get("probability", 0)
                top_action_id = top_match.get("actionId")
                top_element = next((el for el in actionable_elements if el.get("actionId") == top_action_id), None)

                should_execute = False

                if top_probability >= 0.75:
                    # High confidence - auto-execute
                    click.echo(click.style("High confidence match! Executing action... [AI]", fg="green", bold=True))
                    should_execute = True
                else:
                    # Lower confidence - ask for confirmation
                    click.echo()
                    click.echo(click.style("Would you like to execute this action?", fg="yellow", bold=True))
                    if top_element:
                        click.echo(f"  → {top_element.get('type')}: {top_element.get('text', 'N/A')[:80]}")
                        if top_element.get('href'):
                            click.echo(f"  → URL: {top_element.get('href')}")
                    click.echo()

                    # Ask for confirmation
                    if click.confirm("Execute action?", default=True):
                        should_execute = True
                    else:
                        click.echo("Action cancelled.")

                if should_execute:
                    # Execute the action
                    click.echo()
                    click.echo("Executing action...", err=True)

                    try:
                        _execute_element_action(client, top_action_id, top_element)

                        # Store in cache for future use [AI]
                        if cache.is_enabled():
                            cache.store_action(current_url, instruction, action_normalized, top_element, page_data)
                            click.echo(click.style("✓ Action cached for future use [AI]", fg="green"), err=True)

                    except (ConnectionError, TimeoutError, RuntimeError) as e:
                        click.echo(click.style(f"✗ Error executing action: {e}", fg="red"), err=True)
                        sys.exit(1)

            # Output as JSON for easy parsing
            click.echo()
            click.echo("JSON Output:")
            click.echo(json.dumps(response, indent=2))

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
    script_path = Path(__file__).parent.parent.parent / "scripts" / "extract_outline.js"

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
    script_path = Path(__file__).parent.parent.parent / "scripts" / "extract_links.js"

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
@click.option("--force-refresh", is_flag=True, help="Force refresh, bypass cache")
def summarize(format, language, debug, force_refresh):
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
    script_path = Path(__file__).parent.parent.parent / "scripts" / "extract_article.js"

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

        # Get current URL for caching (from article extraction result)
        current_url = article.get("url", "")

        # Prepare article data for fingerprinting
        article_data = {
            "title": title,
            "text": content,
            "publishedDate": article.get("publishedDate", ""),
        }

        # Try cache first (unless force refresh or debug mode)
        content_cache = ContentCache()
        cached_result = None

        if not force_refresh and not debug and content_cache.is_enabled("summarize"):
            fingerprint = content_cache.create_summarize_fingerprint(article_data)
            cached_result = content_cache.get_cached_content(current_url, "summarize", fingerprint, target_lang or "auto")

            if cached_result:
                similarity = cached_result["similarity"]
                age_seconds = cached_result["age_seconds"]

                # Format age
                if age_seconds < 3600:
                    age_str = f"{age_seconds // 60} minutes ago"
                elif age_seconds < 86400:
                    age_str = f"{age_seconds // 3600} hours ago"
                else:
                    age_str = f"{age_seconds // 86400} days ago"

                click.echo(click.style(f"✓ Using cached summary (similarity: {similarity:.0%}, cached {age_str}) [CACHED]", fg="cyan", bold=True), err=True)
                click.echo()
                if byline:
                    click.echo(f"By: {byline}")
                    click.echo("")
                click.echo(cached_result["output"])
                return

        # Generate summary using mods
        if force_refresh:
            click.echo(f"Generating fresh summary for: {title} [AI - Force Refresh]", err=True)
        else:
            click.echo(f"Generating summary for: {title} [AI]", err=True)

        # Read the prompt file
        prompt_path = Path(__file__).parent.parent.parent.parent / "prompts" / "summary.prompt"

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

            output = result.stdout

            # Store in cache for future use
            if content_cache.is_enabled("summarize") and current_url:
                fingerprint = content_cache.create_summarize_fingerprint(article_data)
                content_cache.store_content(current_url, "summarize", fingerprint, output, target_lang or "auto")
                click.echo(click.style("✓ Summary cached for future use", fg="green"), err=True)
                click.echo()

            if byline:
                click.echo(f"By: {byline}")
                click.echo("")
            click.echo(output)

        except subprocess.CalledProcessError as e:
            click.echo(f"Error calling mods: {e}", err=True)
            if e.stderr:
                click.echo(e.stderr, err=True)
            sys.exit(1)

    except (ConnectionError, TimeoutError, RuntimeError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
