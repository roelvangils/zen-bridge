# Inspekt - Chrome Extension

The Chrome extension for Inspekt that **bypasses CSP restrictions** and works on **all websites** including GitHub, Gmail, banking sites, and more.

## Features

✨ **CSP Bypass** - Works on all websites, no restrictions
🔒 **Explicit Opt-In** - You control which domains Zen can access
🚀 **Automatic Connection** - Connects to localhost:8766 automatically
🛠️ **DevTools Panel** - Custom Inspekt panel with automatic element tracking, element picker, and quick actions
📊 **Status Panel** - Built-in settings panel with connection status and domain management
🔄 **Auto-Reconnect** - Maintains connection across page reloads
⚡ **Manifest V3** - Uses latest Chrome extension architecture

## Installation

### Method 1: Developer Mode (Temporary)

This is the quickest way to test the extension, but you'll need to reload it after browser restarts.

1. **Download the extension**:
   ```bash
   cd /path/to/zen-bridge
   cd extensions/chrome
   ```

2. **Open Chrome Extensions page**:
   - Navigate to `chrome://extensions/`
   - Or click the puzzle icon (⚙️) → **Manage Extensions**

3. **Enable Developer Mode**:
   - Toggle the **"Developer mode"** switch in the top right corner

4. **Load the extension**:
   - Click **"Load unpacked"**
   - Select the `extensions/chrome` directory (the folder containing `manifest.json`)

5. **Verify installation**:
   - Look for the ⚡ **Inspekt** extension in your list
   - Click the puzzle icon and pin it to your toolbar for easy access
   - Click the ⚡ icon to see the status panel

### Method 2: Packaged Extension (.crx or .zip)

For easier distribution and installation:

1. **Build the extension** (see [Building](#building) section below)

2. **Install the packaged extension**:
   - Open `chrome://extensions/`
   - Enable **Developer mode**
   - Drag and drop the `.zip` file onto the page
   - Or use **"Load unpacked"** and select the extracted folder

### Method 3: Chrome Web Store (Coming Soon)

Once published to the Chrome Web Store, you'll be able to install with one click. See [CHROME_WEB_STORE.md](CHROME_WEB_STORE.md) for our publication roadmap.

## Usage

### 1. Start the Zen Server

```bash
inspektserver start
```

### 2. Open Any Website and Allow It

When you first visit a website, you'll see a permission modal:

1. **Navigate to a website** (e.g., github.com, gmail.com)
2. **Permission modal appears** - "Allow CLI control of this website?"
3. **Click "Allow [domain]"** to grant permission for that entire domain
4. **Connection established** - Inspekt is now active on that site

The extension remembers your choice, so you only need to allow each domain once. You can manage allowed domains from the extension popup.

**Security:** You must explicitly allow each domain before Inspekt can control it. This prevents unauthorized access and gives you full control.

### 3. Run Zen Commands

```bash
# Get page info
inspektinfo

# Extract title
inspekteval "document.title"

# Natural language actions
inspektdo "click login button"

# AI-powered description
inspektdescribe

# And any other inspektcommand!
```

### 4. Manage Domains via Status Panel

Click the ⚡ icon in your toolbar to:
- **View connection status** (green = connected, yellow = connecting, red = disconnected)
- **See current domain status** - Allowed or not allowed
- **Allow/remove current domain** - One-click permission management
- **View all allowed domains** - See everywhere Inspekt has access
- **Remove domains** - Revoke access anytime
- **Quick start guide** and common commands

## Advantages Over Userscript

| Feature | Userscript | Extension |
|---------|-----------|-----------|
| **Works on GitHub** | ❌ Blocked by CSP | ✅ Yes |
| **Works on Gmail** | ❌ Blocked by CSP | ✅ Yes |
| **Works on Banking Sites** | ❌ Blocked by CSP | ✅ Yes |
| **Installation** | Easier (one click) | Slightly more steps |
| **Auto-Update** | Via Tampermonkey | Via Chrome Web Store (when published) |
| **Settings Panel** | ❌ No | ✅ Yes |
| **Status Indicator** | ❌ No | ✅ Yes |

**Recommendation**: Use the extension for full compatibility on all websites!

## Security Model

### Explicit Opt-In Per Domain

**You're in control.** Inspekt requires explicit permission before it can access any website:

1. **First Visit** - Permission modal appears
2. **You Decide** - Allow or deny access for that domain
3. **Saved Choice** - Extension remembers your decision
4. **Manage Anytime** - View and revoke permissions from the popup

**Why this matters:**
- Prevents unauthorized access to your sensitive sites
- You choose exactly which domains Zen can control
- Permissions persist across sessions but can be revoked anytime
- Transparent - see all allowed domains in the settings panel

### Localhost-Only Communication

All communication stays between:
- Your browser (extension)
- Your local CLI (localhost:8766)

**No external servers. No tracking. No data collection.**

### How CSP Bypass Works

The extension uses Chrome's `scripting.executeScript()` API (Manifest V3) which has elevated privileges:

1. **Content script** receives execution request from WebSocket
2. **Sends message** to background service worker
3. **Background script** uses `scripting.executeScript()` to bypass CSP
4. **Result** is sent back via WebSocket

This is **safe and intended** - browser extensions can bypass CSP for legitimate purposes like developer tools, automation, and accessibility features.

## DevTools Panel

The extension includes a powerful custom DevTools panel with comprehensive element inspection features:

### Automatic Element Tracking

Elements are automatically stored when you inspect them:

1. **Right-click any element** → Select **"Inspect"**
2. **Element is auto-stored** - No manual command needed!
3. **Run in terminal**: `inspekt inspected`

The panel automatically detects when you select elements in the Elements tab and stores them for CLI access.

### Custom Inspekt Panel Features

Open Chrome DevTools and select the **"Inspekt"** tab to access:

**🔍 Currently Inspected Element**
- Displays the element you last selected
- Shows tag name, ID, classes, selector path
- Displays accessibility info (role, accessible name, ARIA attributes)
- Shows element dimensions and visibility status

**⚡ Quick Actions**
- **Pick Element** (🎯) - Click-to-select elements without leaving the Inspekt tab
- **inspekt inspected** - Copy the `inspekt inspected` command to clipboard
- **Copy Selector** - Copy CSS selector to clipboard
- **Copy Click Command** - Copy `inspekt click "selector"` command
- **Show in Elements** - Jump to element in Elements panel
- **Highlight Element** - Visually highlight the element on the page (scales up with blue glow)

**📜 Recent Elements**
- History of recently inspected elements with timestamps
- Click any element to restore it
- ✨ button to highlight each historical element
- 📍 button to open element in Elements panel

**📚 Quick Reference**
- Essential commands (inspect, inspected, click, type)
- Page analysis commands (index, describe, ask)
- Navigation commands (open, back, forward)

**⚙️ Settings**
- Auto-store inspected elements
- Show console notifications
- Track element history

### Element Picker

The element picker lets you select elements without switching to the Elements tab:

1. Click the **"Pick Element"** button (🎯) in the Inspekt panel
2. Hover over elements on the page - they'll be highlighted with an animated blue border
3. Click the element you want to inspect
4. Element is automatically stored and ready for CLI commands

The picker shows a tooltip with the element's tag and classes as you hover, making it easy to find the right element.

### Visual Element Highlighting

Click the **"Highlight Element"** button (✨) to visually emphasize the currently inspected element:

- Element scales up to 1.3× size with smooth animation
- Blue glow and box shadow applied
- Displays for 5 seconds then smoothly fades out
- Click the button again to dismiss early
- Element inherits its background color for visibility
- Follows the element if you scroll the page

Perfect for verifying you've selected the right element before running CLI commands!

## Building

### Create a ZIP Package

To create a distributable ZIP file:

```bash
cd extensions/chrome
zip -r zen-browser-bridge-chrome-4.0.0.zip . -x "*.git*" "*.DS_Store" "build.sh" "CHROME_WEB_STORE.md"
```

This creates a ZIP file that can be:
- Shared with others for manual installation
- Uploaded to Chrome Web Store for distribution

### Build Script (Coming Soon)

We'll add an automated build script similar to Firefox's:

```bash
./build.sh
```

This will:
- Validate manifest.json
- Create optimized ZIP package
- Generate checksums
- Prepare for Chrome Web Store submission

## Troubleshooting

### Extension Not Connecting

**Check the console** (F12):
- Look for `[Inspekt Extension] Loaded` message
- Look for `[Inspekt] Connected via WebSocket` message

**Verify server is running**:
```bash
inspektserver status
```

**Restart server if needed**:
```bash
inspektserver restart
```

### Extension Not Loading

**Reload extension**:
- Go to `chrome://extensions/`
- Click the refresh icon (↻) on the Inspekt card

**Check for errors**:
- Look in the extension's "Errors" section on `chrome://extensions/`
- Check the background service worker console
- Check the browser console (F12) on any page

### CSP Still Blocking?

If you're still seeing CSP errors:

1. **Verify extension is active**:
   - Go to `chrome://extensions/`
   - Make sure Inspekt is enabled
   - Check that it has all required permissions

2. **Check permissions**:
   - The extension needs `activeTab`, `scripting`, and `<all_urls>` permissions
   - If prompted, click "Allow" for all permissions

3. **Reload the page**:
   - The content script loads when the page loads
   - Try refreshing the page after enabling the extension

### "Service worker (inactive)" Warning

This is normal! Chrome's Manifest V3 service workers sleep when not in use to save resources. They wake up automatically when needed.

### Still Not Working?

1. Check [Troubleshooting Guide](https://roelvangils.github.io/zen-bridge/troubleshooting/csp-issues/)
2. Open an issue: https://github.com/roelvangils/inspekt/issues

## Development

### File Structure

```
chrome/
├── manifest.json          # Extension manifest (Manifest V3)
├── background.js          # Background service worker (CSP bypass)
├── content.js             # Content script (WebSocket)
├── popup/
│   ├── popup.html         # Settings panel
│   ├── popup.css          # Styling
│   └── popup.js           # Panel logic
├── icons/                 # Extension icons
├── README.md              # This file
└── CHROME_WEB_STORE.md    # Web Store submission guide
```

### Testing Changes

1. Make your changes to the extension files
2. Go to `chrome://extensions/`
3. Click the **refresh icon (↻)** next to Inspekt
4. Test on a CSP-protected site like GitHub or Gmail

### Debugging

**Background Service Worker**:
- Go to `chrome://extensions/`
- Click "service worker" link under Inspekt
- This opens DevTools for the background script

**Content Script**:
- Open DevTools on any page (F12)
- Check the Console tab for Inspekt messages

**Popup**:
- Right-click the ⚡ icon → "Inspect popup"
- This opens DevTools for the popup

## Differences from Firefox Extension

The Chrome extension uses **Manifest V3** while Firefox uses Manifest V2:

| Feature | Firefox (Manifest V2) | Chrome (Manifest V3) |
|---------|---------------------|---------------------|
| **Background** | Persistent background page | Service worker (event-driven) |
| **API Namespace** | `browser.*` | `chrome.*` |
| **Script Execution** | `tabs.executeScript()` | `scripting.executeScript()` |
| **Permissions** | Combined in `permissions` | Split into `permissions` and `host_permissions` |

Both versions provide the same functionality and CSP bypass capabilities.

## Version History

### 4.0.0 (Current)
- ✅ Initial Chrome extension release
- ✅ Manifest V3 implementation
- ✅ CSP bypass using scripting.executeScript()
- ✅ Settings panel with status indicator
- ✅ DevTools integration
- ✅ Works on all websites

## FAQ

**Q: Why an extension instead of just a userscript?**
A: Userscripts are blocked by CSP on many important sites (GitHub, Gmail, banking). Extensions have elevated privileges and can bypass CSP.

**Q: Is it safe to bypass CSP?**
A: Yes! Browser extensions are designed to have elevated privileges. CSP restrictions apply to web content, not to trusted browser extensions.

**Q: Why Manifest V3?**
A: Chrome is phasing out Manifest V2 extensions. Manifest V3 is the future-proof standard for Chrome extensions.

**Q: Will this work on Edge, Brave, or other Chromium browsers?**
A: Yes! This extension should work on any Chromium-based browser (Edge, Brave, Opera, Vivaldi, etc.). Just load it in developer mode.

**Q: Can I use both userscript and extension?**
A: It's recommended to use only one at a time to avoid conflicts. The extension is the better choice for compatibility.

**Q: When will it be on Chrome Web Store?**
A: We're preparing for submission! See [CHROME_WEB_STORE.md](CHROME_WEB_STORE.md) for our publication roadmap and how you can help.

## Publishing to Chrome Web Store

See [CHROME_WEB_STORE.md](CHROME_WEB_STORE.md) for detailed instructions on how to publish this extension to the Chrome Web Store.

## License

Part of Inspekt - see main repository for license.

## Links

- 📖 [Documentation](https://roelvangils.github.io/zen-bridge/)
- 💻 [GitHub](https://github.com/roelvangils/inspekt)
- 🐛 [Report Issue](https://github.com/roelvangils/inspekt/issues)
- 🌐 [Chrome Web Store](CHROME_WEB_STORE.md) (Coming Soon)
