# Installation

This comprehensive guide will walk you through installing Zen Browser Bridge on your system, from installing Python dependencies to setting up the browser userscript and verifying everything works correctly.

## Installation Flow

```mermaid
flowchart LR
    A[Install CLI] --> B[Install Userscript]
    B --> C[Start Server]
    C --> D[Test Connection]
    D --> E[Ready!]

    style A fill:#e1f5ff
    style B fill:#fff4e1
    style C fill:#ffe1f5
    style D fill:#fff9e6
    style E fill:#e1ffe1
```

---

## Requirements

Before you begin, ensure you have the following:

- **Python 3.11 or higher** - Check your version with `python --version` or `python3 --version`
- **pip** - Python package manager (usually included with Python)
- **A modern browser** - Chrome, Firefox, Edge, Safari, or any Chromium-based browser
- **A userscript manager extension** - We'll install this in the browser setup step

!!! tip "Python Version Check"
    Run `python3 --version` to check your Python version. If you have Python 3.10 or lower, you'll need to upgrade to Python 3.11 or higher.

    === "macOS"
        ```bash
        # Using Homebrew
        brew install python@3.11
        ```

    === "Ubuntu/Debian"
        ```bash
        sudo apt update
        sudo apt install python3.11 python3.11-pip
        ```

    === "Windows"
        Download from [python.org](https://www.python.org/downloads/) and install Python 3.11+

---

## Step 1: Install the CLI Tool

You can install Zen Browser Bridge from source (recommended for development) or via pip (when available).

=== "From Source (Recommended)"

    Clone the repository and install in development mode:

    ```bash
    # Clone the repository
    git clone https://github.com/roelvangils/zen-bridge.git
    cd zen-bridge

    # Install in development mode
    pip install -e .
    ```

    This installs the `zen` command and all dependencies. The `-e` flag means "editable" - changes to the source code will be reflected immediately.

=== "Install Dependencies Manually"

    If you prefer to manage dependencies yourself:

    ```bash
    # Clone the repository
    git clone https://github.com/roelvangils/zen-bridge.git
    cd zen-bridge

    # Install dependencies
    pip install -r requirements.txt
    ```

=== "For Development"

    If you plan to contribute or run tests:

    ```bash
    # Clone the repository
    git clone https://github.com/roelvangils/zen-bridge.git
    cd zen-bridge

    # Install with dev dependencies
    pip install -e ".[dev]"
    ```

    This includes testing tools (pytest, playwright), linters (ruff), and type checkers (mypy).

### Verify the Installation

After installation, verify the `zen` command is available:

```bash
zen --version
```

You should see output like:

```
Zen Browser Bridge v2.0.0
```

Run the help command to see available commands:

```bash
zen --help
```

!!! success "Installation Complete"
    The CLI tool is now installed! Next, we'll set up the browser connection.

---

## Step 2: Install the Browser Userscript

The browser needs a userscript to receive commands from the CLI. This userscript establishes a WebSocket connection to the server.

### 2.1 Install a Userscript Manager

First, install a userscript manager extension in your browser:

=== "Violentmonkey (Recommended)"

    **Best compatibility and open source.**

    - [Chrome/Edge](https://chrome.google.com/webstore/detail/violent-monkey/jinjaccalgkegednnccohejagnlnfdag)
    - [Firefox](https://addons.mozilla.org/firefox/addon/violentmonkey/)
    - [Safari](https://apps.apple.com/app/userscripts/id1463298887)

=== "Tampermonkey"

    **Popular alternative with many features.**

    - [Chrome/Edge](https://chrome.google.com/webstore/detail/tampermonkey/dhdgffkkebhmkfjojejmpbldmpobfkfo)
    - [Firefox](https://addons.mozilla.org/firefox/addon/tampermonkey/)
    - [Safari](https://apps.apple.com/app/tampermonkey/id1482490089)

=== "Greasemonkey (Firefox only)"

    **Classic Firefox userscript manager.**

    - [Firefox](https://addons.mozilla.org/firefox/addon/greasemonkey/)

!!! note "Browser Compatibility"
    Zen Bridge works with any browser that supports userscript managers and WebSockets. This includes all modern browsers.

### 2.2 Get the Userscript Code

Display the userscript code using the CLI:

```bash
zen userscript
```

This will output the complete userscript code to your terminal. The userscript is located at `/Users/roelvangils/zen_bridge/userscript_ws.js` in the repository.

### 2.3 Create the Userscript

Now create a new userscript in your userscript manager:

1. **Click the userscript manager icon** in your browser toolbar
2. **Create a new script** (usually a "+" or "New Script" button)
3. **Delete any default content** in the editor
4. **Paste the userscript code** from the `zen userscript` command
5. **Save the script** (usually ++ctrl+s++ or ++cmd+s++)

The userscript will automatically enable itself.

!!! tip "Quick Copy"
    To copy the userscript to your clipboard (macOS):
    ```bash
    zen userscript | pbcopy
    ```

    Or save it to a file:
    ```bash
    zen userscript > my-userscript.js
    ```

### 2.4 Verify Userscript is Active

To verify the userscript is running:

1. Open your browser's **Developer Console** (++f12++ or ++cmd+opt+i++)
2. Look for a message like: **"Zen Bridge userscript loaded"**
3. Check that the userscript manager shows the script as **enabled**

!!! warning "Userscript Scope"
    By default, the userscript runs on **all pages** (`@match *://*/*`). If you want to restrict it to specific domains, edit the `@match` line in the userscript.

---

## Step 3: Start the Bridge Server

The bridge server acts as a middleman between the CLI and browser, managing WebSocket connections and HTTP endpoints.

### 3.1 Start the Server

You can start the server in foreground or background mode:

=== "Background Mode (Daemon)"

    **Recommended for normal use:**

    ```bash
    zen server start --daemon
    ```

    The server runs in the background. You can close your terminal and it will keep running.

    Check server status:
    ```bash
    zen server status
    ```

    Stop the server:
    ```bash
    zen server stop
    ```

=== "Foreground Mode"

    **Useful for debugging:**

    ```bash
    zen server start
    ```

    The server runs in the foreground with live log output. Press ++ctrl+c++ to stop.

    Example output:
    ```
    Starting Zen Bridge WebSocket server...
    HTTP API server: http://127.0.0.1:8765
    WebSocket server: ws://127.0.0.1:8766
    Server is ready! Waiting for browser connections...
    ```

### 3.2 Server Ports

The server uses two ports:

- **HTTP API**: `http://127.0.0.1:8765` - CLI communicates with this
- **WebSocket**: `ws://127.0.0.1:8766` - Browser connects to this

!!! note "Port Configuration"
    The ports are currently hardcoded. If you need to change them, you'll need to modify the server configuration and userscript.

### 3.3 Verify Server is Running

Check the server status:

```bash
zen server status
```

Expected output when running:

```
✓ Server is running
  PID: 12345
  HTTP API: http://127.0.0.1:8765
  WebSocket: ws://127.0.0.1:8766
  Connected browsers: 0
  Uptime: 2 minutes
```

---

## Step 4: Verify the Complete Setup

Now let's verify that everything is working together:

### 4.1 Open a Browser Tab

1. Open your browser (with the userscript manager and userscript installed)
2. Navigate to any website, for example: [https://example.com](https://example.com)
3. Keep the tab active (the userscript only works in active tabs)

### 4.2 Check Browser Connection

In the browser's Developer Console (++f12++), you should see:

```
Zen Bridge userscript loaded
Connected to Zen Bridge WebSocket server
```

### 4.3 Execute a Test Command

From your terminal, run a simple command:

```bash
zen eval "document.title"
```

Expected output:

```
Example Domain
```

If you see the page title, congratulations! Everything is working correctly.

!!! success "Connection Successful!"
    Your terminal is now connected to your browser. You can execute JavaScript directly in the active tab!

### 4.4 Try More Commands

```bash
# Get page information
zen info

# Get the current URL
zen eval "location.href"

# Count links on the page
zen eval "document.querySelectorAll('a').length"

# Start interactive REPL
zen repl
```

!!! success "Setup Complete!"
    You've successfully installed Zen Browser Bridge! Check out the [Quick Start Guide](quick-start.md) for a hands-on tutorial.

---

## Troubleshooting

### "zen: command not found"

**Problem**: The `zen` command is not in your PATH.

**Solutions**:

=== "Check Installation"
    ```bash
    # Verify installation
    pip show zen-bridge

    # Reinstall if needed
    pip install -e .
    ```

=== "Update PATH"
    ```bash
    # Find where pip installs scripts
    python3 -m site --user-base

    # Add to PATH (add to ~/.bashrc or ~/.zshrc)
    export PATH="$PATH:$(python3 -m site --user-base)/bin"
    ```

=== "Use python -m"
    ```bash
    # Run as a module instead
    python3 -m zen.cli --help
    ```

### "Bridge server is not running"

**Problem**: The CLI cannot connect to the server.

**Solutions**:

1. **Start the server**:
   ```bash
   zen server start --daemon
   ```

2. **Check if server is running**:
   ```bash
   zen server status
   ```

3. **Restart the server**:
   ```bash
   zen server stop
   zen server start --daemon
   ```

4. **Check for port conflicts**:
   ```bash
   # Check if ports 8765 or 8766 are in use
   lsof -i :8765
   lsof -i :8766
   ```

### "No response from browser"

**Problem**: The browser is not connected to the WebSocket server.

**Solutions**:

1. **Verify userscript is installed and enabled**
   - Check userscript manager icon
   - Ensure script is enabled

2. **Check browser console for errors**
   - Open DevTools (++f12++)
   - Look for WebSocket connection errors
   - Ensure you see "Connected to Zen Bridge WebSocket server"

3. **Ensure tab is active**
   - The userscript only works in the currently active browser tab
   - Switch to the tab and try again

4. **Restart everything**:
   ```bash
   # Stop server
   zen server stop

   # Restart browser (to reload userscript)

   # Start server
   zen server start --daemon
   ```

5. **Check WebSocket connection manually**
   - In browser console, run:
     ```javascript
     ws = new WebSocket('ws://127.0.0.1:8766')
     ws.onopen = () => console.log('Connected!')
     ```

### Command Timeout

**Problem**: Commands hang or timeout.

**Solutions**:

1. **Increase timeout**:
   ```bash
   zen eval "slow_operation()" --timeout 30
   ```

2. **Check if tab is active**:
   - Inactive tabs may throttle JavaScript execution
   - Switch to the tab and try again

3. **Check for JavaScript errors**:
   - Open browser console
   - Look for errors when command executes

### WebSocket Connection Refused

**Problem**: Browser cannot connect to WebSocket server.

**Solutions**:

1. **Verify server is running**:
   ```bash
   zen server status
   ```

2. **Check firewall settings**:
   - Ensure localhost connections are allowed
   - Port 8766 must be accessible

3. **Try a different port** (requires code modification):
   - Edit server configuration
   - Update userscript to match

### Python Version Issues

**Problem**: Zen Bridge requires Python 3.11+, but you have an older version.

**Solution**: Upgrade Python:

=== "macOS (Homebrew)"
    ```bash
    brew install python@3.11
    # Update PATH in ~/.zshrc or ~/.bashrc
    export PATH="/usr/local/opt/python@3.11/bin:$PATH"
    ```

=== "Ubuntu/Debian"
    ```bash
    sudo apt update
    sudo apt install python3.11 python3.11-pip
    # Use python3.11 explicitly
    python3.11 -m pip install -e .
    ```

=== "Windows"
    Download and install from [python.org](https://www.python.org/downloads/)

---

## Uninstallation

To uninstall Zen Browser Bridge:

### 1. Stop the Server

```bash
zen server stop
```

### 2. Uninstall the Package

```bash
# If installed with pip
pip uninstall zen-bridge

# If installed from source, just delete the directory
rm -rf ~/zen-bridge
```

### 3. Remove Browser Userscript

1. Click userscript manager icon
2. Find "Zen Bridge" script
3. Delete or disable the script

---

## Next Steps

Now that you have Zen Browser Bridge installed, continue with:

- **[Quick Start Guide](quick-start.md)** - 5-minute hands-on tutorial
- **[Configuration](configuration.md)** - Customize your setup
- **[User Guide](../guide/overview.md)** - Learn all commands and features

---

## Additional Resources

- **[GitHub Repository](https://github.com/roelvangils/zen-bridge)** - Source code and issues
- **[Architecture Guide](../development/architecture.md)** - How Zen Bridge works internally
- **[Security Guide](../development/security.md)** - Security model and best practices
