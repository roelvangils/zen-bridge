# Zen Browser Bridge - Firefox Extension

The Firefox extension for Zen Browser Bridge that **bypasses CSP restrictions** and works on **all websites** including GitHub, Gmail, banking sites, and more.

## Features

✨ **CSP Bypass** - Works on all websites, no restrictions
🚀 **Automatic Connection** - Connects to localhost:8766 automatically
🛠️ **DevTools Integration** - Use `zenStore($0)` in console
📊 **Status Panel** - Built-in settings panel with connection status
🔄 **Auto-Reconnect** - Maintains connection across page reloads

## Installation

### Method 1: Temporary Installation (Development)

1. **Download the extension**:
   ```bash
   cd /path/to/zen-bridge
   cd extensions/firefox
   ```

2. **Open Firefox**:
   - Navigate to `about:debugging#/runtime/this-firefox`
   - Click **"Load Temporary Add-on..."**
   - Select the `manifest.json` file from the `extensions/firefox` directory

3. **Verify installation**:
   - Look for the ⚡ icon in your toolbar
   - Click it to see the status panel

### Method 2: Permanent Installation (.xpi file)

Coming soon! We'll package this as a signed .xpi file for easier installation.

### Method 3: Firefox Add-ons Store

Coming soon! We plan to submit this to the official Firefox Add-ons store.

## Usage

### 1. Start the Zen Server

```bash
zen server start
```

### 2. Open Any Website

The extension works on **all websites**, including:
- ✅ github.com (CSP bypass!)
- ✅ gmail.com (CSP bypass!)
- ✅ Banking sites (CSP bypass!)
- ✅ Any other website

### 3. Run Zen Commands

```bash
# Get page info
zen info

# Extract title
zen eval "document.title"

# Natural language actions
zen do "click login button"

# AI-powered description
zen describe

# And any other zen command!
```

### 4. Check Status Panel

Click the ⚡ icon in your toolbar to see:
- Connection status
- Quick start guide
- Common commands
- Links to documentation

## Advantages Over Userscript

| Feature | Userscript | Extension |
|---------|-----------|-----------|
| **Works on GitHub** | ❌ Blocked by CSP | ✅ Yes |
| **Works on Gmail** | ❌ Blocked by CSP | ✅ Yes |
| **Works on Banking Sites** | ❌ Blocked by CSP | ✅ Yes |
| **Installation** | Easier (one click) | Slightly more steps |
| **Auto-Update** | Via Tampermonkey | Manual for now |
| **Settings Panel** | ❌ No | ✅ Yes |

**Recommendation**: Use the extension for full compatibility on all websites!

## How CSP Bypass Works

The extension uses Firefox's `tabs.executeScript()` API which has elevated privileges:

1. **Content script** receives execution request from WebSocket
2. **Sends message** to background script
3. **Background script** uses `tabs.executeScript()` to bypass CSP
4. **Result** is sent back via WebSocket

This is **safe and intended** - browser extensions can bypass CSP for legitimate purposes.

## DevTools Integration

The extension includes the same DevTools integration as the userscript:

```javascript
// In browser console:
// 1. Inspect element (Right-click → Inspect)
// 2. Store it:
zenStore($0)

// 3. In terminal:
zen inspected
```

## Troubleshooting

### Extension Not Connecting

**Check the console** (F12):
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

### Extension Not Loading

**Reload extension**:
- Go to `about:debugging#/runtime/this-firefox`
- Click "Reload" next to Zen Browser Bridge

**Check for errors**:
- Look in Browser Console (Ctrl+Shift+J)
- Check for extension errors

### Still Not Working?

1. Check [Troubleshooting Guide](https://roelvangils.github.io/zen-bridge/troubleshooting/csp-issues/)
2. Open an issue: https://github.com/roelvangils/zen-bridge/issues

## Development

### File Structure

```
firefox/
├── manifest.json          # Extension manifest
├── background.js          # Background script (CSP bypass)
├── content.js             # Content script (WebSocket)
├── popup/
│   ├── popup.html         # Settings panel
│   ├── popup.css          # Styling
│   └── popup.js           # Panel logic
├── icons/                 # Extension icons
└── README.md              # This file
```

### Testing Changes

1. Make your changes to the extension files
2. Go to `about:debugging#/runtime/this-firefox`
3. Click **"Reload"** next to Zen Browser Bridge
4. Test on a CSP-protected site like GitHub

### Building for Distribution

Coming soon! We'll add build scripts for:
- Creating signed .xpi files
- Packaging for Firefox Add-ons store
- Automated releases

## Version History

### 4.0.0 (Current)
- ✅ Initial Firefox extension release
- ✅ CSP bypass implementation
- ✅ Settings panel with status indicator
- ✅ DevTools integration
- ✅ Works on all websites

## FAQ

**Q: Why an extension instead of just a userscript?**
A: Userscripts are blocked by CSP on many important sites (GitHub, Gmail, banking). Extensions have elevated privileges and can bypass CSP.

**Q: Is it safe to bypass CSP?**
A: Yes! Browser extensions are designed to have elevated privileges. CSP restrictions apply to web content, not to trusted browser extensions.

**Q: Will this work on Chrome too?**
A: We're building a Chrome version next! The Chrome extension will be in `extensions/chrome/`.

**Q: Can I use both userscript and extension?**
A: It's recommended to use only one at a time to avoid conflicts. The extension is the better choice for compatibility.

## License

Part of Zen Browser Bridge - see main repository for license.

## Links

- 📖 [Documentation](https://roelvangils.github.io/zen-bridge/)
- 💻 [GitHub](https://github.com/roelvangils/zen-bridge)
- 🐛 [Report Issue](https://github.com/roelvangils/zen-bridge/issues)
