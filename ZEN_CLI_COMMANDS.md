# ZEN CLI: DETAILED COMMAND REFERENCE

## All Commands Summary Table

| # | Line | Command | Group | Type | Module | Helpers |
|---|------|---------|-------|------|--------|---------|
| 1 | 145 | eval | - | Top-level | exec.py | format_output() |
| 2 | 202 | exec | - | Top-level | exec.py | format_output() |
| 3 | 426 | info | - | Top-level | util.py | _get_domain_metrics, _get_robots_txt, _get_response_headers |
| 4 | 1415 | server start | server | Subcommand | server.py | - |
| 5 | 1456 | server status | server | Subcommand | server.py | - |
| 6 | 1475 | server stop | server | Subcommand | server.py | - |
| 7 | 1482 | repl | - | Top-level | util.py | format_output() |
| 8 | 1538 | highlight | - | Top-level | util.py | - |
| 9 | 1607 | userscript | - | Top-level | util.py | - |
| 10 | 1635 | download | - | Top-level | util.py | requests |
| 11 | 1893 | send | - | Top-level | interaction.py | send_keys.js |
| 12 | 1961 | inspect | - | Top-level | inspect.py | get_inspected.js |
| 13 | 2030 | inspected | - | Top-level | inspect.py | get_inspected.js |
| 14 | 2194 | click | - | Top-level | interaction.py | _perform_click(), click_element.js |
| 15 | 2214 | double-click | - | Top-level | interaction.py | _perform_click(), click_element.js |
| 16 | 2230 | doubleclick | - | Top-level (hidden) | interaction.py | _perform_click(), click_element.js |
| 17 | 2237 | right-click | - | Top-level | interaction.py | _perform_click(), click_element.js |
| 18 | 2253 | rightclick | - | Top-level (hidden) | interaction.py | _perform_click(), click_element.js |
| 19 | 2317 | wait | - | Top-level | interaction.py | wait_for.js |
| 20 | 2425 | open | - | Top-level | navigation.py | - |
| 21 | 2507 | back | - | Top-level | navigation.py | - |
| 22 | 2537 | previous | - | Top-level (hidden) | navigation.py | - |
| 23 | 2544 | forward | - | Top-level | navigation.py | - |
| 24 | 2574 | next | - | Top-level (hidden) | navigation.py | - |
| 25 | 2582 | reload | - | Top-level | navigation.py | - |
| 26 | 2622 | refresh | - | Top-level (hidden) | navigation.py | - |
| 27 | 2639 | cookies | cookies | Group | cookies.py | - |
| 28 | 2645 | cookies list | cookies | Subcommand | cookies.py | _execute_cookie_action() |
| 29 | 2657 | cookies get | cookies | Subcommand | cookies.py | _execute_cookie_action() |
| 30 | 2680 | cookies set | cookies | Subcommand | cookies.py | _execute_cookie_action() |
| 31 | 2706 | cookies delete | cookies | Subcommand | cookies.py | _execute_cookie_action() |
| 32 | 2717 | cookies clear | cookies | Subcommand | cookies.py | _execute_cookie_action() |
| 33 | 2807 | selected | - | Top-level | selection.py | get_selection.js |
| 34 | 2909 | screenshot | - | Top-level | inspect.py | screenshot_element.js |
| 35 | 2998 | watch | watch | Group | watch.py | - |
| 36 | 3004 | watch input | watch | Subcommand | watch.py | watch_keyboard.js |
| 37 | 3087 | control | - | Top-level | watch.py | control.js |
| 38 | 3347 | watch all | watch | Subcommand | watch.py | watch_all.js |
| 39 | 3448 | describe | - | Top-level | extraction.py | extract_page_structure.js, mods |
| 40 | 3558 | outline | - | Top-level | extraction.py | extract_outline.js |
| 41 | 3792 | links | - | Top-level | extraction.py | extract_links.js, _enrich_link_metadata() |
| 42 | 3960 | summarize | - | Top-level | extraction.py | extract_article.js, mods |

---

## DETAILED COMMAND BREAKDOWN BY MODULE

### MODULE: exec.py (~100 lines)
**Commands:** eval, exec

#### eval (Line 145)
```
zen eval [CODE] [OPTIONS]
Options:
  -f, --file TEXT          Execute code from file
  -t, --timeout FLOAT      Timeout in seconds (default: 10)
  --format [auto|json|raw] Output format (default: auto)
  --url                    Also print page URL
  --title                  Also print page title

Usage Examples:
  zen eval "document.title"
  zen eval "alert('Hello!')"
  zen eval --file script.js
  echo "console.log('test')" | zen eval
```

#### exec (Line 202)
```
zen exec FILEPATH [OPTIONS]
Options:
  -t, --timeout FLOAT      Timeout in seconds (default: 10)
  --format [auto|json|raw] Output format (default: auto)

Usage Examples:
  zen exec script.js
```

**Dependencies:**
- BridgeClient.execute(), BridgeClient.execute_file()
- format_output() [from base.py]

---

### MODULE: inspect.py (~150 lines)
**Commands:** inspect, inspected, screenshot

#### inspect (Line 1961)
```
zen inspect [SELECTOR]
Arguments:
  selector  Optional CSS selector (if omitted, shows currently selected element)

Usage Examples:
  zen inspect "h1"
  zen inspect "#header"
  zen inspect ".main-content"
  zen inspect          # Show currently selected element
```

#### inspected (Line 2030)
```
zen inspected
No arguments

Usage Examples:
  zen inspect "h1"
  zen inspected        # Show details of inspected element
```

#### screenshot (Line 2909)
```
zen screenshot [OPTIONS]
Options:
  -s, --selector TEXT  CSS selector of element to screenshot (required)
  -o, --output TEXT    Output file path (optional, auto-generated if omitted)

Usage Examples:
  zen screenshot --selector "#main"
  zen screenshot -s ".hero-section" -o hero.png
  zen screenshot -s "$0" -o inspected.png
```

**Output:** PNG image file (base64 decoded from canvas)

**Dependencies:**
- get_inspected.js script
- screenshot_element.js script
- base64, datetime, pathlib

---

### MODULE: interaction.py (~180 lines)
**Commands:** click, double-click, doubleclick (hidden), right-click, rightclick (hidden), wait, send

#### click (Line 2194)
```
zen click [SELECTOR]
Arguments:
  selector  CSS selector (default: $0 = last inspected element)

Usage Examples:
  zen inspect "button#submit"
  zen click
  zen click "button#submit"
  zen click ".primary-button"
```

#### double-click (Line 2214)
```
zen double-click [SELECTOR]
Arguments:
  selector  CSS selector (default: $0)

Usage Examples:
  zen double-click "div.item"
  zen inspect "div.item"
  zen double-click
```

#### right-click (Line 2237)
```
zen right-click [SELECTOR]
Arguments:
  selector  CSS selector (default: $0)

Usage Examples:
  zen right-click "a.download-link"
  zen inspect "a.download-link"
  zen right-click
```

#### wait (Line 2317)
```
zen wait SELECTOR [OPTIONS]
Arguments:
  selector  CSS selector to wait for

Options:
  -t, --timeout INT    Timeout in seconds (default: 30)
  --visible            Wait for element to be visible
  --hidden             Wait for element to be hidden
  --text TEXT          Wait for element to contain specific text

Usage Examples:
  zen wait "button#submit"          # Wait to exist
  zen wait ".modal" --visible       # Wait to be visible
  zen wait ".spinner" --hidden      # Wait to be hidden
  zen wait "h1" --text "Success"    # Wait for text
  zen wait "div.result" --timeout 10
```

#### send (Line 1893)
```
zen send TEXT [OPTIONS]
Arguments:
  text  Text to type

Options:
  -s, --selector TEXT  CSS selector of element to type into

Usage Examples:
  zen send "Hello World"
  zen send "test@example.com" --selector "input[type=email]"
```

**Helper Function:** _perform_click(selector, click_type) - abstraction for click types

**Scripts:**
- click_element.js - Handles click, dblclick, contextmenu events
- wait_for.js - Polling-based waiter with multiple modes
- send_keys.js - Character-by-character typing

---

### MODULE: navigation.py (~150 lines)
**Commands:** open, back, forward, reload, previous (hidden), next (hidden), refresh (hidden)

#### open (Line 2425)
```
zen open URL [OPTIONS]
Arguments:
  url  URL to navigate to

Options:
  --wait              Wait for page to finish loading
  -t, --timeout INT   Timeout in seconds (default: 30)

Usage Examples:
  zen open "https://example.com"
  zen open "https://example.com" --wait
  zen open "https://example.com" --wait --timeout 60
```

#### back (Line 2507)
```
zen back
No options/arguments
```

#### forward (Line 2544)
```
zen forward
No options/arguments
```

#### reload (Line 2582)
```
zen reload [OPTIONS]
Options:
  --hard  Hard reload (bypass cache)

Usage Examples:
  zen reload
  zen reload --hard
```

#### Aliases (Hidden)
- `previous` → calls `back`
- `next` → calls `forward`
- `refresh` → calls `reload`

---

### MODULE: cookies.py (~180 lines)
**Group:** cookies (Parent command at line 2639)
**Subcommands:** list, get, set, delete, clear

#### cookies list (Line 2645)
```
zen cookies list
No options
```

#### cookies get (Line 2657)
```
zen cookies get NAME
Arguments:
  name  Cookie name
```

#### cookies set (Line 2680)
```
zen cookies set NAME VALUE [OPTIONS]
Arguments:
  name   Cookie name
  value  Cookie value

Options:
  --max-age INT              Max age in seconds
  --expires TEXT             Expiration date (e.g., 'Wed, 21 Oct 2025 07:28:00 GMT')
  --path TEXT                Cookie path (default: /)
  --domain TEXT              Cookie domain
  --secure                   Secure flag (HTTPS only)
  --same-site [Strict|Lax|None]  SameSite attribute

Usage Examples:
  zen cookies set session_id abc123
  zen cookies set token xyz --max-age 3600
  zen cookies set user_pref dark --path / --secure
```

#### cookies delete (Line 2706)
```
zen cookies delete NAME
Arguments:
  name  Cookie name
```

#### cookies clear (Line 2717)
```
zen cookies clear
No options/arguments
```

**Helper Function:** _execute_cookie_action(action, cookie_name, cookie_value, options)

**Script:** cookies.js (with ACTION/NAME/VALUE/OPTIONS placeholders)

---

### MODULE: selection.py (~80 lines)
**Commands:** selected

#### selected (Line 2807)
```
zen selected [OPTIONS]
Options:
  --raw  Output only the raw text (no metadata)

Usage Examples:
  zen selected                 # Get selection with metadata
  zen selected --raw           # Get just the text
```

**Output:** Selection text + position info + container element details

**Script:** get_selection.js

---

### MODULE: server.py (~100 lines)
**Group:** server (Parent command at line 1407)
**Subcommands:** start, status, stop

#### server start (Line 1415)
```
zen server start [OPTIONS]
Options:
  -p, --port INT    Port to run on (default: 8765)
  -d, --daemon      Run in background

Usage Examples:
  zen server start                # Foreground mode (Ctrl+C to stop)
  zen server start --daemon       # Background mode
  zen server start -p 9000        # Custom port
```

#### server status (Line 1456)
```
zen server status
No options
```

**Output:**
```
Bridge server is running
  Pending requests:   N
  Completed requests: N
```

#### server stop (Line 1475)
```
zen server stop
No options
```

**Note:** Only provides instructions for daemon mode (pkill)

---

### MODULE: watch.py (~250 lines)
**Commands:** control, watch (group)
**Subcommands:** watch input, watch all

#### control (Line 3087)
```
zen control
No options/arguments

Key Features:
  - Raw terminal mode (captures all keyboard input)
  - Sends keys to browser in real-time
  - Supports special keys (arrows, Enter, Tab, Escape)
  - Supports modifier keys (Ctrl, Alt, Shift)
  - Auto-restart on page navigation
  - Accessibility name announcement (macOS 'say' command)
  - Verbose logging optional

Exit: Ctrl+D
```

**Configuration:** Uses zen_config.get_control_config()
**Script:** control.js (with ACTION/KEY_DATA/CONFIG placeholders)

#### watch input (Line 3004)
```
zen watch input
No options/arguments

Features:
  - Real-time keyboard event monitoring
  - Streams all typed characters
  - Ctrl+C to stop

Output: Character-by-character stream
```

**Script:** watch_keyboard.js

#### watch all (Line 3347)
```
zen watch all
No options/arguments

Features:
  - Groups regular typing on single lines
  - Shows special keys separately
  - Displays focus changes with accessible names
  - Ctrl+C to stop

Output: Formatted interaction log
```

**Script:** watch_all.js

---

### MODULE: extraction.py (~400 lines)
**Commands:** describe, outline, links, summarize

#### describe (Line 3448)
```
zen describe [OPTIONS]
Options:
  --language, --lang TEXT  Language for AI output (overrides config)
  --debug                  Show full prompt instead of calling AI

Features:
  - Extracts page structure (landmarks, headings, links, images, forms)
  - Uses AI to create concise description
  - Perfect for blind users to understand page at a glance

Dependencies: mods command (https://github.com/charmbracelet/mods)
Script: extract_page_structure.js
```

#### outline (Line 3558)
```
zen outline
No options/arguments

Features:
  - Displays page heading structure (H1-H6, ARIA headings)
  - Hierarchical nested view
  - Heading levels in gray, text in white

Script: extract_outline.js
```

#### links (Line 3792)
```
zen links [OPTIONS]
Options:
  --only-internal         Show only internal links (same domain)
  --only-external         Show only external links
  --alphabetically        Sort alphabetically
  --only-urls             Show only URLs (no anchor text)
  --json                  Output as JSON with detailed info
  --enrich-external       Fetch metadata for external links
                          (HTTP status, MIME type, file size, title, language)

Features:
  - Displays links with anchor text
  - Filters by internal/external
  - Enrichment: HTTP status, MIME type, file size, page title, language
  - Parallel metadata fetching (ThreadPoolExecutor with 10 workers)

Script: extract_links.js
Helper Functions:
  - _enrich_link_metadata(url) - Fetches HTTP headers using curl
  - _enrich_external_links(links) - Parallel enrichment
```

#### summarize (Line 3960)
```
zen summarize [OPTIONS]
Options:
  --format [summary|full]        Output format (default: summary)
  --language, --lang TEXT        Language for AI output
  --debug                        Show full prompt instead of calling AI

Features:
  - Extracts article content using Mozilla Readability
  - Generates AI summary using mods
  - Can also show full extracted article

Dependencies: mods command (required for summary format)
Script: extract_article.js
```

**Language Detection Flow:**
1. CLI flag (--language)
2. config.json ai-language setting
3. Detect from page language
4. Default (let AI decide)

---

### MODULE: util.py (~250 lines)
**Commands:** info, repl, userscript, download, highlight

#### info (Line 426)
```
zen info [OPTIONS]
Options:
  --extended        Show extended information (language, meta tags, security, a11y)
  --json            Output as JSON

Data Returned:
  Basic:
    - url, title, domain, protocol, readyState
    - width, height (window dimensions)
    
  Extended:
    - Language, charset, meta tags
    - Cookie count, script count, stylesheet count, etc.
    - Service worker status
    - Storage sizes (localStorage, sessionStorage)
    - Security: HTTPS, mixed content, CSP, robots meta, referrer policy
    - Accessibility: landmark count, heading structure, alt text issues
    - SEO: canonical URL, Open Graph tags, structured data, robots directives

Helper Functions:
  - _get_domain_metrics(domain) - IP, geolocation, WHOIS, SSL cert info
  - _get_robots_txt(url) - Parse robots.txt directives
  - _get_response_headers(url) - Fetch HTTP headers
```

#### repl (Line 1482)
```
zen repl
No options/arguments

Features:
  - Interactive JavaScript REPL
  - Type: 'exit' or Ctrl+D to quit
  - Shows connected page info
  - Executes code with timeout

Prompt: "zen> "
```

**Dependency:** Server must be running

#### userscript (Line 1607)
```
zen userscript
No options/arguments

Output: Displays installation instructions for browser userscript
```

#### download (Line 1635)
```
zen download [OPTIONS]
Options:
  -o, --output TEXT  Output directory (default: ~/Downloads/<domain>)
  --list             Only list files without downloading
  -t, --timeout FLOAT  Timeout in seconds (default: 30)

Features:
  - Finds downloadable files (images, PDFs, videos, audio, documents, archives)
  - Interactive numbered menu selection
  - Parallel download capability
  - File categories:
    - Images (with dimensions)
    - PDF documents
    - Videos
    - Audio files
    - Documents (DOCX, XLS, PPT, etc.)
    - Archives (ZIP, TAR, RAR, 7Z, etc.)

Script: find_downloads.js
Dependencies: requests library, urllib.parse, ThreadPoolExecutor
```

#### highlight (Line 1538)
```
zen highlight SELECTOR [OPTIONS]
Arguments:
  selector  CSS selector

Options:
  -c, --color TEXT  Outline color (default: red)
  --clear           Clear all highlights

Features:
  - Adds 2px dashed outline around matching elements
  - Multiple elements can be highlighted
  - Uses data-zen-highlight attribute tracking

Usage Examples:
  zen highlight "h1, h2"
  zen highlight ".error" --color orange
  zen highlight "a" --clear
```

---

## COMMAND EXECUTION FLOW PATTERNS

### Standard Browser Command Pattern
```
1. Create BridgeClient()
2. Check if server is alive
3. Load JavaScript code (inline or from script)
4. Replace placeholders (selectors, text, etc.)
5. Execute with client.execute(code, timeout)
6. Check result.get("ok") and result.get("error")
7. Process response and display output
8. Exit with sys.exit(1) on error
```

### Polling Pattern (watch, control)
```
1. Start action (setup event listeners in browser)
2. Set up signal handler for Ctrl+C
3. Poll loop:
   - Execute poll code (get events from window)
   - Process and display events
   - Sleep (100-500ms)
4. Cleanup (remove listeners, restore terminal settings)
```

### AI Pattern (describe, summarize)
```
1. Extract page content (JavaScript)
2. Detect page language
3. Determine target language (CLI > config > detected > default)
4. Read prompt template file
5. Inject language instruction if specified
6. Call mods (subprocess) with full input
7. Display mods output
```

