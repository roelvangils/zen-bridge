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

2. Create a new userscript and copy the contents of `userscript.js`

3. Save and enable the script

To view the userscript location:
```bash
zen userscript
```

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

1. **Bridge Server**: A local HTTP server (port 8765) that manages communication
2. **Userscript**: Runs in your browser, polls the server for code to execute
3. **CLI**: Sends JavaScript code to the server and waits for results

```
┌─────────┐         ┌────────────┐         ┌─────────────┐
│   CLI   │────────>│   Bridge   │<────────│   Browser   │
│         │  HTTP   │   Server   │  Poll   │ (Userscript)│
└─────────┘         └────────────┘         └─────────────┘
```

The system uses request IDs to match commands with their results, allowing for reliable synchronous execution.

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
