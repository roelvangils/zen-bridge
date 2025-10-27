# Zen Bridge Architecture

**Version**: 1.0.0 (current state documented)
**Status**: 📋 Baseline documentation - To be expanded in Phase 1
**Last Updated**: 2025-10-27

---

## Overview

Zen Bridge is a command-line tool that enables execution of JavaScript code in a browser from the terminal. It uses a three-tier architecture with WebSocket-based bidirectional communication.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         USER LAYER                          │
│  ┌──────────────┐         ┌──────────────┐                 │
│  │   Terminal   │         │   Browser    │                 │
│  │   (Shell)    │         │ (Any modern) │                 │
│  └──────┬───────┘         └───────┬──────┘                 │
│         │                         │                         │
└─────────┼─────────────────────────┼─────────────────────────┘
          │                         │
          │ zen CLI                 │ Tampermonkey
          │ commands                │ userscript
          │                         │
┌─────────▼─────────────────────────▼─────────────────────────┐
│                    APPLICATION LAYER                        │
│  ┌──────────────┐         ┌──────────────┐                 │
│  │   CLI App    │         │  Userscript  │                 │
│  │  (Click)     │         │ (WebSocket)  │                 │
│  │  zen/cli.py  │         │  client      │                 │
│  └──────┬───────┘         └───────┬──────┘                 │
│         │                         │                         │
│         │ HTTP POST /run          │ WebSocket connect      │
│         │                         │                         │
└─────────┼─────────────────────────┼─────────────────────────┘
          │                         │
          │                         │
┌─────────▼─────────────────────────▼─────────────────────────┐
│                    COMMUNICATION LAYER                      │
│  ┌──────────────────────────────────────────────────┐      │
│  │         Bridge Server (aiohttp)                  │      │
│  │  ┌────────────────┐    ┌─────────────────────┐  │      │
│  │  │ HTTP Server    │    │ WebSocket Server    │  │      │
│  │  │ :8765          │    │ :8766/ws            │  │      │
│  │  │ (CLI → Server) │    │ (Browser ↔ Server) │  │      │
│  │  └────────────────┘    └─────────────────────┘  │      │
│  │              zen/bridge_ws.py                    │      │
│  └──────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────┘
          │                         │
          │ Request/Response        │ Execute/Result
          │                         │
┌─────────▼─────────────────────────▼─────────────────────────┐
│                       DOMAIN LAYER                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Config     │  │  JavaScript  │  │    Client    │     │
│  │  Management  │  │   Scripts    │  │   Wrapper    │     │
│  │ zen/config   │  │ zen/scripts/ │  │ zen/client   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

---

## Communication Flow

### 1. Command Execution Flow

```
User executes: zen eval "document.title"

┌──────────┐  ┌────────────┐  ┌──────────┐  ┌──────────────┐
│ Terminal │  │ CLI (sync) │  │  Server  │  │ Browser (WS) │
└────┬─────┘  └─────┬──────┘  └────┬─────┘  └──────┬───────┘
     │              │              │                │
     │ zen eval     │              │                │
     ├─────────────>│              │                │
     │              │ POST /run    │                │
     │              ├─────────────>│                │
     │              │              │ WS: execute    │
     │              │              ├───────────────>│
     │              │              │                │ eval()
     │              │              │                ├──┐
     │              │              │                │<─┘
     │              │              │ WS: result     │
     │              │              │<───────────────┤
     │              │ GET /result  │                │
     │              ├─────────────>│                │
     │              │<─────────────┤                │
     │ Output       │              │                │
     │<─────────────┤              │                │
     │              │              │                │
```

### 2. WebSocket Connection Lifecycle

```
Page Load → Connect → Ready → Execute → Result → (Repeat)
                ↓                              ↓
            Subscribe                       Disconnect
                                               ↓
                                       Auto-Reconnect (3s)
```

---

## Module Dependency Graph (Current State)

```
┌─────────────────────────────────────────────────────────────┐
│                         zen/cli.py                          │
│                      (3,946 lines)                          │
│  - All CLI commands (33+)                                   │
│  - Command parsing, argument validation                     │
│  - Output formatting, error handling                        │
│  - Script loading and execution                             │
└───┬─────────────────────┬──────────────────────┬────────────┘
    │                     │                      │
    │ imports             │ imports              │ imports
    ▼                     ▼                      ▼
┌──────────┐       ┌─────────────┐       ┌──────────────┐
│  client  │       │   config    │       │  bridge_ws   │
│   (250)  │       │    (213)    │       │    (396)     │
│          │       │             │       │              │
│ HTTP     │       │ Load/merge  │       │ WebSocket    │
│ wrapper  │       │ JSON config │       │ server       │
└────┬─────┘       └──────┬──────┘       └──────┬───────┘
     │                    │                     │
     │ uses               │ uses                │ uses
     ▼                    ▼                     ▼
┌──────────────────────────────────────────────────────────┐
│               Standard Library + Dependencies            │
│  - click (CLI framework)                                 │
│  - requests (HTTP client)                                │
│  - aiohttp (async WebSocket server)                      │
│  - json, pathlib, time, etc.                             │
└──────────────────────────────────────────────────────────┘

Legend:
  (NNN) = Lines of code
  No circular dependencies detected ✅
```

---

## Data Flow

### Request-Response Pattern

```
1. CLI Command
   ↓
2. BridgeClient.execute(code)
   ↓
3. POST http://127.0.0.1:8765/run
   Body: {"code": "document.title"}
   ↓
4. Server creates request_id (UUID)
   Stores in pending_requests{}
   ↓
5. Server broadcasts via WebSocket
   Message: {"type": "execute", "request_id": "...", "code": "..."}
   ↓
6. Browser receives message
   ↓
7. Browser evaluates code
   result = eval(code)
   ↓
8. Browser sends result via WebSocket
   Message: {"type": "result", "request_id": "...", "ok": true, "result": "..."}
   ↓
9. Server receives result
   Moves from pending_requests{} to completed_requests{}
   ↓
10. CLI polls GET http://127.0.0.1:8765/result?request_id=...
    (Exponential backoff: 100ms → 1s)
    ↓
11. Server returns completed result
    ↓
12. CLI formats and displays output
```

### Async Patterns (Server)

```python
# bridge_ws.py uses asyncio event loop

async def main():
    app = web.Application()
    # Add routes
    runner = web.AppRunner(app)
    await runner.setup()
    await http_site.start()
    await ws_site.start()
    await asyncio.Event().wait()  # Run forever

# WebSocket handler
async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    active_connections.add(ws)

    async for msg in ws:
        # Process messages
        await ws.send_str(response)

# HTTP handlers
async def handle_http_run(request):
    data = await request.json()
    request_id = await send_code_to_browser(code)
    return web.json_response({"ok": True, "request_id": request_id})
```

---

## Import Layer Architecture (Current State)

Currently, the project has a flat structure with no enforced layers:

```
zen/
  ├── cli.py          - Imports: client, config, bridge_ws (indirectly)
  ├── client.py       - Imports: requests, pathlib
  ├── config.py       - Imports: json, pathlib
  └── bridge_ws.py    - Imports: aiohttp, asyncio, pathlib
```

**Current State**: ✅ No circular imports, but no enforced boundaries

**Target State (Post-Refactor)**:
```
Layer 3: Application (zen/app/)
  ├─ cli/          - CLI commands
  └─ server.py     - WebSocket server

Layer 2: Services (zen/services/)
  ├─ script_loader.py
  ├─ bridge_executor.py
  └─ control_manager.py

Layer 1: Adapters (zen/adapters/)
  ├─ filesystem.py
  ├─ websocket.py
  └─ http.py

Layer 0: Domain (zen/domain/)
  ├─ models.py       - Pydantic models
  └─ validation.py   - Pure functions

Rule: Layer N can import Layer N-1, N-2, etc., but NOT Layer N+1
```

---

## JavaScript Scripts Organization

Located in `zen/scripts/`:

### Categories

**Data Extraction** (8 scripts):
- `extract_links.js` - Extract all links from page
- `extract_article.js` - Extract article content (Readability)
- `extract_metadata.js` - Extract meta tags, OpenGraph
- `extract_page_structure.js` - Extract headings, landmarks
- `extract_outline.js` - Extract document outline
- `extract_table.js` - Extract table data
- `extract_images.js` - Extract all images
- `find_downloads.js` - Find downloadable files

**Interaction** (5 scripts):
- `click_element.js` - Click elements by selector
- `send_keys.js` - Type text into inputs
- `wait_for.js` - Wait for elements/conditions
- `screenshot_element.js` - Capture element screenshots
- `get_selection.js` - Get selected text

**Control Mode** (1 script):
- `control.js` (799 lines) - Virtual focus keyboard navigation

**Inspection** (3 scripts):
- `get_inspected.js` - Get element details
- `extended_info.js` - Extended page information
- `performance_metrics.js` - Performance data

**Utilities** (4 scripts):
- `cookies.js` - Manage cookies
- `highlight_selector.js` - Highlight elements
- `inject_jquery.js` - Inject jQuery if needed

**Monitoring** (2 scripts):
- `watch_keyboard.js` - Monitor keyboard events
- `watch_all.js` - Monitor DOM/network events

### Script Loading Pattern

```python
# Current pattern in cli.py (repeated 27+ times)
script_path = Path(__file__).parent / "scripts" / "script_name.js"
with open(script_path) as f:
    script_code = f.read()

# Some scripts use template placeholders
script_code = script_code.replace('ACTION_PLACEHOLDER', action)
script_code = script_code.replace('CONFIG_PLACEHOLDER', json.dumps(config))

# Execute
result = client.execute(script_code, timeout=timeout)
```

**Issue**: Repeated file I/O, no caching (except control.js in server)
**Solution (Phase 2)**: ScriptLoader service with caching

---

## Configuration Management

### Configuration Sources (Priority Order)

1. **CLI flags** (highest priority)
   - `--language`, `--debug`, `--timeout`, etc.

2. **Local config** (`./config.json`)
   - Project-specific settings

3. **User config** (`~/.zen/config.json`)
   - User-wide defaults

4. **Default config** (`zen/config.py:DEFAULT_CONFIG`)
   - Hardcoded defaults

### Configuration Schema

```python
{
    "ai-language": "auto" | "en" | "nl" | "fr" | ...,
    "control": {
        "auto-refocus": "only-spa" | "always" | "never",
        "focus-outline": "custom" | "original" | "none",
        "speak-name": bool,
        "speak-all": bool,
        "announce-role": bool,
        "announce-on-page-load": bool,
        "navigation-wrap": bool,
        "scroll-on-focus": bool,
        "click-delay": int (ms),
        "focus-color": string (CSS color),
        "focus-size": int (pixels),
        "focus-animation": bool,
        "focus-glow": bool,
        "sound-on-focus": "none" | "beep" | "click" | "subtle",
        "selector-strategy": "id-first" | "aria-first" | "css-first",
        "refocus-timeout": int (ms),
        "verbose": bool,
        "verbose-logging": bool
    }
}
```

**Current Validation**: Manual in `validate_control_config()`
**Target (Phase 1)**: Pydantic model with automatic validation

---

## Extension Points

### Adding a New CLI Command (Current)

```python
# In zen/cli.py (add to end of file)

@cli.command()
@click.argument("arg")
@click.option("--flag", is_flag=True)
def my_command(arg, flag):
    """My new command."""
    client = BridgeClient()

    # Load script
    script_path = Path(__file__).parent / "scripts" / "my_script.js"
    with open(script_path) as f:
        code = f.read()

    # Execute
    result = client.execute(code, timeout=10.0)

    # Format output
    output = format_output(result)
    click.echo(output)
```

### Adding a New JavaScript Script

```javascript
// zen/scripts/my_script.js

(function() {
    // Your code here
    const result = doSomething();

    // Return result (will be JSON.stringify'd)
    return result;
})();
```

---

## Security Model

### Threat Model

**Assumptions**:
- User trusts their local system
- User trusts the websites they visit
- Server runs on localhost only (127.0.0.1)
- No remote access required

**Security Properties**:
- ✅ Server binds to 127.0.0.1 (not 0.0.0.0)
- ✅ No authentication needed (localhost-only)
- ✅ Arbitrary JS execution is intentional (tool purpose)
- ⚠️  No origin validation on WebSocket (relies on same-machine)
- ⚠️  No rate limiting (not needed for local use)

**Out of Scope**:
- Remote access (use SSH tunnel if needed)
- Multi-user environments (each user runs own server)
- Sandboxing (user must trust scripts they run)

### Future Enhancements (Optional)

- Token-based authentication for remote binding
- Origin validation for WebSocket connections
- Script signing/verification for untrusted scripts

---

## Performance Characteristics

### Latency

**Round-trip time** (CLI → Server → Browser → Server → CLI):
- Typical: 50-200ms (local WebSocket)
- Depends on: JavaScript execution time, network latency (negligible on localhost)

### Throughput

**Current** (not benchmarked):
- Estimated: 10-50 requests/second
- Bottleneck: Single-threaded async event loop (aiohttp)

**Potential Improvements** (Phase 2+):
- Async file I/O (remove blocking calls)
- Connection pooling (multiple browser tabs)
- Request batching (if needed)

### Resource Usage

- **Memory**: Minimal (~10-50 MB for server)
- **CPU**: Low (event-driven, mostly idle)
- **Network**: Localhost only (negligible)

---

## Known Limitations

1. **Single Browser Tab**
   - Only one active browser tab receives commands
   - Mitigation: Use `document.visibilityState` check

2. **Page Navigation**
   - WebSocket disconnects on navigation
   - Mitigation: Auto-reconnect, resend pending requests

3. **Tampermonkey Required**
   - Users must install browser extension
   - Alternative: Browser extension (future work)

4. **JavaScript Execution Context**
   - Runs in page context (not extension context)
   - Can't access extension APIs (tabs, bookmarks, etc.)

---

## Future Architecture (Post-Refactor)

See REFACTOR_PLAN.md for detailed migration plan.

**Key Changes**:
- Split cli.py into command groups (~300 lines each)
- Extract services (ScriptLoader, BridgeExecutor, etc.)
- Add adapters layer (Filesystem, WebSocket, HTTP)
- Enforce import layer architecture
- Add comprehensive typing (Pydantic models)
- Async file I/O (aiofiles)

---

## References

- REFACTOR_PLAN.md - Detailed refactoring plan
- PROTOCOL.md - WebSocket protocol specification
- CONTRIBUTING.md - Developer guide
- SUMMARY.md - Project overview and status

---

**Document Status**: 📋 Baseline (current state documented)
**Next Update**: After Phase 1 (add Pydantic models, detailed protocol)
**Maintainer**: Roel van Gils
**Last Updated**: 2025-10-27
