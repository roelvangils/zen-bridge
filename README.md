# Zen Browser Bridge

Execute JavaScript in your browser from the command line. A powerful CLI tool for browser automation, debugging, and interactive development.

## Features

- Execute JavaScript code in your active browser tab from the terminal
- Interactive REPL for live experimentation
- Synchronous request/response handling
- Execute code from files or stdin
- Get page information (URL, title, dimensions, etc.)
- Multiple output formats (auto, JSON, raw)
- Works with Firefox, Zen, and any browser supporting userscripts

## Installation

### 1. Install the CLI tool

```bash
# Install in development mode
pip install -e .

# Or install dependencies manually
pip install -r requirements.txt
```

### 2. Install the userscript

The browser needs a userscript to receive and execute commands from the CLI.

1. Install a userscript manager in your browser:
   - [Violentmonkey](https://violentmonkey.github.io/) (recommended)
   - [Tampermonkey](https://www.tampermonkey.net/)
   - [Greasemonkey](https://www.greasespot.net/) (Firefox only)

2. Create a new userscript and copy the contents of **`userscript_ws.js`** (WebSocket version)

3. Save and enable the script

To view the userscript location:
```bash
zen userscript
```

**Note:** The WebSocket version (`userscript_ws.js`) is recommended for better performance and features like auto-refocus in control mode.

### 3. Start the bridge server

The bridge server acts as a communication hub between the CLI and browser.

```bash
# Start in foreground
zen server start

# Or start in background (daemon mode)
zen server start --daemon

# Check server status
zen server status
```

## Usage

### Execute JavaScript code

```bash
# Simple expression
zen eval "document.title"

# Get page info
zen eval "location.href"

# Execute complex code
zen eval "Array.from(document.querySelectorAll('a')).map(a => a.href)"

# Show URL and title
zen eval "document.title" --url --title

# JSON output format
zen eval "({url: location.href, title: document.title})" --format json
```

### Execute from file

```bash
# Execute a JavaScript file
zen eval --file script.js
zen exec script.js

# Or use stdin
cat script.js | zen eval
echo "console.log('Hello')" | zen eval
```

### Get page information

```bash
zen info
```

Output:
```
URL:      https://example.com
Title:    Example Domain
Domain:   example.com
Protocol: https:
State:    complete
Size:     1280x720
```

### Interactive REPL

Start an interactive session to execute JavaScript live:

```bash
zen repl
```

Example session:
```
Zen Browser REPL - Type JavaScript code, 'exit' to quit

Connected to: Example Domain (https://example.com)

zen> document.title
Example Domain

zen> document.querySelectorAll('p').length
2

zen> exit
Goodbye!
```

### Highlight elements on page

Visually highlight elements matching a CSS selector:

```bash
# Highlight headings
zen highlight "h1, h2"

# Highlight with custom color
zen highlight "a" --color blue

# Highlight form fields
zen highlight "input, textarea" --color orange

# Clear all highlights
zen highlight "h1" --clear
```

### Download files from page

Find and download files from the current page interactively:

```bash
# Interactive selection with gum
zen download

# List all downloadable files without downloading
zen download --list

# Download to specific directory
zen download --output ~/Downloads
```

Supported file types:
- Images (jpg, png, gif, svg, webp, etc.)
- PDF documents
- Videos (mp4, webm, avi, mov, etc.)
- Audio files (mp3, wav, ogg, etc.)
- Documents (docx, xlsx, pptx, txt, csv, etc.)
- Archives (zip, rar, tar.gz, 7z, etc.)

### Send text to browser

Type text character by character into the browser, simulating keyboard input:

```bash
# Type into the currently focused input field
zen send "Hello World"

# Type into a specific element
zen send "test@example.com" --selector "input[type=email]"

# Type a longer text
zen send "This will be typed character by character"
```

**Note**: Click on an input field first, or use `--selector` to target a specific element.

### Control browser with keyboard

Navigate and interact with web pages using keyboard controls from your terminal:

```bash
zen control
```

**Features:**
- **Keyboard Navigation**: Tab through focusable elements, use arrow keys, press Enter to click
- **Auto-refocus**: After clicking links, automatically refocuses the element that triggered navigation
- **Visual Feedback**: Elements are highlighted with a blue outline as you navigate
- **Accessible Names**: Hear element names spoken via screen reader (if enabled)
- **Persistent Across Navigation**: Control mode survives page reloads and navigations

**Controls:**
- `Tab` / `Shift+Tab`: Navigate forward/backward through elements
- `Arrow Keys`: Move focus in specified direction
- `Enter` / `Space`: Click/activate focused element
- `Escape`: Return to body element
- `q`: Quit control mode

**Example workflow:**
```bash
# Start control mode
zen control

# Tab through links on a page
# Press Enter on a link → Page navigates
# Element automatically refocuses after page loads
# Continue tabbing from where you left off
```

The auto-refocus feature uses intelligent element matching (combining CSS selectors with text content) to ensure the correct element is refocused even when multiple elements share the same class.

### Watch keyboard input

Monitor all keyboard input in the browser in real-time:

```bash
zen watch input
```

Example output:
```
Watching keyboard input... (Press Ctrl+C to stop)

H e l l o [SPACE] w o r l d [BACKSPACE] [BACKSPACE] [BACKSPACE] [BACKSPACE] [BACKSPACE] W o r l d [ENTER]
```

Shows:
- Regular characters as-is
- Special keys in brackets: `[ENTER]`, `[TAB]`, `[BACKSPACE]`, `[SPACE]`, etc.
- Arrow keys: `[UP]`, `[DOWN]`, `[LEFT]`, `[RIGHT]`
- Modifiers: `[CTRL+C]`, `[ALT+F4]`, `[SHIFT+A]`

Press `Ctrl+C` to stop watching.

### Inspect elements

Get detailed information about DOM elements using two methods:

**Method 1: Select programmatically (fastest)**

```bash
# Select an element by CSS selector
zen inspect "h1"

# View detailed information
zen inspected
```

**Method 2: Capture from DevTools (useful when you can't easily write a selector)**

When you want to inspect a specific element you're looking at in the browser:

1. **Right-click** on any element → **Inspect** (opens DevTools with element selected)
2. Switch to the **Console** tab in DevTools
3. Run: **`zenStore($0)`** (stores the currently inspected element)
4. In your terminal: **`zen inspected`**

> **Why `zenStore($0)`?** The `$0` variable in DevTools Console always refers to the currently inspected element. By calling `zenStore($0)`, you're explicitly passing that element reference to the Zen Bridge, which stores it for CLI access.

Example output:
```
Tag:      <div>
Selector: div#main-content
ID:       main-content
Classes:  container, active
Text:     Welcome to our website...
Position: x=20, y=100
Size:     1200×800px
Visible:  Yes
Children: 5

Styles:
  display: block
  position: relative
  backgroundColor: rgb(255, 255, 255)
  color: rgb(33, 33, 33)
  fontSize: 16px

Attributes:
  id: main-content
  class: container active
  data-page: home
```

**Alternative ways to use zenStore:**

```javascript
// Store the inspected element
zenStore($0)

// Store a specific element by selector
zenStore(document.querySelector('.my-class'))

// Store any element reference
const btn = document.getElementById('submit-btn');
zenStore(btn)
```

### Get text selection

Get the currently selected text in the browser:

```bash
# Get selection with metadata
zen selected

# Get just the raw text (no formatting)
zen selected --raw

# Use in scripts
zen selected --raw | pbcopy
zen selected --raw > selection.txt
```

Example output:
```
Selected Text (42 characters):

"Execute JavaScript in your browser from"

Position:
  x=120, y=340
  Size: 450×24px

Container:
  Tag:   <p>
  Class: description
```

### Click elements

Click, double-click, or right-click on elements:

```bash
# Click on element
zen click "button#submit"

# Use with inspect
zen inspect "button.primary"
zen click

# Double-click
zen double-click "div.editable"
zen doubleclick "div.item"  # alias

# Right-click (context menu)
zen right-click "a.download"
zen rightclick "img"  # alias
```

### Wait for elements

Wait for elements to appear, be visible, hidden, or contain text:

```bash
# Wait for element to exist (default timeout: 30s)
zen wait "button#submit"

# Wait for element to be visible
zen wait ".modal-dialog" --visible

# Wait for element to be hidden (useful for loading spinners)
zen wait ".loading-spinner" --hidden

# Wait for element to contain specific text
zen wait "div.result" --text "Success"

# Custom timeout (in seconds)
zen wait "div.notification" --timeout 10
```

Example output:
```
Waiting for element to be visible: .modal-dialog
✓ Element is visible
  Element: <div#confirmDialog.modal-dialog>
  Waited: 1.23s
```

**Automation example:**
```bash
#!/bin/bash
# Click a button and wait for results
zen click "button.load-more"
zen wait ".new-content" --visible
zen selected --raw > results.txt
```

### Server management

```bash
# Start server
zen server start

# Start in background
zen server start --daemon

# Check status
zen server status

# Stop (if in foreground, use Ctrl+C)
zen server stop
```

## Built-in Scripts

Zen comes with ready-to-use scripts for common tasks:

### 📸 Extract all images
```bash
zen exec zen/scripts/extract_images.js --format json
```

### 📊 Extract table data
```bash
# Convert HTML tables to JSON
zen exec zen/scripts/extract_table.js --format json > data.json
```

### 🔍 Get SEO metadata
```bash
# Extract all meta tags, Open Graph, Twitter Cards, etc.
zen exec zen/scripts/extract_metadata.js --format json
```

### ⚡ Performance metrics
```bash
# Detailed page performance analysis
zen exec zen/scripts/performance_metrics.js --format json
```

### 💉 Inject jQuery
```bash
zen exec zen/scripts/inject_jquery.js
# Then use jQuery
zen eval "$('a').length"
```

### 🎨 Highlight elements
```bash
# Edit zen/scripts/highlight_selector.js to change selector
zen exec zen/scripts/highlight_selector.js
```

## Quick Examples

### DOM manipulation

```bash
# Get all links
zen eval "Array.from(document.querySelectorAll('a')).map(a => ({text: a.textContent, href: a.href}))" --format json

# Count elements
zen eval "document.querySelectorAll('div').length"

# Change page title
zen eval "document.title = 'Changed by Zen!'"
```

### Data extraction from authenticated pages

```bash
# Extract data from dashboard (while logged in)
zen eval "
  Array.from(document.querySelectorAll('.dashboard-item')).map(item => ({
    title: item.querySelector('.title').textContent,
    value: item.querySelector('.value').textContent
  }))
" --format json > dashboard.json
```

### Debug application state

```bash
# Check React/Redux state
zen eval "window.__REDUX_DEVTOOLS_EXTENSION__?.store.getState()" --format json

# Inspect your app state
zen eval "window.myApp?.state" --format json
```

### Performance monitoring

```bash
# Page load time
zen eval "(performance.timing.loadEventEnd - performance.timing.navigationStart) + 'ms'"

# Memory usage
zen eval "Math.round(performance.memory.usedJSHeapSize / 1048576) + 'MB'"
```

### Shell integration

```bash
# Use in scripts
TITLE=$(zen eval "document.title" --format raw)
echo "Current page: $TITLE"

# Monitor changes
while true; do
  zen eval "document.querySelectorAll('.notification').length" --format raw
  sleep 5
done

# Extract and process with other tools
zen eval "Array.from(document.links).map(a => a.href).join('\n')" --format raw | grep "github"
```

## 📚 More Examples

See [EXAMPLES.md](EXAMPLES.md) for 50+ real-world use cases including:
- Web scraping workflows
- Form automation
- Performance analysis
- Accessibility checks
- Local storage operations
- And much more!

## How it works

The bridge uses a **WebSocket-based architecture** for fast, bidirectional communication:

1. **Bridge Server**: Runs on `127.0.0.1:8765` (HTTP) and `:8766` (WebSocket)
2. **Userscript**: Maintains a persistent WebSocket connection to the server
3. **CLI**: Sends commands via HTTP, server forwards to browser via WebSocket

```
┌─────────┐         ┌────────────┐         ┌─────────────┐
│   CLI   │────────>│   Bridge   │<───────>│   Browser   │
│         │  HTTP   │   Server   │WebSocket│ (Userscript)│
└─────────┘         └────────────┘         └─────────────┘
                          ↓
                    • HTTP: :8765 (CLI ⟷ Server)
                    • WebSocket: :8766 (Server ⟷ Browser)
                    • Scripts cached in memory for speed
```

**Key features:**
- **Fast**: WebSocket provides ~12x faster responses than HTTP polling
- **Reliable**: Request IDs match commands with results
- **Persistent**: Connection survives page navigation with auto-reconnect
- **Optimized**: Scripts cached in memory, minimal delays (~150ms refocus time)

## Configuration

The bridge server runs on `127.0.0.1:8765` by default. This can be changed in the code if needed.

## Troubleshooting

### "Bridge server is not running"

Start the server:
```bash
zen server start
```

### "No response from browser after X seconds"

1. Make sure the userscript is installed and active
2. Open a browser tab (the userscript only works in visible tabs)
3. Check the browser console for errors
4. Verify the userscript is polling (you should see a connection message)

### Commands timeout

- Increase the timeout: `zen eval "code" --timeout 30`
- Check if the browser tab is visible (inactive tabs don't execute code)

## Advanced Usage

### Custom timeout

```bash
# Wait up to 30 seconds for result
zen eval "await longRunningOperation()" --timeout 30
```

### Output formatting

```bash
# Auto format (default - smart detection)
zen eval "document.title"

# Force JSON
zen eval "document.title" --format json

# Raw output (no formatting)
zen eval "document.title" --format raw
```

### Piping and composition

```bash
# Pipe to other tools
zen eval "document.body.innerHTML" | grep -i "error"

# Use in scripts
TITLE=$(zen eval "document.title" --format raw)
echo "Current page: $TITLE"
```

## Development

### Project structure

```
zen_bridge/
├── zen/                    # Main package
│   ├── __init__.py        # Package info
│   ├── bridge.py          # HTTP server
│   ├── client.py          # Client library
│   ├── cli.py             # CLI interface
│   ├── scripts/           # Pre-built scripts
│   └── templates/         # Script templates
├── userscript.js          # Browser userscript
├── setup.py               # Package setup
├── requirements.txt       # Dependencies
└── README.md             # This file
```

### Running tests

```bash
# Start server
zen server start --daemon

# Open a test page in your browser
# Then run manual tests
zen eval "document.title"
zen info
zen repl
```

## License

MIT

## Credits

Created by Roel van Gils

Based on the original KM JS Bridge concept.
