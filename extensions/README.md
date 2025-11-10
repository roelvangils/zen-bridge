# Zen Browser Bridge - Extensions

Browser extensions for Zen Browser Bridge that **bypass CSP restrictions** and work on **all websites**.

## Why Extensions?

While the userscript installation is quick and easy, many important websites have **Content Security Policy (CSP)** restrictions that block WebSocket connections and script injection:

| Website Type | Userscript | Extension |
|--------------|-----------|-----------|
| **GitHub** | ❌ Blocked by CSP | ✅ Works |
| **Gmail** | ❌ Blocked by CSP | ✅ Works |
| **Banking Sites** | ❌ Blocked by CSP | ✅ Works |
| **Government Portals** | ❌ Blocked by CSP | ✅ Works |
| **Most Other Sites** | ✅ Works | ✅ Works |

**Extensions have elevated privileges** that allow them to bypass CSP restrictions safely and securely.

## Available Extensions

### Firefox Extension
✅ **Available Now** - Full CSP bypass support

📖 [Firefox Installation Guide](firefox/README.md)

**Features:**
- Works on all websites including GitHub, Gmail, banking sites
- Built-in settings panel with connection status
- DevTools integration with `zenStore($0)`
- Auto-reconnect on page navigation
- Version 4.0.0

**Installation:**
1. Download the extension files
2. Navigate to `about:debugging#/runtime/this-firefox`
3. Click "Load Temporary Add-on..."
4. Select `manifest.json` from `extensions/firefox/`

[Read full Firefox guide →](firefox/README.md)

### Chrome Extension
🚧 **Coming Soon** - In development

We're building a Chrome extension with the same CSP bypass capabilities. It will be available in `extensions/chrome/` soon.

### Edge Extension
📅 **Planned** - Future release

Microsoft Edge extension support is planned for a future release.

## Choosing Your Installation Method

### Use the Extension If:
- ✅ You need to use Zen on GitHub, Gmail, or banking sites
- ✅ You want maximum compatibility across all websites
- ✅ You don't mind a slightly more complex installation
- ✅ You want a built-in settings panel with status indicator

### Use the Userscript If:
- ✅ You want the quickest installation (one click)
- ✅ You primarily use Zen on sites without strict CSP
- ✅ You prefer userscript managers like Tampermonkey
- ✅ You want automatic updates via Tampermonkey

**Recommendation:** Start with the userscript for quick testing. If you encounter CSP issues on important sites, switch to the extension.

## How CSP Bypass Works

Extensions use the browser's native `tabs.executeScript()` API which has elevated privileges:

```
1. Content script receives execution request via WebSocket
2. Content script sends message to background script
3. Background script uses tabs.executeScript() to bypass CSP
4. Result is sent back to CLI via WebSocket
```

This is **safe and intended** - browser extensions are designed to have elevated privileges for legitimate purposes like browser automation, developer tools, and productivity enhancements.

## Feature Comparison

| Feature | Userscript | Firefox Extension | Chrome Extension |
|---------|-----------|-------------------|------------------|
| **Installation** | ⚡ One click | 🔧 Few steps | 🔧 Few steps |
| **CSP Bypass** | ❌ No | ✅ Yes | 🚧 Soon |
| **GitHub** | ❌ Blocked | ✅ Works | 🚧 Soon |
| **Gmail** | ❌ Blocked | ✅ Works | 🚧 Soon |
| **Banking Sites** | ❌ Blocked | ✅ Works | 🚧 Soon |
| **Settings Panel** | ❌ No | ✅ Yes | 🚧 Soon |
| **Status Indicator** | ❌ No | ✅ Yes | 🚧 Soon |
| **DevTools Integration** | ✅ Yes | ✅ Yes | 🚧 Soon |
| **Auto-Update** | ✅ Via Tampermonkey | 🚧 Manual (for now) | 🚧 Manual (for now) |
| **Version** | 3.5 | 4.0.0 | - |

## Common Commands (All Methods)

Once installed (via userscript or extension), all Zen commands work the same:

```bash
# Start the server
zen server start

# Get page information
zen info

# Execute JavaScript
zen eval "document.title"

# Natural language actions
zen do "click login button"

# AI-powered description
zen describe

# Store element from DevTools
# 1. Right-click element → Inspect
# 2. In console: zenStore($0)
# 3. In terminal: zen inspected
```

## Installation Guides

- **Firefox Extension**: [extensions/firefox/README.md](firefox/README.md)
- **Userscript** (Tampermonkey): [See main installation docs](https://roelvangils.github.io/zen-bridge/getting-started/installation/)

## Troubleshooting

### Extension Not Connecting

**Check the browser console** (F12):
- Look for `[Zen Bridge Extension] Loaded` message
- Look for `[Zen Bridge] Connected via WebSocket` message

**Verify server is running**:
```bash
zen server status
```

**Restart server if needed**:
```bash
zen server restart
```

### CSP Issues

If you're using the **userscript** and encountering CSP errors:
- Switch to the **extension** for full CSP bypass
- Read the [CSP Troubleshooting Guide](https://roelvangils.github.io/zen-bridge/troubleshooting/csp-issues/)

### Extension Not Loading

**Reload the extension**:
- Firefox: Go to `about:debugging#/runtime/this-firefox` → Click "Reload"
- Chrome: Go to `chrome://extensions` → Click reload icon

**Check for errors**:
- Firefox: Browser Console (Ctrl+Shift+J)
- Chrome: Extension error console

## Security Notes

**Are extensions safe?**
Yes! Browser extensions from trusted sources are safe. The CSP bypass functionality is:
- ✅ A standard browser extension capability
- ✅ Used by legitimate tools (developer tools, automation, accessibility)
- ✅ Sandboxed by the browser
- ✅ Only works with your local Zen server (localhost:8766)
- ✅ Open source - you can review all code

**Privacy:**
- No data is sent to external servers
- All communication stays between your browser and local CLI
- No tracking or analytics

## Development

### Testing Changes

**Firefox:**
1. Make changes to extension files
2. Go to `about:debugging#/runtime/this-firefox`
3. Click "Reload" next to Zen Browser Bridge
4. Test on a CSP-protected site like GitHub

### Building for Distribution

Coming soon! We'll add build scripts for:
- Creating signed extension packages
- Packaging for browser stores
- Automated releases

## Links

- 📖 [Main Documentation](https://roelvangils.github.io/zen-bridge/)
- 💻 [GitHub Repository](https://github.com/roelvangils/zen-bridge)
- 🐛 [Report Issue](https://github.com/roelvangils/zen-bridge/issues)
- 📚 [API Reference](https://roelvangils.github.io/zen-bridge/api/overview/)
- 🔧 [Troubleshooting](https://roelvangils.github.io/zen-bridge/troubleshooting/csp-issues/)

## Contributing

We welcome contributions! If you'd like to:
- Add support for other browsers (Chrome, Edge, Safari)
- Improve the extension UI
- Fix bugs or add features

Please open an issue or pull request on GitHub.

## License

Part of Zen Browser Bridge - see main repository for license.
