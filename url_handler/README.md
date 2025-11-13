# Inspekt URL Handler

This directory contains the `inspekt://` URL scheme handler for macOS, allowing you to trigger Inspekt commands from anywhere on your system.

## Quick Start

```bash
# Install
./install.sh

# Test
open "inspekt://info"

# Uninstall
./install.sh remove
```

## Files

- **`inspekt_url_handler.py`** - Main URL handler script that parses and executes commands
- **`install.sh`** - Installation script (creates app bundle and registers protocol)
- **`test_links.html`** - Interactive test page with example links
- **`README.md`** - This file

## Installation

The installation script will:
1. Create `/Applications/Inspekt.app` bundle
2. Register the `inspekt://` protocol with macOS
3. Enable URL triggering from any application

```bash
./install.sh
```

**Note:** Requires sudo access to create files in `/Applications/`

## Usage

### From Terminal
```bash
open "inspekt://info"
open "inspekt://eval?code=document.title"
open "inspekt://selection?format=markdown&output=clipboard"
```

### From Browser
Click any `inspekt://` link or create bookmarklets:
```javascript
javascript:window.location='inspekt://selection?format=markdown'
```

### From Shortcuts.app
1. Add "Open URL" action
2. Enter: `inspekt://eval?code=document.title&output=clipboard`
3. Add "Get Clipboard" to retrieve result

### From AppleScript
```applescript
tell application "System Events"
    open location "inspekt://info"
end tell
delay 1
set result to the clipboard
```

## Output Modes

Control where command output goes with the `output` parameter:

| Mode | Description |
|------|-------------|
| `clipboard` (default) | Copy to clipboard |
| `notification` | Show macOS notification |
| `both` | Clipboard + notification |
| `silent` | No output (errors still show) |

**Examples:**
```
inspekt://eval?code=document.title&output=clipboard
inspekt://selection?format=markdown&output=notification
inspekt://info&output=both
```

## Available Commands

### Navigation
- `inspekt://open?url=<url>` - Navigate to URL
- `inspekt://back` - Go back
- `inspekt://forward` - Go forward
- `inspekt://reload` - Reload page

### Execution
- `inspekt://eval?code=<js>` - Execute JavaScript

### Selection
- `inspekt://selection?format=text` - Get selected text
- `inspekt://selection?format=html` - Get selected HTML
- `inspekt://selection?format=markdown` - Get as Markdown

### Interaction
- `inspekt://click?selector=<css>` - Click element
- `inspekt://type?text=<text>&selector=<css>` - Type text
- `inspekt://paste?text=<text>` - Paste text

### Inspection
- `inspekt://inspect?selector=<css>` - Inspect element
- `inspekt://screenshot?selector=<css>` - Screenshot element

### Cookies
- `inspekt://cookies?action=list` - List cookies
- `inspekt://cookies?action=get&name=<name>` - Get cookie
- `inspekt://cookies?action=set&name=<name>&value=<value>` - Set cookie
- `inspekt://cookies?action=delete&name=<name>` - Delete cookie

### Info
- `inspekt://info` - Get page information

## Testing

Open the test page with interactive examples:
```bash
open test_links.html
```

Or test from command line:
```bash
# Get page title (copies to clipboard)
open "inspekt://eval?code=document.title"
sleep 1
pbpaste

# Get selected text as markdown
open "inspekt://selection?format=markdown"
sleep 1
pbpaste
```

## Troubleshooting

### "No application to open URL"
```bash
# Re-run installation
./install.sh

# Verify registration
/System/Library/Frameworks/CoreServices.framework/Versions/A/Frameworks/LaunchServices.framework/Versions/A/Support/lsregister -dump | grep inspekt
```

### Commands not working
```bash
# Check servers are running
inspekt server status

# Start servers if needed
inspekt api start -d

# Test CLI directly
inspekt info
```

### No output
- Check output mode (try `&output=both`)
- Verify notifications are enabled
- Test manually: `/Applications/Inspekt.app/Contents/MacOS/Inspekt "inspekt://info"`

## Uninstallation

```bash
./install.sh remove
```

This removes:
- `/Applications/Inspekt.app`
- Protocol registration

## Documentation

Full documentation: [../docs/url-scheme.md](../docs/url-scheme.md)

## Requirements

- macOS 10.10 or later
- Inspekt CLI installed (`pip install -e .`)
- Bridge server running (`inspekt server start`)

## Security

- Handler executes with your user permissions
- Be cautious with untrusted `inspekt://` links
- All execution is local (no external requests)
- JavaScript runs in your browser context

## Development

To modify the handler:

1. Edit `inspekt_url_handler.py`
2. No need to reinstall - changes take effect immediately
3. Test: `/Applications/Inspekt.app/Contents/MacOS/Inspekt "inspekt://info"`

## Architecture

```
User clicks inspekt:// link
       ↓
macOS LaunchServices recognizes protocol
       ↓
/Applications/Inspekt.app launched
       ↓
MacOS/Inspekt (shell script)
       ↓
inspekt_url_handler.py
       ↓
Executes: inspekt <command> <args>
       ↓
Output → Clipboard/Notification
```

## Examples

See [test_links.html](test_links.html) for interactive examples.

**Bookmarklet to copy selection as markdown:**
```javascript
javascript:window.location='inspekt://selection?format=markdown&output=clipboard'
```

**Shortcut to get page title:**
```
1. Open URL: inspekt://eval?code=document.title&output=clipboard
2. Get Clipboard
3. Show Result
```

**Alfred workflow:**
```applescript
on alfred_script(q)
    do shell script "open 'inspekt://eval?code=" & q & "'"
end alfred_script
```

## License

Same as Inspekt CLI (MIT)
