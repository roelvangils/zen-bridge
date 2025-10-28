# CLI Command Reference

Complete reference for all 42+ Zen Bridge CLI commands organized by category.

---

## Overview

The Zen CLI provides commands to interact with the browser through the WebSocket bridge. Commands range from simple JavaScript execution to complex AI-powered content analysis and interactive browser control.

**Global Usage:**
```bash
zen [OPTIONS] COMMAND [ARGS]...
```

**Global Options:**

- `--version` - Show the version and exit
- `--help` - Show help message and exit

---

## Command Categories

- [Execution](#execution) - Execute JavaScript code
- [Navigation](#navigation) - Navigate browser history and pages
- [Cookies](#cookies) - Manage browser cookies
- [Interaction](#interaction) - Interact with page elements
- [Inspection](#inspection) - Inspect elements and capture screenshots
- [Selection](#selection) - Work with text selection
- [Server](#server) - Manage the bridge server
- [Extraction](#extraction) - Extract and analyze page content
- [Watch](#watch) - Monitor browser events
- [Utilities](#utilities) - Utility commands

---

## Execution

### `eval`

Execute JavaScript code in the active browser tab.

**Syntax:**
```bash
zen eval [CODE] [OPTIONS]
```

**Arguments:**

- `CODE` - JavaScript code to execute (optional if using --file or stdin)

**Options:**

- `-f, --file PATH` - Execute code from file
- `-t, --timeout FLOAT` - Timeout in seconds (default: 10)
- `--format [auto|json|raw]` - Output format (default: auto)
- `--url` - Also print page URL
- `--title` - Also print page title

**Examples:**

```bash
# Execute inline code
zen eval "document.title"

# Execute from file
zen eval --file script.js

# Read from stdin
echo "console.log('test')" | zen eval

# Get result as JSON
zen eval "({title: document.title, url: location.href})" --format json

# Show metadata
zen eval "document.body.innerHTML.length" --url --title
```

**Return Value:**

Outputs the result of JavaScript execution. Format depends on `--format` option:

- **auto** (default): Smart formatting based on type
- **json**: Valid JSON output
- **raw**: String representation

**Error Handling:**

- Exits with code 1 on execution errors
- Shows error message in stderr
- Timeouts after specified seconds

**Related:**

- [`exec`](#exec) - Execute from file only
- [`repl`](#repl) - Interactive execution

---

### `exec`

Execute JavaScript from a file.

**Syntax:**
```bash
zen exec FILEPATH [OPTIONS]
```

**Arguments:**

- `FILEPATH` - Path to JavaScript file (required)

**Options:**

- `-t, --timeout FLOAT` - Timeout in seconds (default: 10)
- `--format [auto|json|raw]` - Output format (default: auto)

**Examples:**

```bash
zen exec script.js
zen exec script.js --timeout 30
zen exec script.js --format json
```

**Return Value:**

Same as `eval` command.

**Error Handling:**

- Exits with code 1 if file not found or execution fails
- Shows error message in stderr

**Related:**

- [`eval`](#eval) - Execute inline code or from stdin

---

## Navigation

### `open`

Navigate to a URL.

**Syntax:**
```bash
zen open URL [OPTIONS]
```

**Arguments:**

- `URL` - URL to navigate to (required)

**Options:**

- `--wait` - Wait for page to finish loading
- `-t, --timeout INT` - Timeout in seconds when using --wait (default: 30)

**Examples:**

```bash
# Navigate to URL
zen open "https://example.com"

# Navigate and wait for page load
zen open "https://example.com" --wait

# Navigate with custom timeout
zen open "https://example.com" --wait --timeout 60
```

**Return Value:**

Prints confirmation message. If `--wait` is used, confirms page load.

**Error Handling:**

- Exits with code 1 if navigation fails
- Timeouts after specified seconds when using --wait

**Related:**

- [`reload`](#reload) - Reload current page
- [`back`](#back) - Go back in history

---

### `back`

Go back to the previous page in browser history.

**Syntax:**
```bash
zen back
```

**Aliases:**

- `previous` (hidden)

**Examples:**

```bash
zen back
```

**Return Value:**

Prints "✓ Navigated back"

**Related:**

- [`forward`](#forward) - Go forward in history
- [`open`](#open) - Navigate to URL

---

### `forward`

Go forward to the next page in browser history.

**Syntax:**
```bash
zen forward
```

**Aliases:**

- `next` (hidden)

**Examples:**

```bash
zen forward
```

**Return Value:**

Prints "✓ Navigated forward"

**Related:**

- [`back`](#back) - Go back in history

---

### `reload`

Reload the current page.

**Syntax:**
```bash
zen reload [OPTIONS]
```

**Options:**

- `--hard` - Hard reload (bypass cache)

**Aliases:**

- `refresh` (hidden)

**Examples:**

```bash
# Normal reload
zen reload

# Hard reload (bypass cache)
zen reload --hard
```

**Return Value:**

Prints confirmation message.

**Related:**

- [`open`](#open) - Navigate to URL

---

## Cookies

The `cookies` command group manages browser cookies.

### `cookies list`

List all cookies for the current page.

**Syntax:**
```bash
zen cookies list
```

**Examples:**

```bash
zen cookies list
```

**Return Value:**

Displays cookie count and name-value pairs:

```
Cookies (3):

  session_id = abc123def456...
  user_pref = dark
  tracking = true
```

**Related:**

- [`cookies get`](#cookies-get) - Get specific cookie

---

### `cookies get`

Get the value of a specific cookie.

**Syntax:**
```bash
zen cookies get NAME
```

**Arguments:**

- `NAME` - Cookie name (required)

**Examples:**

```bash
zen cookies get session_id
```

**Return Value:**

Prints cookie name and value:

```
session_id = abc123def456
```

**Error Handling:**

- Exits with code 1 if cookie not found

**Related:**

- [`cookies list`](#cookies-list) - List all cookies

---

### `cookies set`

Set a cookie.

**Syntax:**
```bash
zen cookies set NAME VALUE [OPTIONS]
```

**Arguments:**

- `NAME` - Cookie name (required)
- `VALUE` - Cookie value (required)

**Options:**

- `--max-age INT` - Max age in seconds
- `--expires TEXT` - Expiration date (e.g., 'Wed, 21 Oct 2025 07:28:00 GMT')
- `--path TEXT` - Cookie path (default: /)
- `--domain TEXT` - Cookie domain
- `--secure` - Secure flag (HTTPS only)
- `--same-site [Strict|Lax|None]` - SameSite attribute

**Examples:**

```bash
# Simple cookie
zen cookies set session_id abc123

# With expiration
zen cookies set token xyz --max-age 3600

# Secure cookie with path
zen cookies set user_pref dark --path / --secure

# With SameSite
zen cookies set csrf_token abc --same-site Strict
```

**Return Value:**

Prints confirmation:

```
✓ Cookie set: session_id = abc123
```

**Related:**

- [`cookies delete`](#cookies-delete) - Delete cookie

---

### `cookies delete`

Delete a specific cookie.

**Syntax:**
```bash
zen cookies delete NAME
```

**Arguments:**

- `NAME` - Cookie name (required)

**Examples:**

```bash
zen cookies delete session_id
```

**Return Value:**

Prints confirmation:

```
✓ Cookie deleted: session_id
```

**Related:**

- [`cookies clear`](#cookies-clear) - Delete all cookies

---

### `cookies clear`

Clear all cookies for the current page.

**Syntax:**
```bash
zen cookies clear
```

**Examples:**

```bash
zen cookies clear
```

**Return Value:**

Prints count of deleted cookies:

```
✓ Cleared 5 cookie(s)
```

**Related:**

- [`cookies delete`](#cookies-delete) - Delete specific cookie

---

## Interaction

### `send`

Send text to the browser by typing it character by character.

**Syntax:**
```bash
zen send TEXT [OPTIONS]
```

**Arguments:**

- `TEXT` - Text to type (required)

**Options:**

- `-s, --selector TEXT` - CSS selector to focus before typing

**Examples:**

```bash
# Type into currently focused element
zen send "Hello World"

# Type into specific element
zen send "test@example.com" --selector "input[type=email]"

# Type into password field
zen send "mypassword" --selector "#password"
```

**Return Value:**

Prints confirmation message.

**Error Handling:**

- Exits with code 1 if element not found (when using --selector)
- Shows error hint if no element focused

**Related:**

- [`click`](#click) - Click elements

---

### `click`

Click on an element.

**Syntax:**
```bash
zen click [SELECTOR]
```

**Arguments:**

- `SELECTOR` - CSS selector (default: $0 for inspected element)

**Examples:**

```bash
# Click on stored element ($0)
zen inspect "button#submit"
zen click

# Click directly on element
zen click "button#submit"
zen click ".primary-button"
```

**Return Value:**

Prints element details and click position:

```
Clicked: <button#submit>
Position: x=120, y=450
```

**Error Handling:**

- Exits with code 1 if element not found

**Related:**

- [`double-click`](#double-click) - Double-click
- [`right-click`](#right-click) - Right-click
- [`inspect`](#inspect) - Inspect element

---

### `double-click`

Double-click on an element.

**Syntax:**
```bash
zen double-click [SELECTOR]
```

**Arguments:**

- `SELECTOR` - CSS selector (default: $0 for inspected element)

**Aliases:**

- `doubleclick` (hidden)

**Examples:**

```bash
zen double-click "div.item"
zen inspect "div.item"
zen double-click
```

**Return Value:**

Same as `click` command.

**Related:**

- [`click`](#click) - Single click

---

### `right-click`

Right-click (context menu) on an element.

**Syntax:**
```bash
zen right-click [SELECTOR]
```

**Arguments:**

- `SELECTOR` - CSS selector (default: $0 for inspected element)

**Aliases:**

- `rightclick` (hidden)

**Examples:**

```bash
zen right-click "a.download-link"
zen inspect "a.download-link"
zen right-click
```

**Return Value:**

Same as `click` command.

**Related:**

- [`click`](#click) - Left click

---

### `wait`

Wait for an element to appear, be visible, hidden, or contain text.

**Syntax:**
```bash
zen wait SELECTOR [OPTIONS]
```

**Arguments:**

- `SELECTOR` - CSS selector (required)

**Options:**

- `-t, --timeout INT` - Timeout in seconds (default: 30)
- `--visible` - Wait for element to be visible
- `--hidden` - Wait for element to be hidden
- `--text TEXT` - Wait for element to contain specific text

**Examples:**

```bash
# Wait for element to exist (up to 30 seconds)
zen wait "button#submit"

# Wait for element to be visible
zen wait ".modal" --visible

# Wait for element to be hidden
zen wait ".loading-spinner" --hidden

# Wait for element to contain text
zen wait "h1" --text "Success"

# Custom timeout (10 seconds)
zen wait "div.result" --timeout 10
```

**Return Value:**

Prints status and wait time:

```
Waiting for element to be visible: .modal
✓ Element is visible
  Element: div.modal
  Waited: 1.23s
```

**Error Handling:**

- Exits with code 1 on timeout
- Shows timeout message with details

**Related:**

- [`click`](#click) - Click after waiting

---

## Inspection

### `inspect`

Select an element and show its details.

**Syntax:**
```bash
zen inspect [SELECTOR]
```

**Arguments:**

- `SELECTOR` - CSS selector (optional)

**Examples:**

```bash
# Select and show details
zen inspect "h1"
zen inspect "#header"
zen inspect ".main-content"

# Show currently selected element
zen inspect
```

**Return Value:**

Displays comprehensive element information:

- Tag name and selector
- ID and classes
- Text content
- Dimensions (position, size, bounds)
- Visibility status
- Accessibility details
- Semantic information
- Computed styles
- Attributes

Example output:

```
Selected element: h1

Tag:      <h1>
Selector: h1#main-title.hero-heading
Parent:   <header>
ID:       main-title
Classes:  hero-heading, large
Text:     Welcome to Our Site

Dimensions:
  Position: x=20, y=100
  Size:     800×60px
  Bounds:   top=100, right=820, bottom=160, left=20

Visibility:
  Visible:     Yes
  In viewport: Yes

Accessibility:
  Role:            heading
  Accessible Name: "Welcome to Our Site"
  Name computed from: contents
  Focusable:       No

Styles:
  font-size: 48px
  font-weight: 700
  color: rgb(33, 33, 33)
```

**Related:**

- [`inspected`](#inspected) - Show inspected element details
- [`click`](#click) - Click inspected element

---

### `inspected`

Get information about the currently inspected element.

**Syntax:**
```bash
zen inspected
```

**Examples:**

```bash
# From DevTools:
# 1. Right-click element → Inspect
# 2. In DevTools Console: zenStore()
# 3. Run:
zen inspected

# Or select programmatically:
zen inspect "h1"
zen inspected
```

**Return Value:**

Same detailed output as `inspect` command.

**Error Handling:**

- Exits with code 1 if no element inspected
- Shows hint on how to inspect element

**Related:**

- [`inspect`](#inspect) - Select element

---

### `screenshot`

Take a screenshot of a specific element.

**Syntax:**
```bash
zen screenshot -s SELECTOR [OPTIONS]
```

**Options:**

- `-s, --selector TEXT` - CSS selector (required, use $0 for inspected element)
- `-o, --output PATH` - Output file path (optional)

**Examples:**

```bash
# Screenshot element
zen screenshot --selector "#main"

# Save to specific file
zen screenshot -s ".hero-section" -o hero.png

# Screenshot inspected element ($0)
zen screenshot -s "$0" -o inspected.png
```

**Return Value:**

Prints save location and image size:

```
Capturing element: #main
Screenshot saved: /path/to/screenshot_main_20251027_143522.png
Size: 1200x800px (245.3 KB)
```

**Error Handling:**

- Exits with code 1 if element not found
- Shows error if screenshot fails

**Related:**

- [`inspect`](#inspect) - Inspect before screenshot

---

## Selection

### `selected`

Get the current text selection in the browser.

**Syntax:**
```bash
zen selected [OPTIONS]
```

**Options:**

- `--raw` - Output only the text without formatting

**Examples:**

```bash
# Get selection with metadata
zen selected

# Get just the raw text
zen selected --raw

# Pipe to file
zen selected --raw > selection.txt
```

**Return Value:**

Default mode shows:

```
Selected Text (145 characters):

"This is the selected text from the browser..."

Position:
  x=120, y=340
  Size: 450×80px

Container:
  Tag:   <p>
  ID:    intro
  Class: lead-paragraph
```

Raw mode outputs only the selected text.

**Error Handling:**

- Exits with code 0 if no selection (not an error)
- Shows hint to select text first

**Related:**

- None

---

## Server

The `server` command group manages the bridge server.

### `server start`

Start the bridge server.

**Syntax:**
```bash
zen server start [OPTIONS]
```

**Options:**

- `-p, --port INT` - Port to run on (default: 8765)
- `-d, --daemon` - Run in background

**Examples:**

```bash
# Start in foreground
zen server start

# Start on custom port
zen server start --port 9000

# Start as background daemon
zen server start --daemon
```

**Return Value:**

Foreground mode: Runs until Ctrl+C
Daemon mode: Prints confirmation and returns

```
Starting WebSocket bridge server in background on port 8765...
WebSocket server started successfully on ports 8765 (HTTP) and 8766 (WebSocket)
```

**Error Handling:**

- Exits with code 1 if server already running
- Shows error if port in use

**Related:**

- [`server status`](#server-status) - Check server status
- [`server stop`](#server-stop) - Stop server

---

### `server status`

Check bridge server status.

**Syntax:**
```bash
zen server status
```

**Examples:**

```bash
zen server status
```

**Return Value:**

Displays server status and statistics:

```
Bridge server is running
  Pending requests:   0
  Completed requests: 142
```

**Error Handling:**

- Exits with code 1 if server not running

**Related:**

- [`server start`](#server-start) - Start server

---

### `server stop`

Stop the bridge server.

**Syntax:**
```bash
zen server stop
```

**Examples:**

```bash
zen server stop
```

**Return Value:**

Shows instructions for stopping server:

```
Note: Use Ctrl+C to stop the server if running in foreground
For daemon mode, use: pkill -f 'zen.bridge_ws'
```

**Related:**

- [`server start`](#server-start) - Start server

---

## Extraction

### `describe`

Generate an AI-powered description of the page for screen reader users.

**Syntax:**
```bash
zen describe [OPTIONS]
```

**Options:**

- `--language, --lang TEXT` - Language for AI output (overrides config)
- `--debug` - Show the full prompt instead of calling AI

**Examples:**

```bash
# Generate description
zen describe

# Force English output
zen describe --language en

# Debug mode (see prompt)
zen describe --debug
```

**Return Value:**

AI-generated natural language description of page structure, landmarks, and navigation.

**Requirements:**

- Requires `mods` command (https://github.com/charmbracelet/mods)
- Analyzes page structure, headings, landmarks, forms, images

**Error Handling:**

- Exits with code 1 if mods not installed
- Shows error if page extraction fails

**Related:**

- [`outline`](#outline) - Show heading structure
- [`summarize`](#summarize) - Summarize article

---

### `outline`

Display the page's heading structure as a nested outline.

**Syntax:**
```bash
zen outline
```

**Examples:**

```bash
zen outline
```

**Return Value:**

Displays hierarchical heading structure:

```
H1 Welcome to Our Site
   H2 Getting Started
      H3 Installation
      H3 Configuration
   H2 Features
      H3 Performance
      H3 Accessibility

Total: 6 headings
```

**Related:**

- [`describe`](#describe) - AI-powered description

---

### `links`

Extract all links from the current page.

**Syntax:**
```bash
zen links [OPTIONS]
```

**Options:**

- `--only-internal` - Show only internal links (same domain)
- `--only-external` - Show only external links (different domain)
- `--alphabetically` - Sort links alphabetically
- `--only-urls` - Show only URLs without anchor text
- `--json` - Output as JSON with detailed link information
- `--enrich-external` - Fetch metadata for external links (MIME type, file size, etc.)

**Examples:**

```bash
# All links with anchor text
zen links

# Only links on same domain
zen links --only-internal

# Only links to other domains
zen links --only-external

# Sort alphabetically
zen links --alphabetically

# Show only URLs
zen links --only-urls

# External URLs only
zen links --only-external --only-urls

# Add metadata for external links
zen links --enrich-external

# JSON output
zen links --json
```

**Return Value:**

Default mode shows links with indicators:

```
→ Home
  https://example.com/

↗ External Site
  https://external.com/
  HTTP 200 | text/html | Title: External Site Title | Lang: en

Total: 25 links
```

JSON mode outputs structured data:

```json
{
  "links": [
    {
      "text": "Home",
      "href": "https://example.com/",
      "type": "internal"
    }
  ],
  "total": 25,
  "domain": "example.com"
}
```

**Related:**

- [`describe`](#describe) - Page description

---

### `summarize`

Summarize the current article using AI.

**Syntax:**
```bash
zen summarize [OPTIONS]
```

**Options:**

- `--format [summary|full]` - Output format (default: summary)
- `--language, --lang TEXT` - Language for AI output (overrides config)
- `--debug` - Show the full prompt instead of calling AI

**Examples:**

```bash
# Get AI summary
zen summarize

# Show full extracted article
zen summarize --format full

# Force French output
zen summarize --language fr

# Debug mode
zen summarize --debug
```

**Return Value:**

Summary mode: AI-generated concise summary
Full mode: Extracted article content

**Requirements:**

- Requires `mods` command
- Uses Mozilla Readability for extraction
- Works best on article pages

**Error Handling:**

- Exits with code 1 if page is not an article
- Shows error if extraction fails

**Related:**

- [`describe`](#describe) - Page description

---

## Watch

The `watch` command group monitors browser events in real-time.

### `watch input`

Watch keyboard input in real-time.

**Syntax:**
```bash
zen watch input
```

**Examples:**

```bash
zen watch input
```

**Return Value:**

Streams keyboard events to terminal. Press Ctrl+C to stop.

**Related:**

- [`watch all`](#watch-all) - Watch all interactions

---

### `watch all`

Watch all user interactions - keyboard, focus, and accessible names.

**Syntax:**
```bash
zen watch all
```

**Examples:**

```bash
zen watch all
```

**Return Value:**

Streams all interaction events:

- Regular typing on single lines
- Special keys on separate lines
- Focus changes with accessible names

Example output:

```
Watching all interactions... (Press Ctrl+C to stop)

Hello World
[Tab]
→ Focus: Search button <button#search>
[Enter]
[Tab]
→ Focus: Email input <input#email>
user@example.com
```

**Related:**

- [`watch input`](#watch-input) - Watch keyboard only
- [`control`](#control) - Interactive control mode

---

### `control`

Control the browser remotely from your terminal (interactive mode).

**Syntax:**
```bash
zen control
```

**Examples:**

```bash
zen control
```

**Features:**

- All keyboard input sent directly to browser
- Virtual focus navigation (Tab, Shift+Tab, Arrow keys)
- Regular text input
- Special keys (Enter, Escape, Backspace, etc.)
- Modifier keys (Ctrl, Alt, Shift, Cmd)
- Accessible name announcements (TTS)
- Auto-restart after navigation

**Configuration:**

Controlled by settings in `config.json` (control section):

- `auto-refocus`: When to refocus after page changes
- `speak-name`: Speak element names via TTS
- `speak-all`: Speak all terminal output
- `announce-role`: Announce element roles
- `verbose`: Show detailed messages
- And many more (see [ControlConfig](models.md#controlconfig))

**Return Value:**

Interactive session. Press Ctrl+D to exit.

Example session:

```
Now controlling: Example Domain
Press Ctrl+D to exit

[Tab] → Focus: Search <input#search>
Hello
[Enter]
🔄 Reinitializing after navigation...
✅ Control restored!
```

**Related:**

- [`watch all`](#watch-all) - Watch without control

---

## Utilities

### `info`

Get information about the current browser tab.

**Syntax:**
```bash
zen info [OPTIONS]
```

**Options:**

- `--extended` - Show extended information
- `--json` - Output as JSON

**Examples:**

```bash
# Basic info
zen info

# Extended info
zen info --extended

# JSON output
zen info --extended --json
```

**Return Value:**

Basic mode shows core information:

```
URL:      https://example.com
Title:    Example Domain
Domain:   example.com
Protocol: https:
State:    complete
Size:     1920x1080
```

Extended mode shows comprehensive data:

- Language and encoding
- Resources (scripts, stylesheets, images, forms)
- Performance metrics
- Storage (cookies, localStorage, sessionStorage)
- Security info (HTTPS, CSP, security headers)
- Accessibility (landmarks, headings, issues)
- SEO metrics (Open Graph, Twitter Card, meta tags)
- Browser/Device info
- Technologies detected (frameworks, CMS, analytics)
- Domain metrics (IP, geolocation, WHOIS, SSL)
- Robots.txt analysis
- And much more...

**Related:**

- [`describe`](#describe) - AI-powered description

---

### `repl`

Start an interactive REPL session.

**Syntax:**
```bash
zen repl
```

**Examples:**

```bash
zen repl
```

**Return Value:**

Interactive JavaScript REPL:

```
Zen Browser REPL - Type JavaScript code, 'exit' to quit

Connected to: Example Domain (https://example.com)

zen> document.title
Example Domain
zen> location.href
https://example.com/
zen> exit
Goodbye!
```

**Usage:**

- Type JavaScript code
- Results displayed immediately
- Type `exit` or `quit` to quit
- Press Ctrl+D or Ctrl+C to exit

**Related:**

- [`eval`](#eval) - Execute one-off code

---

### `userscript`

Display the userscript that needs to be installed in your browser.

**Syntax:**
```bash
zen userscript
```

**Examples:**

```bash
zen userscript
```

**Return Value:**

Shows installation instructions:

```
Userscript location: /path/to/userscript.js

To install:
1. Install a userscript manager (Tampermonkey, Greasemonkey, Violentmonkey)
2. Create a new script and paste the contents of userscript.js
3. Save and enable the script

Or use: cat userscript.js | pbcopy  (to copy to clipboard on macOS)
```

**Related:**

- [`server start`](#server-start) - Start bridge server

---

### `download`

Find and download files from the current page.

**Syntax:**
```bash
zen download [OPTIONS]
```

**Options:**

- `-o, --output PATH` - Output directory (default: ~/Downloads/<domain>)
- `--list` - Only list files without downloading
- `-t, --timeout FLOAT` - Timeout in seconds (default: 30)

**Examples:**

```bash
# Interactive download
zen download

# Download to specific directory
zen download --output ~/Documents

# List files only
zen download --list
```

**Features:**

Discovers and categorizes:

- Images (PNG, JPG, GIF, WebP, SVG)
- PDFs
- Videos (MP4, WebM, etc.)
- Audio (MP3, WAV, etc.)
- Documents (DOCX, XLSX, PPTX, etc.)
- Archives (ZIP, TAR, etc.)

**Return Value:**

Interactive selection menu:

```
Found 42 files. Select what to download:

 1. Download the largest image (1920×1080px)
 2. Download all images (42 files)
 3. Download all PDF documents (3 files)

Files will be saved to:
/Users/you/Downloads/example.com

Enter number to download (0 to cancel):
```

**Related:**

- [`links`](#links) - Extract links

---

## Hidden Commands & Aliases

Some commands have hidden aliases for convenience:

- `previous` → `back`
- `next` → `forward`
- `refresh` → `reload`
- `doubleclick` → `double-click`
- `rightclick` → `right-click`

These aliases work identically to their main commands but don't appear in help output.

---

## Exit Codes

All commands follow standard Unix exit code conventions:

- **0**: Success
- **1**: Error (execution failed, element not found, server not running, etc.)

---

## Environment

Commands respect these environment settings:

- **Config file**: `~/.config/zen-bridge/config.json`
- **Default host**: 127.0.0.1
- **Default port**: 8765 (HTTP API), 8766 (WebSocket)

---

## See Also

- [Services API Reference](services.md)
- [Models Reference](models.md)
- [Protocol Specification](protocol.md)
- [Configuration Guide](../getting-started/configuration.md)
- [Quick Start Guide](../getting-started/quick-start.md)
