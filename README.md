# Zen Browser Bridge

**Execute JavaScript in your browser from the command line.**

A powerful CLI tool for browser automation, debugging, and interactive development. Control your browser, extract data, automate tasks, and interact with web pages—all from your terminal.

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/roelvangils/zen-bridge)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## ✨ Features

- **Execute JavaScript** - Run code in your active browser tab from the terminal
- **Interactive REPL** - Live JavaScript experimentation with instant feedback
- **AI Integration** - Article summarization and page descriptions powered by AI
- **Element Interaction** - Click, inspect, highlight, and wait for elements
- **Keyboard Control** - Navigate pages entirely from your keyboard with auto-refocus
- **Data Extraction** - Links, images, tables, metadata, and more
- **File Downloads** - Interactive file finder and downloader
- **Real-time Monitoring** - Watch keyboard events and browser activity
- **Smart Help** - Enhanced help system shows all available flags for each command
- **Fast & Reliable** - WebSocket-based architecture for instant responses

## 📦 Installation

### 1. Install the CLI tool

```bash
# Clone the repository
git clone https://github.com/roelvangils/zen-bridge.git
cd zen-bridge

# Install in development mode
pip install -e .

# Or install dependencies manually
pip install -r requirements.txt
```

### 2. Install the userscript

The browser needs a userscript to receive commands from the CLI.

1. **Install a userscript manager** in your browser:
   - [Violentmonkey](https://violentmonkey.github.io/) (recommended)
   - [Tampermonkey](https://www.tampermonkey.net/)
   - [Greasemonkey](https://www.greasespot.net/) (Firefox only)

2. **Create a new userscript** and copy the contents of `userscript_ws.js`

3. **Save and enable** the script

To view the userscript:
```bash
zen userscript
```

### 3. Start the bridge server

```bash
# Start in foreground
zen server start

# Or start in background (daemon mode)
zen server start --daemon

# Check server status
zen server status
```

## 🚀 Quick Start

```bash
# Execute JavaScript code
zen eval "document.title"

# Get page information
zen info

# Extract all links
zen links --only-external

# Start interactive REPL
zen repl

# Summarize article with AI
zen summarize

# Control browser with keyboard
zen control

# Get help with all commands and flags
zen --help
```

## 📖 Usage Guide

### Execute JavaScript

```bash
# Simple expression
zen eval "document.title"

# Complex code
zen eval "Array.from(document.querySelectorAll('a')).map(a => a.href)"

# Show URL and title metadata
zen eval "document.title" --url --title

# JSON output format
zen eval "({url: location.href, title: document.title})" --format json

# Execute from file
zen eval --file script.js
zen exec script.js

# Use stdin
echo "console.log('Hello')" | zen eval
cat script.js | zen eval
```

### Interactive REPL

Start a live JavaScript session:

```bash
zen repl
```

Example session:
```javascript
zen> document.title
"Example Domain"

zen> document.querySelectorAll('p').length
2

zen> Array.from(document.links).map(a => a.href)
["https://example.com/page1", "https://example.com/page2"]

zen> exit
Goodbye!
```

### Page Information

```bash
# Basic info
zen info

# Extended info (language, meta tags, cookies)
zen info --extended

# JSON output
zen info --json
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

### Element Interaction

**Click elements:**
```bash
# Click by selector
zen click "button#submit"

# Double-click
zen double-click "div.editable"

# Right-click (context menu)
zen right-click "a.download"
```

**Inspect elements:**
```bash
# Inspect by selector
zen inspect "h1"

# Get details of inspected element
zen inspected

# In browser DevTools Console, you can also use:
# zenStore($0)  - Store currently inspected element
# Then: zen inspected
```

**Highlight elements:**
```bash
# Highlight with default color (red)
zen highlight "h1, h2"

# Custom color
zen highlight "a" --color blue

# Clear highlights
zen highlight --clear
```

**Wait for elements:**
```bash
# Wait for element to exist (default: 30s timeout)
zen wait "button#submit"

# Wait for element to be visible
zen wait ".modal-dialog" --visible

# Wait for element to be hidden
zen wait ".loading-spinner" --hidden

# Wait for text content
zen wait "div.result" --text "Success"

# Custom timeout
zen wait "div.notification" --timeout 10
```

### Extract Links

```bash
# Show all links
zen links

# Only URLs (one per line)
zen links --only-urls

# Filter to internal links
zen links --only-internal

# Filter to external links
zen links --only-external

# Sort alphabetically
zen links --alphabetically

# Get enriched metadata (MIME type, size, title, status)
zen links --enrich-external

# Combine filters
zen links --only-external --only-urls --alphabetically
```

**Example output:**
```
→ Home Page
  https://example.com/

↗ External Resource
  https://other-site.com/page

Total: 15 links (8 internal, 7 external)
```

**Practical uses:**
```bash
# Export external links for analysis
zen links --only-external --only-urls > external-links.txt

# Count total links
zen links --only-urls | wc -l

# Find all PDF links
zen links --only-urls | grep "\.pdf$"
```

### Page Outline

Display heading hierarchy:

```bash
zen outline
```

Output:
```
H1 Getting Started
   H2 Installation
      H3 Prerequisites
      H3 Setup
   H2 Configuration
      H3 Basic Settings
      H3 Advanced Options
         H4 Environment Variables

Total: 7 headings
```

**Features:**
- Native HTML headings (H1-H6)
- ARIA headings (`role="heading"` with `aria-level`)
- Hierarchical indentation
- Colored output for readability

**Use cases:**
- Accessibility audits
- Verify heading hierarchy
- SEO analysis
- Quick page structure overview

### AI-Powered Features

**Article Summarization:**

```bash
# Generate concise summary
zen summarize

# Show full extracted article
zen summarize --format full
```

Requires [mods](https://github.com/charmbracelet/mods) to be installed.

**Page Descriptions for Screen Readers:**

```bash
zen describe
```

Generates a natural-language description perfect for blind users:

```
This webpage is in Dutch, but is also available in English and French.
At the top you can navigate to services, articles, careers, about us
and contact us. The main part contains a rather long article about an
empathy lab with five headings. The footer contains standard links
such as a sitemap and privacy statement.
```

**What it analyzes:**
- Available languages
- Navigation menus
- Page landmarks
- Heading structure
- Main content type and length
- Significant images
- Forms and interactive elements
- Footer utilities

Requires [mods](https://github.com/charmbracelet/mods) to be installed.

### Download Files

Find and download files interactively:

```bash
# Interactive selection
zen download

# List files without downloading
zen download --list

# Custom output directory
zen download --output ~/Downloads
```

**Supported file types:**
- Images (jpg, png, gif, svg, webp)
- Documents (pdf, docx, xlsx, pptx, txt, csv)
- Videos (mp4, webm, avi, mov)
- Audio (mp3, wav, ogg)
- Archives (zip, rar, tar.gz, 7z)

### Keyboard Control Mode

Navigate and interact with pages using only your keyboard:

```bash
zen control
```

**Controls:**
- `Tab` / `Shift+Tab` - Navigate forward/backward
- `Arrow Keys` - Move focus directionally
- `Enter` / `Space` - Activate focused element
- `Escape` - Return to body
- `q` - Quit control mode

**Features:**
- Auto-refocus after navigation
- Visual feedback with blue outlines
- Real-time terminal announcements
- Optional text-to-speech (macOS)
- Persistent across page loads

**Configuration** (`config.json`):
```json
{
  "control": {
    "verbose": true,       // Terminal announcements
    "speak-all": true,     // Text-to-speech
    "verbose-logging": false
  }
}
```

**Example workflow:**
```bash
zen control
# Tab to link → Enter → Page loads → Element auto-refocuses → Continue tabbing
```

### Text Selection

```bash
# Get selected text with metadata
zen selected

# Raw text only
zen selected --raw

# Use in scripts
zen selected --raw | pbcopy
zen selected --raw > selection.txt
```

### Send Text to Browser

Type text character by character:

```bash
# Type into focused field
zen send "Hello World"

# Type into specific element
zen send "test@example.com" --selector "input[type=email]"
```

### Take Screenshots

```bash
# Screenshot by selector
zen screenshot --selector "h1" --output screenshot.png

# Use inspected element ($0 in DevTools)
zen screenshot --selector "$0" --output element.png
```

### Navigation

```bash
# Navigate to URL
zen open https://example.com

# Navigate and wait for load
zen open https://example.com --wait

# Browser history
zen back
zen forward

# Reload page
zen reload

# Hard reload (bypass cache)
zen reload --hard
```

### Watch Events

Monitor browser activity in real-time:

```bash
# Watch keyboard input
zen watch input
```

Output:
```
Watching keyboard input... (Press Ctrl+C to stop)
H e l l o [SPACE] W o r l d [ENTER]
```

### Cookie Management

```bash
zen cookies
```

## 🎯 Practical Examples

### Web Scraping

```bash
# Extract all product prices
zen eval "Array.from(document.querySelectorAll('.price')).map(el => el.textContent)"

# Get all image URLs
zen eval "Array.from(document.images).map(img => img.src)" --format json

# Extract table data
zen exec zen/scripts/extract_table.js --format json > data.json
```

### Authenticated Data Extraction

```bash
# Extract dashboard data (while logged in)
zen eval "
  Array.from(document.querySelectorAll('.dashboard-item')).map(item => ({
    title: item.querySelector('.title').textContent,
    value: item.querySelector('.value').textContent
  }))
" --format json > dashboard.json
```

### Form Automation

```bash
# Fill form fields
zen eval "document.querySelector('#email').value = 'user@example.com'"
zen eval "document.querySelector('#password').value = 'secret'"
zen click "button[type=submit]"
zen wait ".success-message" --visible
```

### Performance Monitoring

```bash
# Page load time
zen eval "(performance.timing.loadEventEnd - performance.timing.navigationStart) + 'ms'"

# Memory usage
zen eval "Math.round(performance.memory.usedJSHeapSize / 1048576) + 'MB'"

# Full performance metrics
zen exec zen/scripts/performance_metrics.js --format json
```

### Debugging & Development

```bash
# Check React/Redux state
zen eval "window.__REDUX_DEVTOOLS_EXTENSION__?.store.getState()" --format json

# Inspect app state
zen eval "window.myApp?.state" --format json

# Console log monitoring
zen watch
```

### SEO Analysis

```bash
# Extract metadata
zen exec zen/scripts/extract_metadata.js --format json

# Get all headings
zen outline

# Find broken internal links
zen links --only-internal --only-urls | xargs -I {} curl -s -o /dev/null -w "%{http_code} {}\n" {}

# Check external link status
zen links --enrich-external --json
```

### Shell Integration

```bash
# Use in scripts
TITLE=$(zen eval "document.title" --format raw)
echo "Current page: $TITLE"

# Monitor for changes
while true; do
  zen eval "document.querySelectorAll('.notification').length" --format raw
  sleep 5
done

# Process with other tools
zen links --only-urls | grep "github" | sort | uniq
```

## 🛠️ Built-in Scripts

Zen includes ready-to-use scripts for common tasks:

```bash
# Extract all images
zen exec zen/scripts/extract_images.js --format json

# Extract table data to JSON
zen exec zen/scripts/extract_table.js --format json > data.json

# Get SEO metadata (Open Graph, Twitter Cards, etc.)
zen exec zen/scripts/extract_metadata.js --format json

# Performance metrics
zen exec zen/scripts/performance_metrics.js --format json

# Inject jQuery
zen exec zen/scripts/inject_jquery.js
# Then use: zen eval "$('a').length"

# Highlight elements
# Edit zen/scripts/highlight_selector.js to change selector
zen exec zen/scripts/highlight_selector.js
```

## 📚 Command Reference

Run `zen --help` to see all commands with their available flags and options:

```bash
zen --help
```

The enhanced help system shows:
- All available commands
- Complete flag documentation for each command
- Default values
- Usage examples

For command-specific help:
```bash
zen eval --help
zen links --help
zen control --help
```

## ⚙️ Configuration

**Server Ports:**
- HTTP: `127.0.0.1:8765` (CLI ⟷ Server)
- WebSocket: `127.0.0.1:8766` (Server ⟷ Browser)

**Config File:** `config.json`

```json
{
  "control": {
    "verbose": true,
    "speak-all": true,
    "verbose-logging": false
  }
}
```

**Customizable Prompts:**
- `prompts/summary.prompt` - AI summarization prompt
- `prompts/describe.prompt` - Page description prompt

## 🏗️ Architecture

The bridge uses a **WebSocket-based architecture** for fast, bidirectional communication:

```
┌─────────┐         ┌────────────┐         ┌─────────────┐
│   CLI   │────────>│   Bridge   │<───────>│   Browser   │
│         │  HTTP   │   Server   │WebSocket│ (Userscript)│
└─────────┘         └────────────┘         └─────────────┘
```

**Key features:**
- **Fast:** ~12x faster than HTTP polling
- **Reliable:** Request IDs match commands with results
- **Persistent:** Survives page navigation with auto-reconnect
- **Optimized:** Scripts cached in memory for speed

## 🐛 Troubleshooting

### "Bridge server is not running"

Start the server:
```bash
zen server start
```

### "No response from browser"

1. Verify userscript is installed and enabled
2. Open a browser tab (userscript only works in visible tabs)
3. Check browser console for errors
4. Ensure WebSocket connection is established

### Commands timeout

```bash
# Increase timeout
zen eval "slow_operation()" --timeout 30

# Check if tab is active (inactive tabs may throttle execution)
```

### WebSocket connection issues

```bash
# Restart the server
zen server stop
zen server start

# Check server status
zen server status

# View server logs
zen server start  # (foreground mode to see logs)
```

## 🧪 Development

### Project Structure

```
zen_bridge/
├── zen/
│   ├── __init__.py        # Package info
│   ├── bridge_ws.py       # WebSocket server
│   ├── client.py          # Client library
│   ├── cli.py             # CLI interface
│   ├── config.py          # Configuration
│   ├── scripts/           # Built-in scripts
│   └── templates/         # Script templates
├── prompts/               # AI prompts
├── userscript_ws.js      # Browser userscript
├── setup.py              # Package setup
├── requirements.txt      # Dependencies
└── README.md            # Documentation
```

### Running Tests

```bash
# Start server
zen server start --daemon

# Open browser and navigate to a test page

# Run manual tests
zen eval "document.title"
zen info
zen repl
zen links
zen outline
```

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details

## 👏 Credits

Created by **Roel van Gils**

Inspired by the original KM JS Bridge concept.

Special thanks to:
- [Mozilla Readability](https://github.com/mozilla/readability) for article extraction
- [mods](https://github.com/charmbracelet/mods) for AI integration
- The open-source community

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues, feature requests, or pull requests.

## 📖 More Resources

- **[EXAMPLES.md](EXAMPLES.md)** - 50+ real-world use cases and workflows
- **GitHub Issues** - Bug reports and feature requests
- **Wiki** - Additional documentation and guides

---

**Zen Browser Bridge v1.0.0** - Control your browser from the command line.
