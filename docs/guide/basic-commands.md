# Basic Commands

Learn the essential commands for everyday use with Zen Bridge. This guide covers the most common commands you'll use for executing code, getting page information, managing the server, and working interactively.

## Server Management

Before you can use any commands, the bridge server must be running.

### Starting the Server

=== "Background Mode (Recommended)"
    ```bash
    zen server start --daemon
    ```

    Starts the server in the background. You can close your terminal and the server keeps running.

=== "Foreground Mode"
    ```bash
    zen server start
    ```

    Starts the server in foreground mode. Useful for debugging. Press `Ctrl+C` to stop.

=== "Custom Port"
    ```bash
    zen server start --port 9000 --daemon
    ```

    Start on a different port (default is 8765).

!!! tip "Auto-start on Login"
    On macOS/Linux, you can create a launch agent or systemd service to start the server automatically when you log in.

### Checking Server Status

```bash
zen server status
```

**Example output:**
```
Bridge server is running
  Pending requests:   0
  Completed requests: 42
```

Shows:
- Whether the server is running
- Number of pending requests
- Total completed requests since server started

### Stopping the Server

```bash
zen server stop
```

Only works if the server is running in foreground mode. For daemon mode, use:

```bash
pkill -f "zen server"
```

!!! warning "Daemon Mode Limitation"
    There's no built-in daemon stop command yet. Use `pkill` as shown above.

---

## Executing JavaScript Code

The `zen eval` command is your primary way to execute JavaScript in the browser.

### Basic Syntax

```bash
zen eval "javascript_code_here"
```

### Simple Expressions

Get quick information from the page:

```bash
# Page title
zen eval "document.title"
# Output: Example Domain

# Page URL
zen eval "location.href"
# Output: https://example.com/

# Number of links
zen eval "document.links.length"
# Output: 15

# Get domain
zen eval "location.hostname"
# Output: example.com
```

### Complex Expressions

Use arrays, objects, and methods:

```bash
# Extract all links
zen eval "Array.from(document.links).map(a => a.href)"

# Get multiple properties
zen eval "({url: location.href, title: document.title, links: document.links.length})"

# Filter elements
zen eval "Array.from(document.querySelectorAll('a')).filter(a => a.hostname !== location.hostname).map(a => a.href)"
```

### Multi-line Code

For complex logic, use proper JavaScript syntax:

```bash
zen eval "
  const links = Array.from(document.querySelectorAll('a'));
  const internal = links.filter(a => a.hostname === location.hostname);
  const external = links.filter(a => a.hostname !== location.hostname);
  return {
    total: links.length,
    internal: internal.length,
    external: external.length
  };
"
```

!!! tip "Semicolons Matter"
    When using multiple statements, separate them with semicolons. The last expression is automatically returned.

### Using stdin

Pipe JavaScript code from files or other commands:

```bash
# From a file
cat script.js | zen eval

# From echo
echo "document.title" | zen eval

# From heredoc
zen eval <<'EOF'
const images = document.querySelectorAll('img');
return Array.from(images).map(img => ({
  src: img.src,
  alt: img.alt,
  width: img.naturalWidth,
  height: img.naturalHeight
}));
EOF
```

---

## Executing Files

The `zen exec` command executes JavaScript from a file.

### Basic Usage

```bash
zen exec script.js
```

Same as:
```bash
zen eval --file script.js
```

### Example Script

**script.js:**
```javascript
// Extract all product information
const products = Array.from(document.querySelectorAll('.product'));
return products.map(product => ({
  name: product.querySelector('.product-name').textContent,
  price: product.querySelector('.product-price').textContent,
  rating: product.querySelector('.product-rating')?.textContent,
  image: product.querySelector('.product-image')?.src
}));
```

**Execute:**
```bash
zen exec script.js --format json > products.json
```

### Built-in Scripts

Zen Bridge includes ready-to-use scripts:

```bash
# Extract all images with metadata
zen exec zen/scripts/extract_images.js --format json

# Extract table data
zen exec zen/scripts/extract_table.js --format json

# Get SEO metadata
zen exec zen/scripts/extract_metadata.js --format json

# Performance metrics
zen exec zen/scripts/performance_metrics.js --format json

# Inject jQuery
zen exec zen/scripts/inject_jquery.js
```

---

## Page Information

Get comprehensive information about the current page.

### Basic Info

```bash
zen info
```

**Output:**
```
URL:      https://example.com
Title:    Example Domain
Domain:   example.com
Protocol: https:
State:    complete
Size:     1280x720
```

Shows:
- Current URL
- Page title
- Domain name
- Protocol (http/https)
- Document ready state
- Window dimensions

### Extended Information

```bash
zen info --extended
```

Includes additional details:
- **Language & Encoding** - Page language, character set
- **Meta Tags** - Description, keywords, viewport
- **Resources** - Script count, stylesheet count, cookie count
- **Security** - HTTPS, mixed content warnings, CSP headers
- **Accessibility** - Landmark count, heading structure, alt text issues
- **SEO** - Canonical URL, Open Graph tags, structured data
- **Storage** - localStorage and sessionStorage sizes
- **Service Workers** - Registration status

### JSON Output

```bash
zen info --json
```

Outputs all information as JSON for parsing with `jq` or other tools:

```bash
zen info --json | jq '.url'
zen info --json | jq '.title'
```

---

## Interactive REPL

Start a live JavaScript session to experiment interactively.

### Starting the REPL

```bash
zen repl
```

**Output:**
```
Connected to: Example Domain
https://example.com

Type 'exit' or press Ctrl+D to quit.

zen>
```

### Using the REPL

Type JavaScript code and press Enter:

```javascript
zen> document.title
"Example Domain"

zen> document.querySelectorAll('p').length
2

zen> const links = Array.from(document.links)
undefined

zen> links.length
10

zen> links.map(a => a.href)
[
  "https://example.com/page1",
  "https://example.com/page2",
  ...
]

zen> exit
Goodbye!
```

### REPL Features

- **State preservation** - Variables persist across commands
- **Multi-line editing** - Use arrow keys to edit history
- **Auto-display** - Last expression is automatically printed
- **Error messages** - Syntax and runtime errors are shown clearly

!!! tip "REPL Shortcuts"
    - `Ctrl+D` or `exit` - Quit REPL
    - `Ctrl+C` - Cancel current line
    - `Up/Down arrows` - Navigate history

### REPL Use Cases

**Testing selectors:**
```javascript
zen> document.querySelector('.main-content')
[object HTMLDivElement]

zen> $0.textContent  // if using DevTools
"Main content here..."
```

**Experimenting with APIs:**
```javascript
zen> await fetch('/api/data').then(r => r.json())
{userId: 1, name: "John Doe"}
```

**Debugging:**
```javascript
zen> window.myApp
{state: {...}, config: {...}}

zen> window.myApp.state
{user: {...}, settings: {...}}
```

---

## Output Formatting

Control how results are displayed using the `--format` flag.

### Format Options

| Format | Description | Best For |
|--------|-------------|----------|
| `auto` (default) | Smart formatting based on output type | General use |
| `json` | Valid JSON output | Piping to `jq`, scripts |
| `raw` | Plain text, no formatting | Shell variables, parsing |

### Auto Format (Default)

```bash
zen eval "document.title"
```

Intelligently formats based on the result type:
- Strings: plain text
- Objects/Arrays: pretty-printed JSON
- Numbers: plain text
- undefined/null: "(empty)"

### JSON Format

```bash
zen eval "({title: document.title, url: location.href})" --format json
```

**Output:**
```json
{
  "title": "Example Domain",
  "url": "https://example.com"
}
```

Perfect for piping to `jq`:
```bash
zen eval "({title: document.title, url: location.href})" --format json | jq '.title'
```

### Raw Format

```bash
zen eval "document.title" --format raw
```

**Output:**
```
Example Domain
```

No extra formatting - perfect for shell variables:
```bash
TITLE=$(zen eval "document.title" --format raw)
echo "Page title is: $TITLE"
```

### Adding Metadata

Add URL and title to output:

```bash
# Add URL
zen eval "document.links.length" --url

# Add title
zen eval "document.links.length" --title

# Add both
zen eval "document.links.length" --url --title
```

**Output:**
```
URL: https://example.com
Title: Example Domain

15
```

---

## Timeout Control

Commands have a default 10-second timeout. Adjust for slow operations.

```bash
# Default timeout (10 seconds)
zen eval "document.title"

# Custom timeout (30 seconds)
zen eval "await slowOperation()" --timeout 30

# Short timeout (5 seconds)
zen eval "document.title" --timeout 5
```

!!! warning "Timeouts"
    If a command takes longer than the timeout, you'll see:
    ```
    Error: Request timed out after 10 seconds
    ```

    Increase the timeout with `--timeout`.

---

## Userscript Information

View installation instructions for the browser userscript.

```bash
zen userscript
```

Displays:
- Installation instructions
- Userscript manager links (Violentmonkey, Tampermonkey)
- How to view the userscript code

---

## Common Patterns

### Get Page Data

```bash
# Title
zen eval "document.title"

# URL
zen eval "location.href"

# Domain
zen eval "location.hostname"

# Full page info
zen info
```

### Count Elements

```bash
# All links
zen eval "document.links.length"

# All images
zen eval "document.images.length"

# Specific selector
zen eval "document.querySelectorAll('.product').length"
```

### Extract Text

```bash
# Page text
zen eval "document.body.textContent"

# Heading text
zen eval "document.querySelector('h1').textContent"

# All headings
zen eval "Array.from(document.querySelectorAll('h1,h2,h3')).map(h => h.textContent)"
```

### Check Existence

```bash
# Element exists
zen eval "document.querySelector('.modal') !== null"

# Element visible
zen eval "document.querySelector('.modal')?.offsetParent !== null"
```

---

## Error Handling

### Common Errors

**Server not running:**
```
Error: Bridge server is not running
Please start the server with: zen server start
```

**Solution:** Start the server with `zen server start --daemon`

**No browser connection:**
```
Error: No response from browser
```

**Solutions:**
- Ensure the userscript is installed and enabled
- Open a browser tab (userscript only works in active tabs)
- Check browser console for errors
- Refresh the page

**Timeout:**
```
Error: Request timed out after 10 seconds
```

**Solution:** Increase timeout with `--timeout 30`

**JavaScript error:**
```
TypeError: Cannot read property 'click' of null
```

**Solution:** Check your selectors - element may not exist

---

## Tips and Tricks

### Use Shell Variables

```bash
TITLE=$(zen eval "document.title" --format raw)
URL=$(zen eval "location.href" --format raw)

echo "Title: $TITLE"
echo "URL: $URL"
```

### Pipe to Other Tools

```bash
# Count links
zen eval "Array.from(document.links).map(a => a.href).join('\n')" --format raw | wc -l

# Filter with grep
zen eval "Array.from(document.links).map(a => a.href).join('\n')" --format raw | grep "github"

# Process with jq
zen eval "Array.from(document.links).map(a => ({text: a.textContent, href: a.href}))" --format json | jq '.[0]'
```

### Async/Await Support

```bash
zen eval "await fetch('/api/data').then(r => r.json())"
```

### Console Logging

```bash
zen eval "console.log('Debug info'); document.title"
```

Check your browser console to see the log output.

---

## Next Steps

- **[JavaScript Execution](javascript-execution.md)** - Deep dive into code execution
- **[Element Interaction](element-interaction.md)** - Click, inspect, and interact with elements
- **[Data Extraction](data-extraction.md)** - Extract structured data from pages

---

## Quick Reference

| Command | Purpose | Example |
|---------|---------|---------|
| `zen server start --daemon` | Start server in background | - |
| `zen server status` | Check server status | - |
| `zen eval "code"` | Execute JavaScript | `zen eval "document.title"` |
| `zen exec file.js` | Execute file | `zen exec script.js` |
| `zen info` | Get page info | `zen info --extended` |
| `zen repl` | Interactive mode | - |
| `zen userscript` | View userscript info | - |

---

!!! success "You're Ready!"
    You now know the essential commands to control your browser from the terminal. Explore the other guides to learn advanced features!
