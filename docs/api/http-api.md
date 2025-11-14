# HTTP API Guide

Inspekt includes a comprehensive REST API that exposes all CLI commands as HTTP endpoints. This allows you to control the browser from any HTTP client, integrate with web applications, or build custom automation workflows.

## Quick Start

```bash
# Start the API server
uvicorn zen.app.api.server:app --host 127.0.0.1 --port 8000

# Check if it's running
curl http://localhost:8000/health

# View interactive documentation
open http://localhost:8000/docs
```

## Understanding the Components

The HTTP API is built with several modern technologies working together. Here's what each one does:

### 🦄 Uvicorn - The Web Server

**What it is**: A lightning-fast ASGI (Asynchronous Server Gateway Interface) web server for Python.

**Why we use it**: FastAPI applications need a server to actually run and listen for HTTP requests. Uvicorn is the most popular choice because it's:

- **Fast** - Built on `uvloop` and `httptools` for maximum performance
- **Async-native** - Handles many concurrent requests efficiently
- **Production-ready** - Used by major companies in production

**Think of it like**:

- FastAPI = Your application code (the "what")
- Uvicorn = The server that runs it (the "how")

**Command breakdown**:

```bash
uvicorn zen.app.api.server:app --host 127.0.0.1 --port 8000
#        └─module─────┘ └─app─┘   └─bind address┘   └─port┘
```

**Useful options**:

```bash
# Auto-reload on code changes (development)
uvicorn zen.app.api.server:app --reload

# Run on all network interfaces (accessible from other machines)
uvicorn zen.app.api.server:app --host 0.0.0.0 --port 8000

# Run in background
uvicorn zen.app.api.server:app --host 127.0.0.1 --port 8000 &

# Multiple workers (production)
uvicorn zen.app.api.server:app --workers 4
```

---

### 📖 Swagger UI - Interactive API Testing

**What it is**: An interactive web-based interface for exploring and testing your API.

**Access it at**: http://localhost:8000/docs

**Why it's useful**: You get a beautiful interface where you can:

- ✅ See all your API endpoints organized by category
- ✅ Read documentation for each endpoint
- ✅ **Try out requests** directly in the browser (no curl needed!)
- ✅ See request/response examples with syntax highlighting
- ✅ Test with different parameters interactively

**Example workflow**:

1. Open http://localhost:8000/docs
2. Find the endpoint you want to test (e.g., `/api/execution/eval`)
3. Click to expand it
4. Click **"Try it out"** button
5. Fill in the parameters (e.g., `{"code": "document.title"}`)
6. Click **"Execute"**
7. See the response immediately!

**Screenshot-like description**:

```
┌─────────────────────────────────────────────────┐
│ Inspekt API                    v1.0.0           │
├─────────────────────────────────────────────────┤
│                                                 │
│ ▼ Navigation                                    │
│   POST /api/navigation/open            [Try it]│
│        Navigate to a URL                        │
│   POST /api/navigation/back            [Try it]│
│        Go back in history                       │
│                                                 │
│ ▼ Execution                                     │
│   POST /api/execution/eval             [Try it]│
│        Execute JavaScript code                  │
│                                                 │
│ ▼ Extraction                                    │
│   GET /api/extraction/info             [Try it]│
│        Get page information                     │
└─────────────────────────────────────────────────┘
```

**Best for**: Development, testing, demos, API exploration

---

### 📚 ReDoc - Beautiful API Documentation

**What it is**: A clean, modern documentation interface focused on **reading** rather than testing.

**Access it at**: http://localhost:8000/redoc

**Why it's different from Swagger UI**:

| Feature | Swagger UI | ReDoc |
|---------|------------|-------|
| Interactive testing | ✅ Yes | ❌ No |
| Design | Functional | 🎨 Beautiful |
| Print-friendly | ❌ No | ✅ Yes (PDF export) |
| Navigation | Dropdown menus | Scrollable sidebar |
| Best for | Testing | Documentation |

**Features**:

- **Three-column layout** - Navigation, content, examples
- **Better for complex APIs** - Shows nested data structures beautifully
- **Search functionality** - Find endpoints quickly
- **Code samples** - Shows request/response examples in multiple languages
- **Dark mode support** - Easy on the eyes

**Example view**:

```
┌──────────────┬─────────────────────┬─────────────────┐
│ Sidebar      │ Documentation       │ Examples        │
├──────────────┼─────────────────────┼─────────────────┤
│ Introduction │ POST /navigation/   │ Request:        │
│              │ open                │ {               │
│ Navigation   │                     │   "url": "...", │
│  - open      │ Navigate to a URL   │   "wait": true  │
│  - back      │                     │ }               │
│  - forward   │ Parameters:         │                 │
│              │ • url (required)    │ Response:       │
│ Execution    │ • wait (optional)   │ {               │
│  - eval      │ • timeout           │   "ok": true,   │
│              │                     │   ...           │
│ Extraction   │ Returns:            │ }               │
│  - info      │ CommandResponse     │                 │
│  - links     │                     │                 │
└──────────────┴─────────────────────┴─────────────────┘
```

**Best for**: Sharing API docs with users, creating reference documentation, presentations

---

### 🤖 OpenAPI Specification (not OpenAI!)

!!! warning "Important Distinction"
    This is **OpenAPI** (API specification format), not **OpenAI** (the company that makes ChatGPT/GPT-4). They are completely different things!

**What it is**: A **specification format** - a standardized way to describe REST APIs in JSON or YAML.

**Access it at**: http://localhost:8000/openapi.json

**Why it matters**:

- 📋 **Industry standard** - Recognized by thousands of tools worldwide
- 🤖 **Machine-readable** - Tools can auto-generate code from it
- 🔄 **Language-agnostic** - Works with any programming language
- 📝 **Self-documenting** - Your API documents itself

**Example snippet**:

```json
{
  "openapi": "3.1.0",
  "info": {
    "title": "Inspekt API",
    "version": "1.0.0",
    "description": "HTTP API for browser automation"
  },
  "paths": {
    "/api/navigation/open": {
      "post": {
        "summary": "Navigate to a URL",
        "tags": ["Navigation"],
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "properties": {
                  "url": {"type": "string"},
                  "wait": {"type": "boolean"},
                  "timeout": {"type": "integer"}
                }
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {"$ref": "#/components/schemas/CommandResponse"}
              }
            }
          }
        }
      }
    }
  }
}
```

**What you can do with it**:

1. **Auto-generate client libraries**:
   ```bash
   # Generate Python client
   openapi-generator-cli generate -i openapi.json -g python -o client/

   # Generate JavaScript client
   openapi-generator-cli generate -i openapi.json -g javascript -o client/
   ```

2. **Import into API testing tools**:
   - Postman: Import → Link → Paste OpenAPI URL
   - Insomnia: Import → From URL → Paste OpenAPI URL
   - HTTPie: `http --print=HhBb $(< openapi.json)`

3. **Validate your API**:
   ```bash
   # Check if API matches the spec
   openapi-validator validate openapi.json
   ```

4. **Generate mock servers**:
   ```bash
   # Create a mock API for testing
   prism mock openapi.json
   ```

**Real-world examples**: Major APIs publish OpenAPI specs:

- [Stripe API](https://github.com/stripe/openapi)
- [GitHub API](https://github.com/github/rest-api-description)
- [Twilio API](https://www.twilio.com/docs/openapi)

---

## How They Work Together

Here's the complete flow:

```
┌─────────────────────────────────────────────────────┐
│ 1. You write FastAPI code with type hints           │
│    @router.post("/eval")                            │
│    async def eval(request: EvalRequest):            │
│        # code                                       │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│ 2. FastAPI auto-generates OpenAPI specification    │
│    (openapi.json) from your code                   │
└──────────────────┬──────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
┌───────────────┐    ┌────────────────┐
│ 3. Swagger UI │    │ 3. ReDoc reads │
│    reads spec │    │    spec →      │
│    → Testing  │    │    Beautiful   │
│    interface  │    │    docs        │
└───────────────┘    └────────────────┘
        │                     │
        └──────────┬──────────┘
                   ▼
┌─────────────────────────────────────────────────────┐
│ 4. Uvicorn serves everything on localhost:8000     │
│    - API endpoints                                  │
│    - Swagger UI at /docs                           │
│    - ReDoc at /redoc                               │
│    - OpenAPI spec at /openapi.json                 │
└─────────────────────────────────────────────────────┘
```

**The magic**: You write code once, get all of this for free:

- ✅ API server (Uvicorn)
- ✅ Interactive testing (Swagger UI)
- ✅ Beautiful docs (ReDoc)
- ✅ Machine-readable spec (OpenAPI)
- ✅ Request validation (Pydantic)
- ✅ Auto-complete in IDEs

---

## Available Endpoints

### Navigation (`/api/navigation/`)

Control browser navigation and scrolling.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/open` | POST | Navigate to a URL |
| `/back` | POST | Go back in history |
| `/forward` | POST | Go forward in history |
| `/reload` | POST | Reload current page |
| `/pageup` | POST | Scroll up one page |
| `/pagedown` | POST | Scroll down one page |
| `/top` | POST | Scroll to top of page |
| `/bottom` | POST | Scroll to bottom of page |

**Example: Navigate to URL**

```bash
curl -X POST http://localhost:8000/api/navigation/open \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "wait": true,
    "timeout": 30
  }'
```

**Response**:
```json
{
  "ok": true,
  "result": {
    "ok": true,
    "url": "https://example.com"
  },
  "error": null,
  "url": "https://example.com",
  "title": "Example Domain"
}
```

---

### Execution (`/api/execution/`)

Execute arbitrary JavaScript code in the browser.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/eval` | POST | Execute JavaScript code |

**Example: Execute JavaScript**

```bash
curl -X POST http://localhost:8000/api/execution/eval \
  -H "Content-Type: application/json" \
  -d '{
    "code": "document.querySelector(\"h1\").textContent",
    "timeout": 5.0
  }'
```

**Response**:
```json
{
  "ok": true,
  "result": "Example Domain",
  "error": null,
  "url": "https://example.com",
  "title": "Example Domain"
}
```

**Complex example**:
```bash
curl -X POST http://localhost:8000/api/execution/eval \
  -H "Content-Type: application/json" \
  -d '{
    "code": "Array.from(document.querySelectorAll(\"a\")).length"
  }'
```

---

### Extraction (`/api/extraction/`)

Extract data from the current page.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/info` | GET | Get page information |
| `/links` | GET | Extract all links |

**Example: Get page info**

```bash
curl http://localhost:8000/api/extraction/info
```

**Response**:
```json
{
  "ok": true,
  "result": {
    "url": "https://example.com",
    "title": "Example Domain",
    "domain": "example.com",
    "protocol": "https:",
    "readyState": "complete",
    "width": 1280,
    "height": 720
  },
  "error": null,
  "url": "https://example.com",
  "title": "Example Domain"
}
```

**Example: Extract links**

```bash
# Get all links with text
curl "http://localhost:8000/api/extraction/links?include_text=true"

# Get just URLs
curl "http://localhost:8000/api/extraction/links?include_text=false"
```

---

### Interaction (`/api/interaction/`)

Interact with page elements - click, type, paste, and wait.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/click` | POST | Click on an element |
| `/double-click` | POST | Double-click on an element |
| `/right-click` | POST | Right-click (context menu) on an element |
| `/type` | POST | Type text character by character |
| `/paste` | POST | Paste text instantly |
| `/wait` | POST | Wait for an element or condition |

**Example: Click an element**

```bash
curl -X POST http://localhost:8000/api/interaction/click \
  -H "Content-Type: application/json" \
  -d '{
    "selector": "button#submit"
  }'
```

**Example: Type text with human-like speed**

```bash
curl -X POST http://localhost:8000/api/interaction/type \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, World!",
    "selector": "input[name=\"search\"]",
    "speed": 0,
    "clear": true
  }'
```

**Example: Wait for element to appear**

```bash
curl -X POST http://localhost:8000/api/interaction/wait \
  -H "Content-Type: application/json" \
  -d '{
    "selector": ".modal",
    "wait_type": "visible",
    "timeout": 10
  }'
```

---

### Inspection (`/api/inspection/`)

Inspect elements and capture screenshots.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/inspect` | POST | Select and inspect an element |
| `/inspected` | GET | Get details of inspected element |
| `/screenshot` | POST | Capture screenshot of an element |

**Example: Inspect an element**

```bash
curl -X POST http://localhost:8000/api/inspection/inspect \
  -H "Content-Type: application/json" \
  -d '{
    "selector": "h1"
  }'
```

**Response**:
```json
{
  "ok": true,
  "result": {
    "tag": "h1",
    "selector": "body > h1",
    "textContent": "Example Domain",
    "dimensions": {
      "width": 200,
      "height": 50,
      "top": 100,
      "left": 50
    },
    "visible": true
  }
}
```

**Example: Screenshot an element**

```bash
curl -X POST http://localhost:8000/api/inspection/screenshot \
  -H "Content-Type: application/json" \
  -d '{
    "selector": "#main-content"
  }'
```

**Response** (includes base64-encoded PNG):
```json
{
  "ok": true,
  "result": {
    "dataUrl": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUg...",
    "width": 800,
    "height": 600
  }
}
```

---

### Selection (`/api/selection/`)

Get text selection from the browser in multiple formats.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Get selection in all formats (text, HTML, markdown) |
| `/text` | GET | Get selected text (plain text) |
| `/html` | GET | Get selected HTML |
| `/markdown` | GET | Get selected text as Markdown |

**Example: Get all selection formats**

```bash
curl http://localhost:8000/api/selection
```

**Response**:
```json
{
  "ok": true,
  "result": {
    "hasSelection": true,
    "text": "Example text",
    "html": "<strong>Example text</strong>",
    "markdown": "**Example text**",
    "length": 12,
    "position": {"x": 100, "y": 200, "width": 80, "height": 20},
    "container": {"tag": "p", "id": "content"}
  }
}
```

**Example: Get just plain text**

```bash
curl http://localhost:8000/api/selection/text
```

---

### Cookies (`/api/cookies/`)

Manage browser cookies.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | List all cookies |
| `/{name}` | GET | Get a specific cookie |
| `/` | POST | Set a cookie |
| `/{name}` | DELETE | Delete a specific cookie |
| `/` | DELETE | Clear all cookies |

**Example: List all cookies**

```bash
curl http://localhost:8000/api/cookies
```

**Response**:
```json
{
  "ok": true,
  "result": {
    "cookies": {
      "session_id": "abc123",
      "user_pref": "dark"
    },
    "count": 2
  }
}
```

**Example: Set a cookie**

```bash
curl -X POST http://localhost:8000/api/cookies \
  -H "Content-Type: application/json" \
  -d '{
    "name": "token",
    "value": "xyz789",
    "max_age": 3600,
    "path": "/",
    "secure": true
  }'
```

**Example: Delete a cookie**

```bash
curl -X DELETE http://localhost:8000/api/cookies/session_id
```

**Example: Clear all cookies**

```bash
curl -X DELETE http://localhost:8000/api/cookies
```

---

## Response Format

All API endpoints return JSON in a consistent format:

### Success Response

```json
{
  "ok": true,
  "result": <command-specific-data>,
  "error": null,
  "url": "https://current-page.com",
  "title": "Current Page Title"
}
```

### Error Response

```json
{
  "ok": false,
  "result": null,
  "error": "Error message describing what went wrong",
  "url": null,
  "title": null
}
```

---

## HTTP Status Codes

The API uses standard HTTP status codes:

| Code | Meaning | When it happens |
|------|---------|----------------|
| `200 OK` | Success | Command executed successfully |
| `400 Bad Request` | Invalid input | Missing required parameters, invalid types |
| `404 Not Found` | Unknown endpoint | Endpoint doesn't exist |
| `500 Internal Server Error` | Execution failed | JavaScript error, command failure |
| `503 Service Unavailable` | Bridge unavailable | Bridge server not running |
| `504 Gateway Timeout` | Timeout | Command took too long to execute |

**Example error response (bridge not running)**:

```bash
curl http://localhost:8000/api/extraction/info
```

```json
{
  "ok": false,
  "error": "Bridge server is not running. Start it with: zen server start",
  "detail": "Is the bridge server running? Start it with: zen server start"
}
```

---

## Practical Examples

### 1. Browser Automation Workflow

```bash
# 1. Check if everything is running
curl http://localhost:8000/health

# 2. Navigate to a page
curl -X POST http://localhost:8000/api/navigation/open \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "wait": true}'

# 3. Get page information
curl http://localhost:8000/api/extraction/info | jq

# 4. Extract all links
curl http://localhost:8000/api/extraction/links | jq

# 5. Execute custom JavaScript
curl -X POST http://localhost:8000/api/execution/eval \
  -H "Content-Type: application/json" \
  -d '{"code": "document.querySelectorAll(\"p\").length"}'

# 6. Scroll down
curl -X POST http://localhost:8000/api/navigation/pagedown

# 7. Go back
curl -X POST http://localhost:8000/api/navigation/back
```

### 2. Integration with Python

```python
import requests

API_BASE = "http://localhost:8000"

# Navigate to a page
response = requests.post(
    f"{API_BASE}/api/navigation/open",
    json={"url": "https://example.com", "wait": True}
)
print(response.json())

# Get page title
response = requests.post(
    f"{API_BASE}/api/execution/eval",
    json={"code": "document.title"}
)
print(response.json()["result"])

# Extract all links
response = requests.get(f"{API_BASE}/api/extraction/links")
links = response.json()["result"]
print(f"Found {len(links)} links")
```

### 3. Integration with JavaScript/Node.js

```javascript
const API_BASE = 'http://localhost:8000';

// Navigate to a page
const response = await fetch(`${API_BASE}/api/navigation/open`, {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    url: 'https://example.com',
    wait: true
  })
});

const data = await response.json();
console.log(data);

// Execute JavaScript
const evalResponse = await fetch(`${API_BASE}/api/execution/eval`, {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    code: 'document.querySelectorAll("a").length'
  })
});

const evalData = await evalResponse.json();
console.log(`Found ${evalData.result} links`);
```

### 4. Testing with HTTPie

```bash
# HTTPie provides a cleaner syntax than curl

# Get page info
http GET localhost:8000/api/extraction/info

# Execute JavaScript
http POST localhost:8000/api/execution/eval \
  code='document.title' \
  timeout:=5.0

# Navigate
http POST localhost:8000/api/navigation/open \
  url='https://example.com' \
  wait:=true \
  timeout:=30
```

---

## Development Tips

### Auto-reload During Development

Use the `--reload` flag to automatically restart the server when code changes:

```bash
uvicorn zen.app.api.server:app --host 127.0.0.1 --port 8000 --reload
```

Now every time you edit `/zen/app/api/server.py` or any router file, the server restarts automatically!

### Enable Debug Logging

```bash
uvicorn zen.app.api.server:app --log-level debug
```

### Custom Port

```bash
uvicorn zen.app.api.server:app --port 8888
```

### Run in Background

```bash
# Start in background
uvicorn zen.app.api.server:app --host 127.0.0.1 --port 8000 &

# Save the process ID
echo $! > /tmp/zen-api.pid

# Stop later
kill $(cat /tmp/zen-api.pid)
```

---

## Production Deployment

For production use, consider:

### 1. Multiple Workers

```bash
uvicorn zen.app.api.server:app --workers 4 --host 0.0.0.0 --port 8000
```

### 2. Behind a Reverse Proxy

Use Nginx or Traefik to add HTTPS:

```nginx
server {
    listen 443 ssl;
    server_name api.example.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 3. Process Manager

Use systemd or supervisor to keep it running:

```ini
# /etc/systemd/system/zen-api.service
[Unit]
Description=Inspekt HTTP API
After=network.target

[Service]
Type=simple
User=zen
WorkingDirectory=/opt/zen-bridge
ExecStart=/usr/local/bin/uvicorn zen.app.api.server:app --host 127.0.0.1 --port 8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## Architecture

The HTTP API follows the same hexagonal architecture as the CLI:

```
┌──────────────────────────────────────────────────────────┐
│                     HTTP Request                         │
└────────────────────────┬─────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│              FastAPI Router (API Layer)                  │
│  • Validates request (Pydantic models)                   │
│  • Handles HTTP concerns (status codes, errors)          │
│  • Returns JSON responses                                │
└────────────────────────┬─────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│             Service Layer (Business Logic)               │
│  • NavigationService, ExtractionService, etc.            │
│  • Same services used by CLI!                            │
│  • Pure Python, no HTTP/Click knowledge                  │
└────────────────────────┬─────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│            Bridge Executor (Communication)               │
│  • Sends JavaScript to browser                           │
│  • Handles WebSocket/HTTP communication                  │
│  • Returns results                                       │
└────────────────────────┬─────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│                       Browser                            │
└──────────────────────────────────────────────────────────┘
```

**Key principles**:

- ✅ **No code duplication** - CLI and API share the same business logic
- ✅ **Consistent behavior** - Both interfaces produce identical results
- ✅ **Easy maintenance** - Add a command once, get CLI + API for free
- ✅ **Type safety** - Pydantic models validate all requests/responses

**Adding a new endpoint is easy**:

1. Add method to service layer (if needed)
2. Create endpoint in router that calls service
3. Register router in `server.py`
4. Done! Swagger UI and ReDoc update automatically

---

## Next Steps

- [API Reference](commands.md) - Complete list of all endpoints
- [Architecture Guide](../development/architecture.md) - Learn about the service layer
- [Contributing](../development/contributing.md) - Add new endpoints

---

## FAQ

### Q: Why do I need both the bridge server AND the API server?

**A**: They serve different purposes:

- **Bridge Server** (port 8765/8766) - Communicates with the browser via WebSocket
- **API Server** (port 8000) - Provides HTTP endpoints for you to call

The API server sends commands to the bridge server, which sends them to the browser.

### Q: Can I use the API without the CLI?

**A**: Yes! The API is completely independent. You just need:

1. Bridge server running (`zen server start`)
2. Browser with extension/userscript
3. API server running (`uvicorn ...`)

### Q: Why are there two documentation interfaces (Swagger + ReDoc)?

**A**: They serve different needs:

- **Swagger UI** - Best for testing and development
- **ReDoc** - Best for reading and sharing docs

Use whichever you prefer!

### Q: How do I add authentication?

**A**: Add FastAPI middleware for API keys, JWT, or OAuth. See [FastAPI Security docs](https://fastapi.tiangolo.com/tutorial/security/).

### Q: Can I generate client libraries?

**A**: Yes! Download the OpenAPI spec and use [OpenAPI Generator](https://openapi-generator.tech/):

```bash
# Download spec
curl http://localhost:8000/openapi.json > openapi.json

# Generate Python client
openapi-generator-cli generate -i openapi.json -g python -o client/

# Generate JavaScript client
openapi-generator-cli generate -i openapi.json -g javascript -o client/
```
