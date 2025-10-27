# Changelog

All notable changes to Zen Browser Bridge are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.0.0] - 2025-10-27

### Major Refactoring - Hexagonal Architecture

Version 2.0.0 represents a comprehensive refactoring of Zen Bridge with **zero breaking changes**. All existing commands and features remain fully compatible with v1.x.

#### Architecture Improvements

**4-Layer Hexagonal Architecture:**

- **Domain Layer** - Pure business logic with Pydantic models
- **Adapter Layer** - I/O operations (filesystem, WebSocket)
- **Service Layer** - Application services and orchestration
- **Application Layer** - CLI commands and server

**Modular CLI Structure:**

Split monolithic `cli.py` (3,946 lines) into 12 focused modules:

- `cli_main.py` - Entry point and shared utilities (147 lines)
- `cli_core.py` - Core commands (eval, exec, repl, info) (379 lines)
- `cli_interaction.py` - Element interaction (click, inspect, highlight, wait) (293 lines)
- `cli_extraction.py` - Data extraction (links, outline, selected) (315 lines)
- `cli_ai.py` - AI-powered features (summarize, describe) (174 lines)
- `cli_control.py` - Keyboard control mode (240 lines)
- `cli_navigation.py` - Navigation commands (open, back, forward, reload) (167 lines)
- `cli_media.py` - Media commands (screenshot, download) (193 lines)
- `cli_utilities.py` - Utility commands (send, watch, cookies) (148 lines)
- `cli_server.py` - Server management (125 lines)
- `cli_browser.py` - Browser state (tabs, windows) (102 lines)
- `cli_help.py` - Enhanced help system (273 lines)

**New Services (97%+ test coverage):**

- `bridge_executor.py` (263 lines, 96.63% coverage) - Standardized execution flow with retry logic
- `ai_integration.py` (367 lines, 99.30% coverage) - AI orchestration and language detection
- `control_manager.py` (230 lines, 100% coverage) - Control mode state and notification management
- `script_loader.py` (existing, enhanced) - Script discovery and loading

#### Testing & Quality

- **267 tests** total (up from 52 in v1.0.0)
- **192 new tests** added across all layers
- **97%+ coverage** on core services
- **12.53% overall coverage** (focused on critical paths)
- All tests passing with zero regressions

**Test Distribution:**

- Unit tests: 139 tests
- Integration tests: 97 tests
- End-to-end tests: 31 tests (Playwright-based)

#### Performance Improvements

- Eliminated blocking I/O operations
- Optimized WebSocket communication
- Faster command execution times
- Reduced memory footprint

#### Documentation

**New comprehensive documentation:**

- `ARCHITECTURE.md` - System design and layer responsibilities
- `SECURITY.md` - Security model and best practices
- `PROTOCOL.md` - WebSocket protocol specification
- `REFACTOR_PLAN.md` - Complete refactoring history and metrics

**MkDocs Documentation Site:**

- Material theme with dark/light mode
- Complete user guides with examples
- API reference for all services and models
- Development guides for contributors
- Interactive navigation with search

#### Type Safety

- Full type hints throughout codebase
- Pydantic models for all data structures
- Protocol validation with clear error messages
- MyPy type checking enabled

#### CI/CD Pipeline

- Automated testing on Python 3.11, 3.12, 3.13
- Linting with Ruff
- Type checking with MyPy
- Code formatting enforcement
- Test coverage reporting

#### Project Structure

```
zen/
├── domain/          # Core models (Pydantic)
│   ├── models.py
│   └── protocols.py
├── adapters/        # I/O adapters
│   ├── filesystem.py
│   └── websocket.py
├── services/        # Business logic
│   ├── bridge_executor.py
│   ├── ai_integration.py
│   ├── control_manager.py
│   └── script_loader.py
└── app/
    ├── cli/         # CLI commands (12 modules)
    └── bridge_ws.py # WebSocket server
```

### Changed

- Refactored entire codebase to hexagonal architecture
- Improved error handling and validation
- Enhanced type safety with Pydantic
- Optimized WebSocket connection handling
- Modernized development tooling

### Added

- Comprehensive test suite (267 tests)
- MkDocs documentation with Material theme
- CI/CD pipeline with GitHub Actions
- Development documentation (ARCHITECTURE.md, SECURITY.md)
- Type checking with MyPy
- Code quality tools (Ruff, pre-commit hooks)

### Fixed

- WebSocket connection stability issues
- Memory leaks in long-running sessions
- Race conditions in async operations
- Error handling edge cases

---

## [1.0.0] - 2025-10-27

### First Production Release

Initial production-ready release of Zen Browser Bridge with all core features implemented.

#### Core Features

**JavaScript Execution:**

- Execute JavaScript in active browser tab
- Interactive REPL for live experimentation
- Execute code from files or stdin
- Multiple output formats (text, JSON, raw)
- Script execution with built-in library

**Element Interaction:**

- Click, double-click, right-click elements
- Inspect and highlight elements
- Wait for elements (with timeout and conditions)
- Element state detection (visible, hidden)
- Text content matching

**Data Extraction:**

- Extract all links (internal/external filtering)
- Page outline with heading hierarchy
- Selected text extraction
- Page information and metadata
- Cookie management

**AI-Powered Features:**

- Article summarization with Readability
- Page descriptions for screen readers
- AI language configuration and auto-detection
- Customizable AI prompts

**Keyboard Control Mode:**

- Navigate pages entirely from keyboard
- Auto-refocus after navigation
- Visual feedback with blue outlines
- Real-time terminal announcements
- Optional text-to-speech (macOS)
- Persistent across page loads

**Navigation:**

- Open URLs with optional wait
- Browser history (back/forward)
- Page reload (normal and hard reload)
- Navigation state tracking

**Media Handling:**

- Screenshot capture by selector
- Interactive file downloader
- Support for multiple file types (images, documents, videos, audio, archives)

**Real-time Monitoring:**

- Watch keyboard input events
- Real-time event streaming
- Formatted output display

**Server Management:**

- WebSocket server with daemon mode
- Server status checking
- Process management
- Health monitoring

#### Technical Features

- **WebSocket Architecture** - Fast bi-directional communication
- **HTTP API** - RESTful command interface
- **Configuration System** - JSON-based configuration
- **Userscript Integration** - Browser-side JavaScript injection
- **Error Handling** - Comprehensive error messages
- **Timeout Support** - Configurable timeouts for all commands
- **JSON Output** - Machine-readable output format
- **Debug Mode** - Verbose logging for troubleshooting

#### Built-in Scripts

- `extract_images.js` - Extract all images with metadata
- `extract_table.js` - Convert tables to JSON
- `extract_metadata.js` - SEO metadata extraction
- `performance_metrics.js` - Performance monitoring
- `inject_jquery.js` - jQuery injection
- `highlight_selector.js` - Visual element highlighting

#### CLI Commands (30+)

Core commands: `eval`, `exec`, `repl`, `info`
Interaction: `click`, `double-click`, `right-click`, `inspect`, `inspected`, `highlight`, `wait`
Extraction: `links`, `outline`, `selected`, `cookies`
AI: `summarize`, `describe`
Control: `control`
Navigation: `open`, `back`, `forward`, `reload`
Media: `screenshot`, `download`
Utilities: `send`, `watch`
Server: `server start`, `server stop`, `server status`
Help: `userscript`, `--help`

#### Requirements

- Python 3.11+
- Zen Browser (or any browser with userscript support)
- Userscript manager (Violentmonkey, Tampermonkey, or Greasemonkey)

#### Dependencies

- `click>=8.1.0` - CLI framework
- `requests>=2.31.0` - HTTP client
- `aiohttp>=3.9.0` - Async HTTP
- `pydantic>=2.5.0` - Data validation

#### Development Tools

- `pytest>=7.4.0` - Testing framework
- `ruff>=0.1.6` - Linting and formatting
- `mypy>=1.7.0` - Type checking
- `playwright>=1.40.0` - E2E testing

---

## Version History Summary

| Version | Release Date | Highlights |
|---------|--------------|------------|
| 2.0.0   | 2025-10-27   | Major refactoring: hexagonal architecture, 267 tests, comprehensive documentation |
| 1.0.0   | 2025-10-27   | First production release: 30+ commands, AI features, keyboard control |

---

## Development Timeline

**October 27, 2025** - Complete refactoring cycle:

- Phase 0: Foundation and infrastructure setup
- Phase 1: Type safety and protocol validation
- Phase 2: Services and adapters layers, fixed blocking I/O
- Phase 3: CLI modularization and comprehensive testing
- Documentation: MkDocs site with Material theme

**October 26-27, 2025** - Feature additions:

- AI-powered article summarization
- Page description for screen readers
- Keyboard control mode with auto-refocus
- Link extraction with filtering
- Page outline visualization
- Language detection and configuration

**October 25, 2025** - Initial development:

- WebSocket communication architecture
- Basic CLI commands
- Userscript integration
- Element highlighting
- Initial feature set

---

## Next Steps

- [License](license.md)
- [Contributing Guide](../development/contributing.md)
- [Architecture Overview](../development/architecture.md)
- [Home](../index.md)
