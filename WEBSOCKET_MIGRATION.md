# WebSocket Migration Guide

## Why WebSockets?

The new WebSocket implementation offers significant advantages:

- ⚡ **Instant execution** - No 300ms polling delay
- 💪 **More efficient** - No constant HTTP requests
- 🔄 **Bidirectional** - Server can push to browser instantly
- 📉 **Lower CPU usage** - Browser doesn't poll every 300ms
- 🔗 **Always connected** - Persistent connection with auto-reconnect

## Migration Steps

### 1. Install New Dependencies

```bash
pip install websockets aiohttp
```

Or from requirements.txt:
```bash
pip install -r requirements.txt
```

### 2. Use the New Server

**Option A: Replace old server**

Stop the old server and start the new one:
```bash
# Stop old server (if running in background)
pkill -f zen.bridge

# Start new WebSocket server
python zen/bridge_ws.py
```

**Option B: Run alongside (different ports)**

The WebSocket server uses:
- Port 8765: HTTP API (CLI communication)
- Port 8766: WebSocket (browser communication)

```bash
# Start WebSocket server
python zen/bridge_ws.py
```

### 3. Update the Userscript

Replace your existing userscript with the WebSocket version:

1. Open your userscript manager (Violentmonkey/Tampermonkey)
2. Find "Zen Browser Bridge" userscript
3. Replace content with `userscript_ws.js`
4. Save and reload browser tab

### 4. Verify Connection

Open browser console and look for:
```
[Zen Bridge] Connected via WebSocket
```

### 5. Test

```bash
# Make sure server is running
python zen/bridge_ws.py

# In another terminal, test:
zen eval "document.title"
```

Should be instant! ⚡

## Features

### Auto-Reconnect

The userscript automatically reconnects if connection is lost:
- Reconnects every 3 seconds after disconnect
- Shows connection status in console
- Works seamlessly when switching tabs

### Keepalive

Connection stays alive with ping/pong every 30 seconds.

### Visibility Detection

Only the active (visible) tab executes code. Inactive tabs ignore messages.

## Comparison: Before vs After

### Old (HTTP Polling)

```
Timeline:
0ms   - CLI sends code
0ms   - Code stored in server
300ms - Browser polls (nothing)
600ms - Browser polls (gets code!)
601ms - Browser executes
602ms - Browser sends result
602ms - CLI polls for result
605ms - CLI gets result

Total: ~605ms
```

### New (WebSockets)

```
Timeline:
0ms - CLI sends code
0ms - Server pushes to browser
1ms - Browser receives & executes
2ms - Browser sends result
2ms - CLI gets result

Total: ~2ms
```

**~300x faster!** 🚀

## Troubleshooting

### "WebSocket connection failed"

1. **Check if server is running**:
   ```bash
   lsof -i :8766
   ```

2. **Check firewall**: Make sure port 8766 is not blocked

3. **Check console**: Open browser console for error details

### "No response from browser"

1. **Check userscript is active**: Look for connection message in console
2. **Reload page**: Sometimes helps after userscript update
3. **Check tab is visible**: Only visible tabs execute code

### Old server still running

```bash
# Stop old HTTP server
pkill -f km_js_bridge
pkill -f zen.bridge

# Or find process
lsof -i :8765
kill <PID>
```

## Architecture

```
┌─────────┐                    ┌────────────┐                    ┌─────────────┐
│   CLI   │──HTTP (8765)──────>│   Bridge   │<──WebSocket────────│   Browser   │
│         │<───────────────────│   Server   │      (8766)────────>│ (Userscript)│
└─────────┘                    └────────────┘                    └─────────────┘
```

**HTTP (Port 8765)**: CLI communicates with server (backward compatible)

**WebSocket (Port 8766)**: Browser maintains persistent connection

## Backward Compatibility

The old HTTP polling still works! You can use:
- Old userscript (`userscript.js`) with old server (`zen/bridge.py`)
- New userscript (`userscript_ws.js`) with new server (`zen/bridge_ws.py`)

But not mixed (old userscript with new server won't work).

## Future Plans

- Make WebSocket server the default
- Add `zen server start --websocket` option
- Deprecate HTTP polling eventually

## Questions?

Open an issue on GitHub: https://github.com/roelvangils/zen-bridge
