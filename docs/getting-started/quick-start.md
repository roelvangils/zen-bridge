# Quick Start

Get up and running with Zen Browser Bridge in just 5 minutes! This hands-on tutorial will walk you through the basics and show you the power of browser automation from the command line.

!!! note "Prerequisites"
    Make sure you've completed the [Installation](installation.md) guide before starting this tutorial.

## Quick Start Workflow

Here's what we'll cover in this tutorial:

```mermaid
graph LR
    A[Execute JavaScript] --> B[Use REPL]
    B --> C[Extract Data]
    C --> D[Automate Tasks]
    D --> E[Advanced Features]

    style A fill:#e1f5ff
    style B fill:#fff4e1
    style C fill:#ffe1f5
    style D fill:#fff9e6
    style E fill:#e1ffe1
```

---

## Your First Commands

### Step 1: Navigate to a Test Page

Open your browser and navigate to [https://example.com](https://example.com). Keep this tab active.

### Step 2: Execute JavaScript

Run your first command to get the page title:

```bash
zen eval "document.title"
```

Expected output:

```
Example Domain
```

Congratulations! You just executed JavaScript in your browser from the terminal.

### Step 3: Try More Expressions

```bash
# Get the current URL
zen eval "location.href"
# => https://example.com/

# Count paragraphs on the page
zen eval "document.querySelectorAll('p').length"
# => 2

# Get all link URLs
zen eval "Array.from(document.links).map(a => a.href)"
# => ["https://www.iana.org/domains/example"]
```

!!! tip "Quick Tip"
    The `zen eval` command evaluates JavaScript expressions. For more complex code, use `zen exec` with a file.

---

## Interactive REPL Session

The REPL (Read-Eval-Print Loop) lets you experiment with JavaScript interactively:

```bash
zen repl
```

Try these commands in the REPL:

```javascript
// Get the page title
zen> document.title
"Example Domain"

// Query the DOM
zen> document.querySelectorAll('h1')[0].textContent
"Example Domain"

// Create an array of links
zen> Array.from(document.links).map(a => ({text: a.textContent, href: a.href}))
[{text: "More information...", href: "https://www.iana.org/domains/example"}]

// Exit the REPL
zen> exit
Goodbye!
```

!!! success "REPL Power"
    The REPL is perfect for exploring APIs, debugging, and prototyping JavaScript code before adding it to scripts.

---

## Extract Page Information

Use the `info` command to get comprehensive page details:

```bash
zen info
```

Example output:

```
URL:      https://example.com
Title:    Example Domain
Domain:   example.com
Protocol: https:
State:    complete
Size:     1280x720
```

For extended information including language, meta tags, and cookies:

```bash
zen info --extended
```

---

## Working with Links

Navigate to a page with more links (like a news site or blog), then:

### List All Links

```bash
zen links
```

Example output:

```
→ Home Page
  https://example.com/

→ About Us
  https://example.com/about

↗ External Resource
  https://other-site.com/page

Total: 15 links (12 internal, 3 external)
```

### Extract External Links Only

```bash
zen links --only-external --only-urls
```

This outputs just the URLs, one per line - perfect for piping to other tools.

### Save Links to a File

```bash
zen links --only-urls > all-links.txt
```

### Get Enriched Link Metadata

```bash
zen links --only-external --enrich-external
```

This fetches additional metadata like MIME types, file sizes, and HTTP status codes.

---

## Element Interaction

### Click an Element

```bash
# Click by CSS selector
zen click "button#submit"

# Double-click
zen double-click "div.editable"

# Right-click (context menu)
zen right-click "a.download"
```

### Highlight Elements

Useful for visual debugging:

```bash
# Highlight all headings
zen highlight "h1, h2, h3"

# Custom color
zen highlight "a" --color blue

# Clear highlights
zen highlight --clear
```

### Wait for Elements

Perfect for automation:

```bash
# Wait for element to exist (default: 30s timeout)
zen wait "button#submit"

# Wait for element to be visible
zen wait ".modal-dialog" --visible

# Wait for element to be hidden
zen wait ".loading-spinner" --hidden

# Wait for text content
zen wait "div.result" --text "Success"

# Custom timeout (10 seconds)
zen wait "div.notification" --timeout 10
```

---

## Page Structure Analysis

### View Heading Hierarchy

```bash
zen outline
```

Example output:

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

This is great for:

- Accessibility audits
- SEO analysis
- Understanding page structure

---

## Data Extraction Patterns

### Extract Table Data

```bash
zen exec zen/scripts/extract_table.js --format json > data.json
```

### Extract All Images

```bash
zen exec zen/scripts/extract_images.js --format json
```

### Get SEO Metadata

```bash
zen exec zen/scripts/extract_metadata.js --format json
```

### Custom Extraction

Extract product prices (example):

```bash
zen eval "
  Array.from(document.querySelectorAll('.product')).map(p => ({
    name: p.querySelector('.name').textContent,
    price: p.querySelector('.price').textContent
  }))
" --format json
```

!!! tip "Format Options"
    Use `--format json` for structured output, `--format raw` for plain text, or `--format default` for human-readable output.

---

## AI-Powered Features

!!! note "Requires mods"
    AI features require [mods](https://github.com/charmbracelet/mods) to be installed.

### Summarize an Article

Navigate to a news article or blog post, then:

```bash
zen summarize
```

This extracts the article content using Mozilla Readability and generates a concise summary.

### Describe a Page for Screen Readers

```bash
zen describe
```

Example output:

```
This webpage is in English. At the top you can navigate to Home, About,
Services, and Contact. The main part contains an article about browser
automation with three headings. The footer contains links to Privacy
Policy and Terms of Service.
```

Perfect for understanding page structure before diving into automation.

---

## Form Automation Example

Let's automate filling out a login form:

```bash
# Fill email field
zen eval "document.querySelector('#email').value = 'user@example.com'"

# Fill password field
zen eval "document.querySelector('#password').value = 'mypassword'"

# Click submit button
zen click "button[type=submit]"

# Wait for success message
zen wait ".success-message" --visible

# Verify we're logged in
zen eval "document.querySelector('.user-name').textContent"
```

!!! warning "Security Note"
    Be careful with passwords in command history! See the [Security Guide](../development/security.md) for best practices.

---

## Navigation Commands

```bash
# Navigate to a URL
zen open https://example.com

# Navigate and wait for page load
zen open https://example.com --wait

# Go back in history
zen back

# Go forward in history
zen forward

# Reload the page
zen reload

# Hard reload (bypass cache)
zen reload --hard
```

---

## Working with Text

### Get Selected Text

Select some text in the browser, then:

```bash
# Get selected text with metadata
zen selected

# Raw text only
zen selected --raw

# Copy to clipboard (macOS)
zen selected --raw | pbcopy
```

### Send Text to Browser

Type text character by character into focused field:

```bash
# Type into currently focused field
zen send "Hello World"

# Type into specific field
zen send "test@example.com" --selector "input[type=email]"
```

---

## Keyboard Control Mode

Navigate pages entirely with your keyboard:

```bash
zen control
```

**Controls:**

- ++tab++ / ++shift+tab++ - Navigate forward/backward
- ++arrow-up++ ++arrow-down++ ++arrow-left++ ++arrow-right++ - Move focus directionally
- ++enter++ / ++space++ - Activate focused element
- ++escape++ - Return to body
- ++q++ - Quit control mode

**Features:**

- Auto-refocus after page navigation
- Visual feedback (blue outlines)
- Real-time terminal announcements
- Optional text-to-speech (macOS)

!!! tip "Control Mode Configuration"
    Customize control mode behavior in `config.json`. See the [Configuration Guide](configuration.md).

---

## Watch Browser Events

Monitor keyboard input in real-time:

```bash
zen watch input
```

Focus any text field in the browser and start typing. The terminal will show each keystroke:

```
Watching keyboard input... (Press Ctrl+C to stop)
H e l l o [SPACE] W o r l d [ENTER]
```

Press ++ctrl+c++ to stop watching.

---

## Execute JavaScript from Files

Create a file `extract-titles.js`:

```javascript
// Extract all headings from the page
const headings = Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, h6'))
  .map(h => ({
    level: h.tagName,
    text: h.textContent.trim(),
    id: h.id
  }));

headings;  // Return value
```

Execute it:

```bash
zen exec extract-titles.js --format json
```

Or use the shorthand:

```bash
zen exec extract-titles.js --format json
# Same as:
zen eval --file extract-titles.js --format json
```

---

## Working with Output Formats

Zen Bridge supports multiple output formats:

=== "Default (Human-Readable)"

    ```bash
    zen eval "({title: document.title, url: location.href})"
    ```

    Output:
    ```
    {
      title: "Example Domain",
      url: "https://example.com/"
    }
    ```

=== "JSON"

    ```bash
    zen eval "({title: document.title, url: location.href})" --format json
    ```

    Output:
    ```json
    {
      "title": "Example Domain",
      "url": "https://example.com/"
    }
    ```

=== "Raw"

    ```bash
    zen eval "document.title" --format raw
    ```

    Output:
    ```
    Example Domain
    ```

    No extra formatting - perfect for piping to other commands.

---

## Combining with Shell Commands

Zen Bridge plays nicely with standard Unix tools:

```bash
# Count external links
zen links --only-external --only-urls | wc -l

# Find all PDF links
zen links --only-urls | grep "\.pdf$"

# Get unique domains from external links
zen links --only-external --only-urls | sed 's|https\?://\([^/]*\).*|\1|' | sort | uniq

# Export data and process with jq
zen eval "Array.from(document.querySelectorAll('a')).map(a => ({text: a.textContent, href: a.href}))" --format json | jq '.[0:5]'
```

---

## Common Patterns and Recipes

### Check if Element Exists

```bash
zen eval "document.querySelector('#element-id') !== null"
# => true or false
```

### Get Computed Style

```bash
zen eval "getComputedStyle(document.querySelector('h1')).color"
# => rgb(0, 0, 0)
```

### Scroll to Bottom

```bash
zen eval "window.scrollTo(0, document.body.scrollHeight)"
```

### Take Screenshot of Element

```bash
# Screenshot by selector
zen screenshot --selector "h1" --output screenshot.png

# Screenshot inspected element (set in DevTools)
zen screenshot --selector "$0" --output element.png
```

### Monitor for Changes

```bash
# Check element count every 5 seconds
while true; do
  zen eval "document.querySelectorAll('.notification').length" --format raw
  sleep 5
done
```

### Extract and Download Files

```bash
# Interactive file finder
zen download

# List all downloadable files
zen download --list

# Custom output directory
zen download --output ~/Downloads
```

---

## Troubleshooting Tips

### Command Hangs or Times Out

```bash
# Increase timeout (in seconds)
zen eval "slowOperation()" --timeout 30
```

### "No response from browser"

1. Ensure browser tab is **active** (not in background)
2. Check browser console for errors (++f12++)
3. Verify WebSocket connection in console:
   ```javascript
   // Should see "Connected to Zen Bridge WebSocket server"
   ```

### Check Server Status

```bash
zen server status
```

If server isn't running:

```bash
zen server start --daemon
```

---

## Next Steps

Now that you've mastered the basics, explore these resources:

<div class="grid cards" markdown>

-   :wrench: __Configuration__

    ---

    Customize Zen Bridge for your workflow - control mode, AI settings, and more.

    [:octicons-arrow-right-24: Configuration Guide](configuration.md)

-   :books: __User Guide__

    ---

    Deep dive into all commands, features, and advanced usage patterns.

    [:octicons-arrow-right-24: User Guide](../guide/overview.md)

-   :page_with_curl: __Built-in Scripts__

    ---

    Explore ready-to-use scripts for common tasks like data extraction and SEO analysis.

    [:octicons-arrow-right-24: Scripts Reference](../guide/advanced.md#built-in-scripts)

-   :hammer_and_wrench: __API Reference__

    ---

    Complete command reference with all flags and options.

    [:octicons-arrow-right-24: CLI Commands](../api/commands.md)

</div>

---

## Practice Challenges

Try these exercises to build your skills:

!!! example "Challenge 1: Link Analysis"
    Navigate to your favorite news site and:

    1. Count total links on the homepage
    2. Extract all external links
    3. Find all links containing "privacy" or "terms"
    4. Save results to a file

    ??? success "Solution"
        ```bash
        # 1. Count total links
        zen eval "document.querySelectorAll('a').length"

        # 2. Extract external links
        zen links --only-external --only-urls > external.txt

        # 3. Find privacy/terms links
        zen links --only-urls | grep -E "(privacy|terms)"

        # 4. Already saved in step 2!
        ```

!!! example "Challenge 2: Form Automation"
    Find a demo contact form online and:

    1. Fill all fields programmatically
    2. Submit the form
    3. Wait for success message
    4. Extract the success message text

    ??? success "Solution"
        ```bash
        # 1. Fill fields
        zen eval "document.querySelector('#name').value = 'John Doe'"
        zen eval "document.querySelector('#email').value = 'john@example.com'"
        zen eval "document.querySelector('#message').value = 'Hello!'"

        # 2. Submit
        zen click "button[type=submit]"

        # 3. Wait for success
        zen wait ".success-message" --visible

        # 4. Extract message
        zen eval "document.querySelector('.success-message').textContent"
        ```

!!! example "Challenge 3: Data Extraction"
    Navigate to a Wikipedia article and:

    1. Get the article title
    2. Count all sections (h2 headings)
    3. Extract all image URLs
    4. Create JSON with all the data

    ??? success "Solution"
        ```bash
        # 1. Get title
        zen eval "document.querySelector('h1').textContent"

        # 2. Count sections
        zen eval "document.querySelectorAll('h2').length"

        # 3. Extract images
        zen eval "Array.from(document.querySelectorAll('img')).map(img => img.src)"

        # 4. Create JSON
        zen eval "{
          title: document.querySelector('h1').textContent,
          sections: document.querySelectorAll('h2').length,
          images: Array.from(document.querySelectorAll('img')).map(img => img.src)
        }" --format json > wikipedia.json
        ```

---

## Quick Reference Card

| Task | Command |
|------|---------|
| Execute JavaScript | `zen eval "code"` |
| Interactive REPL | `zen repl` |
| Page info | `zen info` |
| Extract links | `zen links` |
| Click element | `zen click "selector"` |
| Wait for element | `zen wait "selector" --visible` |
| Highlight elements | `zen highlight "selector"` |
| Page outline | `zen outline` |
| AI summary | `zen summarize` |
| Page description | `zen describe` |
| Keyboard control | `zen control` |
| Watch events | `zen watch input` |
| Server status | `zen server status` |
| Get help | `zen --help` |

---

Happy automating! If you run into any issues, check the [Troubleshooting](installation.md#troubleshooting) section or [open an issue](https://github.com/roelvangils/zen-bridge/issues) on GitHub.
