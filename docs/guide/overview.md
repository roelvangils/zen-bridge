# Overview

Welcome to Zen Bridge - a powerful CLI tool that lets you control your browser from the command line. Execute JavaScript, automate tasks, extract data, and interact with web pages without leaving your terminal.

## What is Zen Bridge?

Zen Bridge is a command-line interface that connects your terminal to your web browser through a WebSocket-based architecture. It allows you to:

- Execute JavaScript code in your active browser tab
- Interact with page elements (click, inspect, highlight, wait)
- Extract data (links, images, tables, metadata)
- Automate form filling and navigation
- Debug and test web applications
- Monitor browser activity in real-time
- Control your browser entirely from your keyboard

Think of it as a **bridge** between your terminal and your browser - hence the name.

## How It Works

Zen Bridge uses a three-component architecture:

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│             │  HTTP   │              │  WS     │             │
│  CLI Tool   │────────▶│    Server    │◀───────▶│   Browser   │
│  (Terminal) │  8765   │  (Python)    │  8766   │ (Userscript)│
│             │         │              │         │             │
└─────────────┘         └──────────────┘         └─────────────┘
```

### 1. CLI Tool (Your Terminal)

When you run commands like `zen eval "document.title"`, the CLI tool:

- Parses your command and options
- Formats the JavaScript code
- Sends an HTTP request to the local server
- Waits for the response
- Displays the result

### 2. Bridge Server (Background Process)

The server acts as a message broker:

- Listens for HTTP requests from the CLI (port 8765)
- Maintains WebSocket connections with browser tabs (port 8766)
- Routes commands to the active browser tab
- Returns results back to the CLI
- Runs in the background as a daemon

Start the server with:
```bash
zen server start --daemon
```

### 3. Browser Userscript (In Your Browser)

A lightweight userscript runs in your browser:

- Establishes a WebSocket connection to the server
- Receives JavaScript code from the server
- Executes the code in the page context
- Sends results back to the server
- Works across page navigations

The userscript must be installed in a userscript manager like [Violentmonkey](https://violentmonkey.github.io/) or [Tampermonkey](https://www.tampermonkey.net/).

## WebSocket Communication Explained

### Why WebSockets?

Traditional HTTP polling would be slow and inefficient. WebSockets provide:

- **Instant communication** - No polling delays
- **Bi-directional** - Server can push to browser, browser can push to server
- **Persistent connection** - One connection serves multiple commands
- **Low overhead** - Minimal latency compared to HTTP requests

### Message Flow Example

When you run `zen eval "document.title"`:

1. **CLI → Server (HTTP)**
   ```json
   POST http://127.0.0.1:8765/execute
   {
     "code": "document.title",
     "timeout": 10
   }
   ```

2. **Server → Browser (WebSocket)**
   ```json
   {
     "type": "execute",
     "code": "document.title",
     "id": "req-123"
   }
   ```

3. **Browser executes code and responds (WebSocket)**
   ```json
   {
     "type": "response",
     "id": "req-123",
     "result": "Example Domain",
     "ok": true
   }
   ```

4. **Server → CLI (HTTP Response)**
   ```json
   {
     "ok": true,
     "result": "Example Domain"
   }
   ```

5. **CLI displays output**
   ```
   Example Domain
   ```

### Security Considerations

The WebSocket connection is **local only**:

- Server binds to `127.0.0.1` (localhost)
- Not accessible from external networks
- No authentication needed (local-only access)
- Userscript only connects to localhost

This means Zen Bridge can only control browsers on your own machine.

## When to Use Zen Bridge

Zen Bridge is ideal for:

### Web Development & Debugging

- Inspect application state (`window.myApp`, Redux stores)
- Test JavaScript functions interactively
- Debug DOM manipulations
- Monitor performance metrics
- Inject jQuery or other libraries for testing

### Web Scraping & Data Extraction

- Extract data from authenticated pages (logged-in dashboards)
- Scrape tables, lists, and structured data
- Download files (images, PDFs, videos)
- Extract metadata (Open Graph, Twitter Cards)
- Monitor page changes over time

### Browser Automation

- Fill and submit forms
- Navigate through multi-page workflows
- Click buttons and interact with elements
- Wait for dynamic content to load
- Automate repetitive tasks

### Accessibility Testing

- Check heading structure (`zen outline`)
- Find images without alt text
- Test keyboard navigation (`zen control`)
- Generate page descriptions for screen readers

### Content Analysis

- Generate AI summaries of articles (`zen summarize`)
- Get concise page descriptions (`zen describe`)
- Analyze link structures
- Check SEO metadata

### Shell Scripting & CI/CD

- Integrate browser data into shell scripts
- Monitor build dashboards
- Automate visual regression testing
- Extract data for reports

## When NOT to Use Zen Bridge

Zen Bridge is **not** suitable for:

### Heavy Automation at Scale

- Use [Playwright](https://playwright.dev/) or [Puppeteer](https://pptr.dev/) for:
  - Running hundreds of parallel browser instances
  - Server-side rendering testing
  - Complex test suites with retries and parallelization

### Distributed/Remote Automation

- Zen Bridge only works on localhost
- For remote browser control, use Playwright, Puppeteer, or Selenium Grid

### Production Monitoring

- Don't rely on Zen Bridge for production monitoring
- Use proper APM tools (Datadog, New Relic, etc.)

### Privacy-Sensitive Operations

- Zen Bridge has access to everything in your browser
- Don't use it on pages with sensitive credentials
- Be careful with commands that extract cookies or local storage

## Key Features

### Execute JavaScript

Run any JavaScript code in your browser:

```bash
zen eval "document.title"
zen eval "Array.from(document.links).map(a => a.href)"
zen eval "({url: location.href, title: document.title})" --format json
```

### Interactive REPL

Live JavaScript session:

```bash
zen repl
zen> document.querySelectorAll('p').length
2
zen> exit
```

### Element Interaction

Click, inspect, highlight, and wait for elements:

```bash
zen click "button#submit"
zen inspect "h1"
zen highlight ".error" --color red
zen wait ".modal" --visible
```

### Data Extraction

Extract structured data:

```bash
zen links --only-external
zen outline
zen download
zen info --extended
```

### AI-Powered Features

Summarize and describe pages:

```bash
zen summarize
zen describe
```

Requires [mods](https://github.com/charmbracelet/mods) for AI integration.

### Keyboard Control

Navigate entirely from your keyboard:

```bash
zen control
# Use Tab, Enter, Arrow keys to navigate
# Press 'q' to quit
```

### Real-Time Monitoring

Watch browser activity:

```bash
zen watch input  # Monitor keyboard input
zen watch all    # Monitor all interactions
```

## Architecture Benefits

Zen Bridge follows a **hexagonal architecture** with clear separation of concerns:

- **Domain Layer** - Pure business logic with Pydantic models
- **Adapter Layer** - I/O operations (filesystem, WebSocket)
- **Service Layer** - Application services and orchestration
- **Application Layer** - CLI commands and server

This design ensures:

- High testability (97%+ coverage on services)
- Clear dependencies (no circular imports)
- Easy extensibility (add new commands/services)
- Maintainable codebase

See [Architecture Guide](../development/architecture.md) for technical details.

## Getting Started

Ready to try Zen Bridge? Check out these guides:

1. **[Basic Commands](basic-commands.md)** - Start here for essential commands
2. **[JavaScript Execution](javascript-execution.md)** - Master code execution
3. **[Element Interaction](element-interaction.md)** - Click, inspect, and interact
4. **[Data Extraction](data-extraction.md)** - Extract structured data
5. **[AI Features](ai-features.md)** - AI-powered summarization and descriptions
6. **[Control Mode](control-mode.md)** - Keyboard-only navigation
7. **[Advanced Usage](advanced.md)** - Scripting and best practices

## Next Steps

1. Install Zen Bridge and the userscript (see [Installation guide](../getting-started/installation.md))
2. Start the server: `zen server start --daemon`
3. Try basic commands: `zen eval "document.title"`
4. Explore the guides above
5. Check out the [API Reference](../api/commands.md) for complete documentation

## Getting Help

- Run `zen --help` to see all commands
- Run `zen <command> --help` for command-specific help
- Check the [GitHub Issues](https://github.com/roelvangils/zen-bridge/issues) for known issues
- Read the [Contributing Guide](../development/contributing.md) to contribute

Welcome to Zen Bridge - control your browser from the command line!
