# zen/cli.py Structure Analysis
**File Size:** 4,093 lines | **Total CLI Commands:** 30+ main commands + 10+ subcommands

---

## 1. SHARED UTILITIES & INFRASTRUCTURE (Lines 1-127)

### Core Utilities (Candidates for base.py)
- **format_output()** [Line 25-45]: Formats execution results (JSON/raw/auto modes)
- **get_ai_language()** [Line 48-82]: Language detection for AI operations (CLI > config > page > default)
- **CustomGroup** class [Line 85-126]: Custom Click group for better help formatting

### Global Imports & Constants
```python
# Built-in saves (to avoid shadowing by Click commands)
_builtin_open = open  # Line 21
_builtin_next = next  # Line 22
```

### Key Dependencies
- `click` - CLI framework
- `json` - Output formatting
- `subprocess` - External command execution
- `pathlib.Path` - File operations
- `zen.client.BridgeClient` - Browser communication
- `zen.config` - Configuration management

---

## 2. COMMAND CATEGORIZATION

### A. EXECUTION COMMANDS (Lines 136-223)
**2 commands** - Execute JavaScript directly

| Line | Command | Type | Purpose |
|------|---------|------|---------|
| 145 | `eval` | @cli.command() | Execute inline JS code or from stdin |
| 202 | `exec` | @cli.command() | Execute JS from file |

**Shared Helper:** `format_output()` - Both use for result formatting

---

### B. INSPECTION & ELEMENT SELECTION (Lines 1959-2190)
**3 commands** - DOM inspection and element metadata

| Line | Command | Type | Options | Helper Script |
|------|---------|------|---------|----------------|
| 1961 | `inspect` | @cli.command() | selector (optional) | get_inspected.js |
| 2030 | `inspected` | @cli.command() | None | get_inspected.js |
| 2909 | `screenshot` | @cli.command() | --selector, --output | screenshot_element.js |

**Flow:** `inspect` -> marks element -> calls `inspected` internally

---

### C. INTERACTION COMMANDS (Lines 2192-2413)
**8 commands** - Mouse and keyboard interactions

| Line | Command | Type | Selector | Helper Script |
|------|---------|------|----------|----------------|
| 2194 | `click` | @cli.command(name="click") | required, default=$0 | click_element.js |
| 2214 | `double-click` | @cli.command(name="double-click") | required, default=$0 | click_element.js |
| 2230 | `doubleclick` | HIDDEN ALIAS | required, default=$0 | click_element.js |
| 2237 | `right-click` | @cli.command(name="right-click") | required, default=$0 | click_element.js |
| 2253 | `rightclick` | HIDDEN ALIAS | required, default=$0 | click_element.js |
| 2317 | `wait` | @cli.command() | selector, --timeout, --visible/--hidden/--text | wait_for.js |
| 1893 | `send` | @cli.command() | text, --selector | send_keys.js |

**Helper Function:** `_perform_click()` [Line 2258-2308] - Abstraction for all click types

---

### D. NAVIGATION COMMANDS (Lines 2425-2635)
**6 commands** - Browser history and page loading

| Line | Command | Type | Options |
|------|---------|------|---------|
| 2425 | `open` | @cli.command() | url, --wait, --timeout |
| 2507 | `back` | @cli.command() | None |
| 2537 | `previous` | HIDDEN ALIAS | Calls `back` |
| 2544 | `forward` | @cli.command() | None |
| 2574 | `next` | HIDDEN ALIAS | Calls `forward` |
| 2582 | `reload` | @cli.command() | --hard |
| 2622 | `refresh` | HIDDEN ALIAS | Calls `reload` |

**Pattern:** Simple JavaScript execution (window.history, window.location)

---

### E. COOKIE MANAGEMENT (Lines 2638-2802)
**6 commands** - Cookie manipulation (GROUP + 5 subcommands)

| Line | Command | Type | Purpose |
|------|---------|------|---------|
| 2639 | `cookies` | @cli.group() | Cookie management group |
| 2645 | `cookies list` | @cookies.command() | List all cookies |
| 2657 | `cookies get` | @cookies.command() | Get specific cookie |
| 2680 | `cookies set` | @cookies.command() | Set cookie with options |
| 2706 | `cookies delete` | @cookies.command() | Delete specific cookie |
| 2717 | `cookies clear` | @cookies.command() | Clear all cookies |

**Helper Function:** `_execute_cookie_action()` [Line 2727-2802] - Unified cookie operations

---

### F. SELECTION & DATA COMMANDS (Lines 2805-2899)
**1 command** - Text selection retrieval

| Line | Command | Type | Options | Helper Script |
|------|---------|------|---------|----------------|
| 2807 | `selected` | @cli.command() | --raw | get_selection.js |

---

### G. WATCH COMMANDS (Lines 2997-3084)
**2 commands** - Real-time event monitoring (GROUP + 1 subcommand)

| Line | Command | Type | Purpose |
|------|---------|------|---------|
| 2998 | `watch` | @cli.group() | Event watching group |
| 3004 | `watch input` | @watch.command() | Monitor keyboard input |
| 3347 | `watch all` | @watch.command() | Monitor all interactions |

---

### H. CONTROL COMMAND (Lines 3086-3344)
**1 command** - Interactive browser control

| Line | Command | Type | Key Features |
|------|---------|------|--------------|
| 3087 | `control` | @cli.command() | Terminal-to-browser key forwarding, accessibility support, auto-restart on navigation |

**Helper Script:** control.js with 3 actions (start/send/stop)
**Special Features:** 
- Raw terminal mode
- Accessibility name announcement
- Refocus message handling
- macOS `say` command integration

---

### I. CONTENT EXTRACTION COMMANDS (Lines 3443-3946)
**4 commands** - AI-powered content analysis

| Line | Command | Type | Options | Helper Scripts | AI Tool |
|------|---------|------|---------|-----------------|---------|
| 3448 | `describe` | @cli.command() | --language, --debug | extract_page_structure.js | mods |
| 3558 | `outline` | @cli.command() | None | extract_outline.js | None |
| 3792 | `links` | @cli.command() | --only-internal/external, --alphabetically, --only-urls, --json, --enrich-external | extract_links.js | curl (for enrichment) |
| 3960 | `summarize` | @cli.command() | --format (summary/full), --language, --debug | extract_article.js | mods |

**Helper Functions:**
- `_enrich_link_metadata()` [Line 3625-3722] - Fetch HTTP headers, MIME type, file size, title
- `_enrich_external_links()` [Line 3733-3776] - Parallel enrichment with ThreadPoolExecutor

---

### J. SERVER COMMANDS (Lines 1406-1479)
**4 commands** - Bridge server management (GROUP + 3 subcommands)

| Line | Command | Type | Purpose |
|------|---------|------|---------|
| 1407 | `server` | @cli.group() | Server management group |
| 1415 | `server start` | @server.command() | Start WebSocket server (foreground or daemon) |
| 1456 | `server status` | @server.command() | Check server status |
| 1475 | `server stop` | @server.command() | Stop server (daemon mode info) |

---

### K. UTILITY COMMANDS (Lines 421-1603)
**4 commands** - Information and setup

| Line | Command | Type | Purpose | Features |
|------|---------|------|---------|----------|
| 426 | `info` | @cli.command() | Page information | --extended (meta, cookies, scripts, etc.), --json |
| 1482 | `repl` | @cli.command() | Interactive REPL | Connect to server, execute JS interactively |
| 1607 | `userscript` | @cli.command() | Show userscript | Display installation instructions |
| 1635 | `download` | @cli.command() | Download page files | --output, --list, --timeout, interactive selection |

---

### L. MAIN CLI GROUP (Line 129-133)
```python
@click.group(cls=CustomGroup)
@click.version_option(version=__version__)
def cli():
```

---

## 3. COMMAND DEPENDENCIES & RELATIONSHIPS

### Direct Calls Between Commands
```
inspect → inspected (called internally at line 2022)
previous → back (ctx.invoke at line 2540)
next → forward (ctx.invoke at line 2576)
refresh → reload (ctx.invoke at line 2635)
```

### Shared Helper Functions
```
_perform_click()     → Used by: click, double-click, right-click
_execute_cookie_action() → Used by: cookies list/get/set/delete/clear
format_output()      → Used by: eval, exec, repl, highlight
get_ai_language()    → Used by: describe, summarize
_enrich_link_metadata() → Used by: _enrich_external_links
_enrich_external_links() → Used by: links command
```

### Helper Scripts (Located in zen/scripts/)
```
extract_page_structure.js → describe command
extract_outline.js → outline command
extract_links.js → links command
extract_article.js → summarize command
click_element.js → click, double-click, right-click
wait_for.js → wait command
send_keys.js → send command
get_inspected.js → inspected command
screenshot_element.js → screenshot command
cookies.js → cookies group
get_selection.js → selected command
watch_keyboard.js → watch input command
watch_all.js → watch all command
control.js → control command
find_downloads.js → download command
```

---

## 4. PROPOSED REFACTORING STRUCTURE

### Target: Split into 8-10 focused modules (each <400 lines)

```
zen/cli/
├── __init__.py                    # Entry point, main CLI group
├── base.py                        # Shared utilities (~150 lines)
│   ├── format_output()
│   ├── get_ai_language()
│   ├── CustomGroup class
│   └── Common constants/imports
├── exec.py                        # eval, exec (~100 lines)
├── inspect.py                     # inspect, inspected, screenshot (~150 lines)
├── interaction.py                 # click, double-click, right-click, wait, send (~180 lines)
├── navigation.py                  # open, back, forward, reload, refresh, previous, next (~150 lines)
├── cookies.py                     # cookies group + all subcommands (~180 lines)
├── selection.py                   # selected command (~80 lines)
├── watch.py                       # watch group, input, all; control (~250 lines)
├── extraction.py                  # describe, outline, links, summarize (~400 lines)
│   ├── Helper: _enrich_link_metadata()
│   ├── Helper: _enrich_external_links()
├── server.py                      # server group + start, status, stop (~100 lines)
└── util.py                        # info, repl, userscript, download, highlight (~250 lines)
```

### Module Dependencies:
```
All modules depend on:
  - base.py (utilities, CustomGroup)
  - zen.client.BridgeClient
  - zen.config

execution.py, interaction.py, navigation.py, selection.py:
  - base.format_output()

watch.py, extraction.py:
  - base.get_ai_language()

extraction.py:
  - subprocess for AI tools (mods, curl)

util.py (download):
  - requests library
  - urllib.parse
  - ThreadPoolExecutor for parallel downloads
```

---

## 5. KEY STATISTICS

| Category | Count |
|----------|-------|
| Total CLI commands | 30+ |
| Top-level commands | ~20 |
| Subcommands | ~10 |
| Command groups | 4 (server, cookies, watch) |
| Hidden/alias commands | 4 |
| Helper functions | 8 |
| Helper scripts | 14 |
| Lines of code | 4,093 |
| Imports | 13 main modules |

---

## 6. IMPORT ANALYSIS

### Essential Dependencies
```python
import click                    # CLI framework
import json                     # Output formatting
import re                       # Pattern matching (links, parsing)
import os                       # Path operations
import sys                      # Exit codes, stdin/stdout
import subprocess               # External tools (mods, curl, say)
import signal                   # Ctrl+C handling
from pathlib import Path        # Modern path handling
from concurrent.futures import ThreadPoolExecutor, as_completed  # Parallel downloads

# Internal
from zen.client import BridgeClient    # Browser communication
from zen import config as zen_config    # Configuration
from zen import __version__            # Version info
```

### Optional Dependencies (conditional imports)
```python
import requests                 # download command, enrich_external_links
import base64                   # screenshot command
from datetime import datetime   # screenshot filename generation
from urllib.parse import urlparse   # download command
import termios, tty, select     # control command (Unix/Linux/macOS)
import time                     # Polling in watch/control commands
```

---

## 7. COMMAND LINE PATTERNS

### Most Common Pattern (20+ commands)
```python
@cli.command()
@click.option(...)
def cmd_name(args):
    client = BridgeClient()
    if not client.is_alive():
        click.echo("Error: Bridge server not running", err=True)
        sys.exit(1)
    
    # Execute or interact with browser
    result = client.execute(code, timeout=...)
    # Handle result
```

### Group Commands Pattern (4 groups)
```python
@cli.group()
def group_name():
    pass

@group_name.command()
def subcommand():
    ...
```

### Advanced Patterns
- **Raw terminal mode** (control command): Uses termios/tty for keyboard capture
- **Polling loops** (watch/control): Continuous execution with Ctrl+C handling
- **Script template injection** (click, wait, cookies): Placeholder replacement
- **Parallel execution** (_enrich_external_links): ThreadPoolExecutor

---

## 8. ERROR HANDLING PATTERNS

### Consistent throughout:
1. Check if server is alive
2. Handle ConnectionError, TimeoutError, RuntimeError
3. Exit with sys.exit(1) on failure
4. Print errors to stderr with err=True

### Example:
```python
try:
    result = client.execute(code, timeout=10.0)
    if not result.get("ok"):
        click.echo(f"Error: {result.get('error')}", err=True)
        sys.exit(1)
except (ConnectionError, TimeoutError, RuntimeError) as e:
    click.echo(f"Error: {e}", err=True)
    sys.exit(1)
```

---

## REFACTORING RECOMMENDATIONS

### Priority 1: Extract (High Impact)
- **base.py**: format_output, get_ai_language, CustomGroup (used everywhere)
- **exec.py**: eval, exec commands (simple, isolated)
- **navigation.py**: back, forward, reload, open (simple, isolated)

### Priority 2: Extract (Medium Impact)
- **cookies.py**: self-contained cookie operations
- **interaction.py**: click operations + wait (uses _perform_click helper)
- **extraction.py**: Large, complex, but self-contained

### Priority 3: Extract (Lower Priority)
- **watch.py**: Contains both watch group and control command
- **util.py**: Mixed utilities (info, repl, download, highlight)
- **server.py**: Small but important

### Post-Refactor:
- Create `zen/cli/__init__.py` that imports and registers all command groups
- Update `setup.py` entry_point to point to new cli.__init__:cli
- All helper scripts can stay in `zen/scripts/` unchanged

