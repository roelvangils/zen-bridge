# Basic Commands

Learn the essential commands for everyday use with Inspekt. This guide covers the most common commands you'll use for executing code, getting page information, managing the server, and working interactively.

## Server Management

Before you can use any commands, the bridge server must be running.

### Starting the Server

=== "Background Mode (Recommended)"
    ```bash
    inspekt server start --daemon
    ```

    Starts the server in the background. You can close your terminal and the server keeps running.

=== "Foreground Mode"
    ```bash
    inspekt server start
    ```

    Starts the server in foreground mode. Useful for debugging. Press `Ctrl+C` to stop.

=== "Custom Port"
    ```bash
    inspekt server start --port 9000 --daemon
    ```

    Start on a different port (default is 8765).

!!! tip "Auto-start on Login"
    On macOS/Linux, you can create a launch agent or systemd service to start the server automatically when you log in.

### Checking Server Status

```bash
inspekt server status
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
inspekt server stop
```

Only works if the server is running in foreground mode. For daemon mode, use:

```bash
pkill -f "inspekt server"
```

!!! warning "Daemon Mode Limitation"
    There's no built-in daemon stop command yet. Use `pkill` as shown above.

---

## Executing JavaScript Code

The `inspekt eval` command is your primary way to execute JavaScript in the browser.

### Basic Syntax

```bash
inspekt eval "javascript_code_here"
```

### Simple Expressions

Get quick information from the page:

```bash
# Page title
inspekt eval "document.title"
# Output: Example Domain

# Page URL
inspekt eval "location.href"
# Output: https://example.com/

# Number of links
inspekt eval "document.links.length"
# Output: 15

# Get domain
inspekt eval "location.hostname"
# Output: example.com
```

### Complex Expressions

Use arrays, objects, and methods:

```bash
# Extract all links
inspekt eval "Array.from(document.links).map(a => a.href)"

# Get multiple properties
inspekt eval "({url: location.href, title: document.title, links: document.links.length})"

# Filter elements
inspekt eval "Array.from(document.querySelectorAll('a')).filter(a => a.hostname !== location.hostname).map(a => a.href)"
```

### Multi-line Code

For complex logic, use proper JavaScript syntax:

```bash
inspekt eval "
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
cat script.js | inspekt eval

# From echo
echo "document.title" | inspekt eval

# From heredoc
inspekt eval <<'EOF'
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

The `inspekt exec` command executes JavaScript from a file.

### Basic Usage

```bash
inspekt exec script.js
```

Same as:
```bash
inspekt eval --file script.js
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
inspekt exec script.js --format json > products.json
```

### Built-in Scripts

Inspekt includes ready-to-use scripts:

```bash
# Extract all images with metadata
inspekt exec zen/scripts/extract_images.js --format json

# Extract table data
inspekt exec zen/scripts/extract_table.js --format json

# Get SEO metadata
inspekt exec zen/scripts/extract_metadata.js --format json

# Performance metrics
inspekt exec zen/scripts/performance_metrics.js --format json

# Inject jQuery
inspekt exec zen/scripts/inject_jquery.js
```

---

## Page Information

Get comprehensive information about the current page.

### Basic Info

```bash
inspekt info
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
inspekt info --extended
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
inspekt info --json
```

Outputs all information as JSON for parsing with `jq` or other tools:

```bash
inspekt info --json | jq '.url'
inspekt info --json | jq '.title'
```

---

## Interactive REPL

Start a live JavaScript session to experiment interactively.

### Starting the REPL

```bash
inspekt repl
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
inspekt eval "document.title"
```

Intelligently formats based on the result type:
- Strings: plain text
- Objects/Arrays: pretty-printed JSON
- Numbers: plain text
- undefined/null: "(empty)"

### JSON Format

```bash
inspekt eval "({title: document.title, url: location.href})" --format json
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
inspekt eval "({title: document.title, url: location.href})" --format json | jq '.title'
```

### Raw Format

```bash
inspekt eval "document.title" --format raw
```

**Output:**
```
Example Domain
```

No extra formatting - perfect for shell variables:
```bash
TITLE=$(inspekt eval "document.title" --format raw)
echo "Page title is: $TITLE"
```

### Adding Metadata

Add URL and title to output:

```bash
# Add URL
inspekt eval "document.links.length" --url

# Add title
inspekt eval "document.links.length" --title

# Add both
inspekt eval "document.links.length" --url --title
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
inspekt eval "document.title"

# Custom timeout (30 seconds)
inspekt eval "await slowOperation()" --timeout 30

# Short timeout (5 seconds)
inspekt eval "document.title" --timeout 5
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
inspekt userscript
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
inspekt eval "document.title"

# URL
inspekt eval "location.href"

# Domain
inspekt eval "location.hostname"

# Full page info
inspekt info
```

### Count Elements

```bash
# All links
inspekt eval "document.links.length"

# All images
inspekt eval "document.images.length"

# Specific selector
inspekt eval "document.querySelectorAll('.product').length"
```

### Extract Text

```bash
# Page text
inspekt eval "document.body.textContent"

# Heading text
inspekt eval "document.querySelector('h1').textContent"

# All headings
inspekt eval "Array.from(document.querySelectorAll('h1,h2,h3')).map(h => h.textContent)"
```

### Check Existence

```bash
# Element exists
inspekt eval "document.querySelector('.modal') !== null"

# Element visible
inspekt eval "document.querySelector('.modal')?.offsetParent !== null"
```

---

## Error Handling

### Common Errors

**Server not running:**
```
Error: Bridge server is not running
Please start the server with: inspekt server start
```

**Solution:** Start the server with `inspekt server start --daemon`

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
TITLE=$(inspekt eval "document.title" --format raw)
URL=$(inspekt eval "location.href" --format raw)

echo "Title: $TITLE"
echo "URL: $URL"
```

### Pipe to Other Tools

```bash
# Count links
inspekt eval "Array.from(document.links).map(a => a.href).join('\n')" --format raw | wc -l

# Filter with grep
inspekt eval "Array.from(document.links).map(a => a.href).join('\n')" --format raw | grep "github"

# Process with jq
inspekt eval "Array.from(document.links).map(a => ({text: a.textContent, href: a.href}))" --format json | jq '.[0]'
```

### Async/Await Support

```bash
inspekt eval "await fetch('/api/data').then(r => r.json())"
```

### Console Logging

```bash
inspekt eval "console.log('Debug info'); document.title"
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
| `inspekt server start --daemon` | Start server in background | - |
| `inspekt server status` | Check server status | - |
| `inspekt eval "code"` | Execute JavaScript | `inspekt eval "document.title"` |
| `inspekt exec file.js` | Execute file | `inspekt exec script.js` |
| `inspekt info` | Get page info | `inspekt info --extended` |
| `inspekt repl` | Interactive mode | - |
| `inspekt userscript` | View userscript info | - |

---

!!! success "You're Ready!"
    You now know the essential commands to control your browser from the terminal. Explore the other guides to learn advanced features!
