# Element Interaction

Master element interaction in Zen Bridge. Learn how to click, inspect, highlight, wait for elements, send keyboard input, and take screenshots - all from your terminal.

## Overview

Zen Bridge provides specialized commands for interacting with page elements:

- `zen click` - Click elements
- `zen double-click` / `zen right-click` - Double-click and right-click
- `zen wait` - Wait for elements to appear/disappear
- `zen send` - Type text into elements
- `zen inspect` / `zen inspected` - Inspect elements
- `zen highlight` - Highlight elements visually
- `zen screenshot` - Screenshot elements

## Clicking Elements

### Basic Click

```bash
zen click "button#submit"
```

Clicks the first element matching the selector.

### Click Examples

```bash
# Click button by ID
zen click "#submit-btn"

# Click link by class
zen click ".nav-link"

# Click by complex selector
zen click "nav > ul > li:first-child > a"

# Click by attribute
zen click "[data-action='delete']"

# Click by text content (using eval)
zen eval "Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Submit')).click()"
```

### Using Inspected Element

You can click the currently inspected element (from DevTools):

```bash
# In DevTools, select an element ($0)
# In browser console: zenStore($0)

# Then click it
zen click
# or explicitly
zen click "$0"
```

### Double Click

Double-click elements for actions that require it:

```bash
zen double-click "div.editable"
zen double-click ".file-item"
```

### Right Click (Context Menu)

Trigger context menus:

```bash
zen right-click "a.download-link"
zen right-click ".file-item"
```

!!! tip "Click Types"
    - `zen click` - Single left click
    - `zen double-click` - Double left click
    - `zen right-click` - Right click (context menu)

---

## Waiting for Elements

The `zen wait` command waits for elements to appear, become visible, become hidden, or contain specific text.

### Wait for Element to Exist

```bash
# Wait up to 30 seconds (default)
zen wait "button#submit"

# Custom timeout
zen wait ".modal" --timeout 10
```

### Wait for Element to be Visible

```bash
zen wait ".modal-dialog" --visible

# With custom timeout
zen wait ".notification" --visible --timeout 15
```

### Wait for Element to be Hidden

```bash
zen wait ".loading-spinner" --hidden

# Wait for modal to close
zen wait ".modal-overlay" --hidden --timeout 20
```

### Wait for Specific Text

```bash
# Wait for element with specific text
zen wait "div.result" --text "Success"

# Wait for error message
zen wait ".message" --text "Error" --visible
```

### Wait Use Cases

**Wait for page load:**
```bash
zen wait "main.content" --visible
```

**Wait for AJAX content:**
```bash
zen wait ".dynamic-content" --visible --timeout 20
```

**Wait for form validation:**
```bash
# Fill form
zen eval "document.querySelector('#email').value = 'test@example.com'"

# Submit
zen click "#submit-btn"

# Wait for success message
zen wait ".success-message" --visible
```

**Wait for loading to finish:**
```bash
# Click action that shows spinner
zen click ".load-more"

# Wait for spinner to disappear
zen wait ".spinner" --hidden
```

!!! warning "Timeout Default"
    Default timeout is **30 seconds**. Adjust with `--timeout` flag.

---

## Sending Keyboard Input

The `zen send` command types text character by character, simulating keyboard input.

### Basic Text Input

```bash
zen send "Hello World"
```

Types into the currently focused element.

### Send to Specific Element

```bash
# Type into email input
zen send "test@example.com" --selector "input[type=email]"

# Type into search box
zen send "query text" --selector "input[name=search]"

# Type into textarea
zen send "Multi-line text here" --selector "textarea#message"
```

### Form Filling Examples

**Login form:**
```bash
zen send "user@example.com" --selector "#email"
zen send "password123" --selector "#password"
zen click "#login-btn"
```

**Search form:**
```bash
zen send "Zen Bridge documentation" --selector "input[name=q]"
zen click "button[type=submit]"
```

**Comment form:**
```bash
zen send "Great article!" --selector "textarea#comment"
zen send "John Doe" --selector "input#name"
zen click "button#post-comment"
```

### Typing Speed

The `send` command types at a realistic speed (character by character). For instant value setting, use `zen eval`:

```bash
# Instant value (no events)
zen eval "document.querySelector('#email').value = 'test@example.com'"

# Typed input (fires input events)
zen send "test@example.com" --selector "#email"
```

!!! tip "Input Events"
    `zen send` fires proper keyboard events, which may trigger validation, autocomplete, and other event listeners.

---

## Inspecting Elements

### Inspect Element

Select and store an element for inspection:

```bash
zen inspect "h1"
```

**Output:**
```
Element: H1
Text: Welcome to Example
Classes: page-title, main-heading
ID: title
```

### Inspect by Selector

```bash
# By ID
zen inspect "#header"

# By class
zen inspect ".main-content"

# By complex selector
zen inspect "nav > ul > li:first-child > a"

# By attribute
zen inspect "[data-id='123']"
```

### Get Inspected Element Details

After inspecting an element, get detailed information:

```bash
zen inspected
```

**Output:**
```json
{
  "tagName": "H1",
  "textContent": "Welcome to Example",
  "id": "title",
  "className": "page-title main-heading",
  "attributes": {
    "id": "title",
    "class": "page-title main-heading",
    "data-section": "hero"
  },
  "boundingBox": {
    "x": 100,
    "y": 50,
    "width": 600,
    "height": 80
  }
}
```

### Using DevTools Integration

You can also store the currently selected element in DevTools:

1. Open DevTools (F12)
2. Select an element (inspect tool or click in Elements panel)
3. In console, run: `zenStore($0)`
4. Then use: `zen inspected`

!!! tip "Workflow"
    Use `zen inspect` to find elements programmatically, or use DevTools + `zenStore($0)` for visual selection.

---

## Highlighting Elements

Visually highlight elements on the page with colored outlines.

### Basic Highlight

```bash
zen highlight "h1, h2"
```

Highlights all matching elements with a red dashed outline.

### Custom Color

```bash
zen highlight "a" --color blue
zen highlight ".error" --color red
zen highlight ".success" --color green
zen highlight ".warning" --color orange
```

### Clear Highlights

```bash
zen highlight --clear
```

Removes all highlights from the page.

### Highlight Use Cases

**Debugging layout:**
```bash
zen highlight "div"
```

**Find all links:**
```bash
zen highlight "a" --color blue
```

**Highlight errors:**
```bash
zen highlight ".error-message" --color red
```

**Accessibility audit:**
```bash
# Highlight images without alt text
zen eval "
  document.querySelectorAll('img:not([alt])').forEach(img => {
    img.style.outline = '3px solid red';
  });
  'Highlighted images without alt text';
"
```

---

## Screenshots

Take screenshots of specific elements.

### Screenshot Element

```bash
zen screenshot --selector "h1" --output screenshot.png
```

### Screenshot Examples

```bash
# Screenshot by selector
zen screenshot --selector "#header" --output header.png

# Screenshot with auto-generated filename
zen screenshot --selector ".hero-section"

# Screenshot of inspected element
zen inspect "h1"
zen screenshot --selector "$0" --output title.png
```

### Screenshot Use Cases

**Visual regression testing:**
```bash
zen screenshot --selector ".hero" --output hero-$(date +%Y%m%d).png
```

**Documentation:**
```bash
zen screenshot --selector ".component-example" --output docs/component.png
```

**Bug reports:**
```bash
zen screenshot --selector ".error-dialog" --output bug-screenshot.png
```

!!! note "Screenshot Format"
    Screenshots are saved as PNG files. The `--output` flag is optional; a timestamp-based filename is generated if omitted.

---

## CSS Selectors Explained

Zen Bridge uses standard CSS selectors. Here's a quick reference:

### Basic Selectors

| Selector | Example | Description |
|----------|---------|-------------|
| Element | `div` | Select by tag name |
| Class | `.button` | Select by class |
| ID | `#submit` | Select by ID |
| Attribute | `[type="text"]` | Select by attribute |
| Universal | `*` | Select all elements |

### Combinators

| Combinator | Example | Description |
|------------|---------|-------------|
| Descendant | `div p` | All `<p>` inside `<div>` |
| Child | `div > p` | Direct children only |
| Adjacent sibling | `h1 + p` | `<p>` immediately after `<h1>` |
| General sibling | `h1 ~ p` | All `<p>` siblings after `<h1>` |

### Pseudo-classes

| Pseudo-class | Example | Description |
|--------------|---------|-------------|
| `:first-child` | `li:first-child` | First child element |
| `:last-child` | `li:last-child` | Last child element |
| `:nth-child(n)` | `li:nth-child(2)` | Nth child element |
| `:not(selector)` | `:not(.active)` | Elements not matching |
| `:hover` | `a:hover` | Hovered elements |

### Complex Selectors

```bash
# Multiple classes
zen click ".button.primary"

# Attribute with value
zen click "[data-action='submit']"

# Attribute contains
zen click "[class*='modal']"

# Attribute starts with
zen click "[id^='btn-']"

# Attribute ends with
zen click "[href$='.pdf']"

# Multiple selectors
zen highlight "h1, h2, h3"

# Complex combination
zen click "nav > ul > li:first-child > a.active"
```

---

## Interactive Examples

### Example 1: Form Automation

```bash
# Fill login form
zen send "user@example.com" --selector "#email"
zen send "password123" --selector "#password"
zen click "#remember-me"
zen click "#login-btn"

# Wait for redirect or error
zen wait ".dashboard, .error-message" --visible --timeout 10
```

### Example 2: Modal Interaction

```bash
# Open modal
zen click "#open-modal"

# Wait for modal to appear
zen wait ".modal-dialog" --visible

# Interact with modal
zen send "Test message" --selector ".modal textarea"
zen click ".modal button.confirm"

# Wait for modal to close
zen wait ".modal-dialog" --hidden
```

### Example 3: Dynamic Content

```bash
# Click "Load More" button
zen click ".load-more"

# Wait for spinner to disappear
zen wait ".loading-spinner" --hidden

# Count new items
zen eval "document.querySelectorAll('.item').length"
```

### Example 4: Multi-step Flow

```bash
# Step 1: Fill first form
zen send "John" --selector "#first-name"
zen send "Doe" --selector "#last-name"
zen click "#next-btn"

# Step 2: Wait and fill second form
zen wait "#email" --visible
zen send "john@example.com" --selector "#email"
zen send "1234567890" --selector "#phone"
zen click "#submit-btn"

# Step 3: Wait for confirmation
zen wait ".success-message" --visible --text "Success"
```

### Example 5: Visual Testing

```bash
# Highlight all buttons
zen highlight "button" --color blue

# Inspect specific button
zen inspect "button.primary"

# Take screenshot
zen screenshot --selector "button.primary" --output button.png

# Clear highlights
zen highlight --clear
```

---

## Advanced Patterns

### Conditional Clicking

```bash
# Click only if element exists
zen eval "
  const button = document.querySelector('#optional-btn');
  if (button) {
    button.click();
    return 'Clicked';
  }
  return 'Button not found';
"
```

### Click All Matching Elements

```bash
# Click all checkboxes
zen eval "
  document.querySelectorAll('input[type=checkbox]').forEach(cb => cb.click());
  return 'Clicked all checkboxes';
"
```

### Wait with Polling

```bash
zen eval "
  async function waitForElement(selector, timeout = 30000) {
    const start = Date.now();
    while (Date.now() - start < timeout) {
      const element = document.querySelector(selector);
      if (element) return element;
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    throw new Error('Timeout');
  }

  const element = await waitForElement('.dynamic-content');
  return element.textContent;
"
```

### Hover Simulation

```bash
zen eval "
  const element = document.querySelector('.menu-item');
  const event = new MouseEvent('mouseover', {
    bubbles: true,
    cancelable: true,
    view: window
  });
  element.dispatchEvent(event);
  return 'Hovered over element';
"
```

### Focus and Blur

```bash
# Focus element
zen eval "document.querySelector('#email').focus()"

# Blur element
zen eval "document.querySelector('#email').blur()"

# Type after focusing
zen eval "document.querySelector('#email').focus()"
zen send "test@example.com" --selector "#email"
```

---

## Troubleshooting

### Element Not Found

**Error:**
```
Error: Element not found: .missing-selector
```

**Solutions:**
1. Verify selector is correct
2. Wait for element to load: `zen wait ".selector" --visible`
3. Check if element is in iframe (not supported directly)
4. Use DevTools to test selector

### Click Not Working

**Possible causes:**
- Element is not visible
- Element is disabled
- JavaScript event handler expecting different event
- Element is covered by another element

**Solutions:**
```bash
# Check if visible
zen eval "document.querySelector('.btn')?.offsetParent !== null"

# Check if disabled
zen eval "document.querySelector('.btn')?.disabled"

# Force click with JavaScript
zen eval "document.querySelector('.btn').click()"

# Dispatch click event
zen eval "document.querySelector('.btn').dispatchEvent(new MouseEvent('click', {bubbles: true}))"
```

### Element Changes After Action

Some elements are replaced after interaction (e.g., React re-renders). Re-select after action:

```bash
# Wrong - selector may be stale
zen click ".btn"
zen eval "document.querySelector('.btn').textContent"

# Correct - re-select after action
zen click ".btn"
zen wait ".success-message" --visible
zen eval "document.querySelector('.success-message').textContent"
```

---

## Best Practices

### 1. Use Specific Selectors

```bash
# Good - specific
zen click "#submit-btn"
zen click "[data-testid='submit-button']"

# Avoid - too generic
zen click "button"
zen click ".btn"
```

### 2. Wait Before Interacting

```bash
# Good - wait for element
zen wait "#modal" --visible
zen click "#modal .confirm-btn"

# Risky - element may not exist yet
zen click "#modal .confirm-btn"
```

### 3. Handle Errors Gracefully

```bash
# Use optional chaining
zen eval "document.querySelector('.maybe-missing')?.click() ?? 'Element not found'"
```

### 4. Verify Actions

```bash
# Click and verify
zen click "#submit-btn"
zen wait ".success-message" --visible --text "Saved"
```

---

## Next Steps

- **[Data Extraction](data-extraction.md)** - Extract structured data from pages
- **[Control Mode](control-mode.md)** - Keyboard-only navigation
- **[Advanced Usage](advanced.md)** - Complex patterns and scripting

---

## Quick Reference

| Command | Purpose | Example |
|---------|---------|---------|
| `zen click "selector"` | Click element | `zen click "#submit"` |
| `zen double-click "selector"` | Double-click | `zen double-click ".file"` |
| `zen right-click "selector"` | Right-click | `zen right-click ".context"` |
| `zen wait "selector"` | Wait for element | `zen wait ".modal" --visible` |
| `zen send "text"` | Type text | `zen send "hello" --selector "#input"` |
| `zen inspect "selector"` | Inspect element | `zen inspect "h1"` |
| `zen inspected` | Get inspected details | `zen inspected` |
| `zen highlight "selector"` | Highlight elements | `zen highlight "a" --color blue` |
| `zen screenshot --selector` | Screenshot element | `zen screenshot --selector "h1"` |
