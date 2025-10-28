# Contributing to Zen Bridge

Thank you for your interest in contributing to Zen Bridge! This guide will help you get started with development.

---

## Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Development Workflow](#development-workflow)
- [Adding or Modifying Commands](#adding-or-modifying-commands)
- [Code Style & Standards](#code-style--standards)
- [Testing](#testing)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)
- [Project Structure](#project-structure)
- [Common Tasks](#common-tasks)

---

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Git
- A modern browser (Chrome, Firefox, Edge) with Tampermonkey extension
- Basic knowledge of Python, JavaScript, and async programming

### Quick Setup

```bash
# Clone the repository
git clone https://github.com/roelvangils/zen-bridge.git
cd zen-bridge

# Install in development mode
pip install -e .

# Verify installation
zen --version
```

---

## Development Setup

### Option 1: Using uv (Recommended)

[uv](https://github.com/astral-sh/uv) is a fast Python package installer and resolver.

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"

# Install pre-commit hooks (post-refactor)
pre-commit install
```

### Option 2: Using pip + venv

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .

# For development (after Phase 0 refactor)
pip install -e ".[dev]"
```

### Option 3: Using poetry

```bash
# Install poetry (if not already installed)
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Activate shell
poetry shell
```

---

## Development Workflow

### 1. Start the Bridge Server

In one terminal:

```bash
# Start the WebSocket server
zen server start
```

Expected output:
```
Zen Bridge WebSocket Server (aiohttp)
WebSocket: ws://127.0.0.1:8766/ws
HTTP API: http://127.0.0.1:8765

✓ Loaded control.js into cache (36766 bytes)

HTTP server running on http://127.0.0.1:8765
WebSocket server running on ws://127.0.0.1:8766/ws
Ready for connections!
```

### 2. Install Userscript in Browser

1. Install [Tampermonkey](https://www.tampermonkey.net/) browser extension
2. Open `userscript_ws.js` in the project root
3. Copy the entire file contents
4. Open Tampermonkey dashboard
5. Click "Create a new script"
6. Paste the contents and save
7. Open any website (e.g., https://example.com)
8. Check browser console for: `[Zen Bridge] Connected via WebSocket`

### 3. Test Commands

In another terminal:

```bash
# Test basic evaluation
zen eval "document.title"

# Test data extraction
zen extract-links

# Test control mode
zen control start
zen control next
zen control click
```

### 4. Make Your Changes

Edit the relevant Python files:
- `zen/cli.py` - CLI commands (current monolith)
- `zen/bridge_ws.py` - WebSocket server
- `zen/client.py` - HTTP client
- `zen/config.py` - Configuration management
- `zen/scripts/*.js` - JavaScript extraction/interaction scripts

### 5. Test Your Changes

```bash
# Quick test: Does it still work?
zen eval "document.title"

# After refactor: Run test suite
make test

# Run linter
make lint

# Run type checker
make typecheck
```

---

## Adding or Modifying Commands

⚠️ **IMPORTANT**: Before adding or modifying CLI commands, read the [**Command Development Guide**](COMMAND_DEVELOPMENT_GUIDE.md).

This comprehensive guide covers:
- Directory structure and path resolution rules
- Step-by-step instructions for adding new commands
- Complete testing checklist (MUST complete before submitting PR)
- Common pitfalls and how to avoid them
- Quick reference for file locations

**Why this is critical**: Incorrect path resolution can break commands. The guide provides exact patterns for:
- JavaScript scripts: `.parent.parent.parent / "scripts"`
- AI prompts: `.parent.parent.parent.parent / "prompts"`

Always complete the full testing checklist from the guide, including:
1. Help text verification
2. Path resolution testing
3. Script execution testing
4. Full functionality testing
5. Error handling testing
6. Integration testing with existing commands

---

## Code Style & Standards

### Python Style (Post-Refactor: Phase 0+)

We use **ruff** for linting and formatting.

```bash
# Format code
make format
# or: ruff format zen/

# Check code quality
make lint
# or: ruff check zen/

# Auto-fix issues
ruff check zen/ --fix
```

**Style Guidelines**:
- Line length: 100 characters
- Indentation: 4 spaces
- String quotes: Double quotes preferred
- Imports: Sorted alphabetically, grouped (stdlib, third-party, local)

### Type Hints (Post-Refactor: Phase 1+)

All functions must have type hints.

```python
# ✅ Good
def get_title(url: str, timeout: float = 10.0) -> str:
    """Get page title."""
    ...

# ❌ Bad
def get_title(url, timeout=10.0):
    ...
```

Run type checker:
```bash
make typecheck
# or: mypy zen/ --strict
```

### Docstrings

Use Google-style docstrings for all public functions.

```python
def execute_script(script_path: Path, timeout: float) -> dict[str, Any]:
    """Execute a JavaScript file in the browser.

    Args:
        script_path: Path to JavaScript file
        timeout: Maximum execution time in seconds

    Returns:
        Dictionary with execution result:
        - ok (bool): Whether execution succeeded
        - result (Any): Return value from JavaScript
        - error (str | None): Error message if failed

    Raises:
        ConnectionError: If bridge server is not running
        TimeoutError: If execution exceeds timeout
        FileNotFoundError: If script file does not exist

    Example:
        >>> result = execute_script(Path("scripts/extract_links.js"), 10.0)
        >>> if result["ok"]:
        ...     links = result["result"]
    """
    ...
```

### JavaScript Style

For scripts in `zen/scripts/`:

```javascript
// Use IIFE (Immediately Invoked Function Expression)
(function() {
    'use strict';

    // Your code here
    const result = doSomething();

    // Return value (will be JSON.stringify'd automatically)
    return result;
})();
```

**Guidelines**:
- Use modern ES6+ syntax
- Prefer `const` over `let`, avoid `var`
- Use `querySelector` / `querySelectorAll` for DOM access
- Handle errors gracefully (return error object)
- Comment complex logic

---

## Testing

### Current State (v1.0.0)

No tests exist yet. Manual testing only.

**Manual Test Checklist**:
1. Start server: `zen server start`
2. Install userscript in browser
3. Open test page (e.g., https://example.com)
4. Run 10 commands:
   - `zen eval "document.title"`
   - `zen extract-links`
   - `zen extract-page-structure`
   - `zen control start`
   - `zen control next` (5x)
   - `zen control click`
   - `zen get url`
   - `zen screenshot "body" test.png`
   - `zen wait "#logo" --timeout 5`
5. All should complete without errors

### Post-Refactor (Phase 0+)

After refactor, we'll have comprehensive tests:

```bash
# Run all tests
make test
# or: pytest tests/ -v

# Run specific test suite
pytest tests/unit/              # Unit tests only
pytest tests/integration/       # Integration tests
pytest tests/e2e/               # End-to-end browser tests

# Run with coverage report
pytest tests/ --cov=zen --cov-report=html
open htmlcov/index.html         # View coverage report

# Run specific test file
pytest tests/unit/test_config.py -v

# Run specific test
pytest tests/unit/test_config.py::test_load_default_config -v
```

### Writing Tests (Phase 1+)

**Unit Test Example**:
```python
# tests/unit/test_config.py
import pytest
from zen.config import load_config, validate_control_config

def test_load_default_config():
    """Test loading default config when no file exists."""
    config = load_config()
    assert config["ai-language"] == "auto"
    assert "control" in config

def test_validate_control_config_with_invalid_values():
    """Test validation normalizes invalid values."""
    config = {"control": {"auto-refocus": "invalid", "click-delay": -5}}
    validated = validate_control_config(config)
    assert validated["auto-refocus"] == "only-spa"  # Falls back to default
    assert validated["click-delay"] == 0  # Normalized to 0
```

**Integration Test Example**:
```python
# tests/integration/test_bridge.py
import pytest
from zen.client import BridgeClient

@pytest.fixture
def server():
    """Start bridge server for testing."""
    # Start server in background
    # Yield
    # Stop server

def test_execute_simple_code(server):
    """Test executing simple JavaScript."""
    client = BridgeClient()
    result = client.execute("1 + 1", timeout=5.0)
    assert result["ok"] is True
    assert result["result"] == 2
```

**E2E Test Example** (Phase 3):
```python
# tests/e2e/test_browser.py
import pytest
from playwright.sync_api import sync_playwright

@pytest.fixture
def browser_with_userscript():
    """Launch browser with Zen Bridge userscript."""
    # Setup: Start server, inject userscript, open test page
    # Yield browser page
    # Teardown

def test_extract_links_command(browser_with_userscript):
    """Test zen extract-links returns valid links."""
    page = browser_with_userscript
    page.goto("https://example.com")

    # Run CLI command (subprocess)
    result = subprocess.run(["zen", "extract-links"], capture_output=True)
    links = json.loads(result.stdout)

    assert len(links) > 0
    assert all("href" in link for link in links)
```

---

## Commit Guidelines

We follow **Conventional Commits** specification.

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, no logic change)
- `refactor`: Code refactoring (no feature change, no bug fix)
- `test`: Add or modify tests
- `chore`: Maintenance tasks (deps, config, etc.)
- `perf`: Performance improvements
- `ci`: CI/CD changes

**Examples**:

```bash
# New feature
git commit -m "feat(cli): add new extract-cookies command"

# Bug fix
git commit -m "fix(server): prevent event loop blocking in file I/O"

# Documentation
git commit -m "docs(contributing): add testing guidelines"

# Refactoring
git commit -m "refactor(cli): split eval commands into separate module"

# Breaking change
git commit -m "feat(config)!: require Python 3.11+

BREAKING CHANGE: Drop support for Python 3.7-3.10"
```

### Commit Best Practices

- ✅ Use present tense: "add feature" not "added feature"
- ✅ Use imperative mood: "move cursor" not "moves cursor"
- ✅ Keep subject line under 72 characters
- ✅ Separate subject from body with blank line
- ✅ Wrap body at 72 characters
- ✅ Explain what and why, not how
- ❌ Don't end subject line with a period

---

## Pull Request Process

### 1. Create a Branch

```bash
# Create feature branch
git checkout -b feature/my-feature

# Or bug fix branch
git checkout -b fix/issue-123
```

**Branch Naming**:
- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation
- `refactor/description` - Code refactoring
- `test/description` - Test additions

### 2. Make Changes and Commit

```bash
# Make your changes
# ...

# Stage changes
git add .

# Commit with conventional commit message
git commit -m "feat(cli): add new command"

# Push to your fork
git push origin feature/my-feature
```

### 3. Create Pull Request

1. Go to GitHub repository
2. Click "New Pull Request"
3. Select your branch
4. Fill out PR template:
   - **Description**: What does this PR do?
   - **Motivation**: Why is this change needed?
   - **Testing**: How was this tested?
   - **Checklist**: Complete the checklist

### 4. Code Review Checklist

Before submitting, ensure:

- [ ] Code follows style guidelines (ruff passes)
- [ ] All tests pass (pytest passes)
- [ ] Type checking passes (mypy passes)
- [ ] Documentation updated (if applicable)
- [ ] Commit messages follow Conventional Commits
- [ ] No breaking changes (or documented in CHANGELOG.md)
- [ ] Manual testing done (run 10+ commands)
- [ ] No new linter warnings
- [ ] No decrease in test coverage

### 5. Review and Merge

- Address reviewer feedback
- Make requested changes
- Push updates (no force-push unless necessary)
- Once approved, maintainer will merge

---

## Project Structure

### Current Structure (v1.0.0)

```
zen_bridge/
├── zen/
│   ├── __init__.py          # Package metadata
│   ├── cli.py               # 🔴 All CLI commands (3,946 lines)
│   ├── bridge_ws.py         # WebSocket server
│   ├── client.py            # HTTP client wrapper
│   ├── config.py            # Config management
│   ├── scripts/             # JavaScript files
│   │   ├── extract_*.js     # Data extraction
│   │   ├── control.js       # Keyboard navigation
│   │   ├── click_element.js # Interactions
│   │   └── ...
│   └── templates/           # (empty)
├── userscript_ws.js         # Tampermonkey userscript
├── setup.py                 # Package definition
├── README.md                # User documentation
├── SUMMARY.md               # Project overview
├── ARCHITECTURE.md          # Architecture docs
├── REFACTOR_PLAN.md         # Refactor plan
├── CONTRIBUTING.md          # This file
└── PROTOCOL.md              # WebSocket protocol spec
```

### Target Structure (Post-Refactor)

See REFACTOR_PLAN.md for detailed migration plan.

```
zen_bridge/
├── zen/
│   ├── domain/              # Layer 0: Pure domain logic
│   │   ├── models.py        # Pydantic models
│   │   └── validation.py    # Pure validation
│   ├── adapters/            # Layer 1: I/O adapters
│   │   ├── filesystem.py    # File operations
│   │   ├── websocket.py     # WebSocket client
│   │   └── http.py          # HTTP client
│   ├── services/            # Layer 2: Business logic
│   │   ├── script_loader.py
│   │   ├── bridge_executor.py
│   │   ├── ai_integration.py
│   │   └── control_manager.py
│   ├── app/                 # Layer 3: Application
│   │   ├── cli/             # CLI commands
│   │   │   ├── base.py
│   │   │   ├── eval_commands.py
│   │   │   ├── extract_commands.py
│   │   │   ├── control_commands.py
│   │   │   └── ...
│   │   ├── server.py        # WebSocket server
│   │   └── main.py          # Entry point
│   └── scripts/             # JavaScript files (unchanged)
├── tests/
│   ├── unit/                # Pure function tests
│   ├── integration/         # Server/client tests
│   ├── e2e/                 # Browser tests
│   └── fixtures/            # Test data
├── pyproject.toml           # Modern packaging
├── Makefile                 # Common tasks
└── ...
```

---

## Common Tasks

### Adding a New CLI Command

**Current Approach** (v1.0.0):

1. Open `zen/cli.py`
2. Add command at end of file:

```python
@cli.command()
@click.argument("arg")
@click.option("--timeout", type=float, default=10.0)
def my_command(arg: str, timeout: float) -> None:
    """My new command description."""
    client = BridgeClient()

    # Load script
    script_path = Path(__file__).parent / "scripts" / "my_script.js"
    with open(script_path) as f:
        code = f.read()

    # Execute
    result = client.execute(code, timeout=timeout)

    # Output
    output = format_output(result)
    click.echo(output)

    # Error handling
    if not result.get("ok"):
        sys.exit(1)
```

3. Test: `zen my-command test-arg`

**Post-Refactor Approach** (Phase 2+):

1. Create `zen/app/cli/my_commands.py`
2. Define command using services:

```python
import click
from zen.services.bridge_executor import BridgeExecutor
from zen.services.script_loader import ScriptLoader
from zen.app.cli.base import format_output

@click.command()
@click.argument("arg")
@click.option("--timeout", type=float, default=10.0)
def my_command(arg: str, timeout: float) -> None:
    """My new command description."""
    # Load script via service
    loader = ScriptLoader()
    code = loader.load_script("my_script.js")

    # Execute via service
    executor = BridgeExecutor()
    result = executor.execute(code, timeout=timeout)

    # Output
    output = format_output(result)
    click.echo(output)
```

3. Register in `zen/app/cli/main.py`:

```python
from zen.app.cli.my_commands import my_command

cli.add_command(my_command)
```

4. Write test:

```python
# tests/unit/test_my_commands.py
def test_my_command(mock_executor):
    result = runner.invoke(cli, ["my-command", "test-arg"])
    assert result.exit_code == 0
```

### Adding a New JavaScript Script

1. Create `zen/scripts/my_script.js`:

```javascript
/**
 * Description of what this script does.
 * @returns {Object} Description of return value
 */
(function() {
    'use strict';

    try {
        // Your code here
        const data = document.querySelectorAll('.item');
        const results = Array.from(data).map(el => ({
            text: el.textContent.trim(),
            href: el.querySelector('a')?.href
        }));

        return {
            ok: true,
            results: results
        };
    } catch (error) {
        return {
            ok: false,
            error: error.message
        };
    }
})();
```

2. Create corresponding CLI command (see above)
3. Test on a real page
4. Document in README.md

### Running Locally with Live Reload (Development)

```bash
# Terminal 1: Run server with auto-reload (Python 3.7+ only)
python zen/bridge_ws.py

# Terminal 2: Edit code
vim zen/cli.py

# Terminal 3: Test changes
zen eval "document.title"
```

No need to restart server for CLI changes (server is separate process).

### Debugging Tips

**Enable Verbose Logging**:

```bash
# Server side
zen server start  # Already verbose by default

# Browser side
# Edit userscript_ws.js, set:
const VERBOSE = true;
```

**Check Server Status**:

```bash
# Is server running?
zen server status

# Health check
curl http://127.0.0.1:8765/health
```

**WebSocket Connection Issues**:

1. Check browser console for WebSocket errors
2. Verify Tampermonkey script is active (green icon)
3. Refresh page to reconnect
4. Check firewall (should allow localhost)

**Command Not Working**:

1. Test simple command first: `zen eval "1+1"`
2. Check browser console for JavaScript errors
3. Try `zen --debug` flag (if available)
4. Check server logs for errors

---

## Getting Help

- **Documentation**: See ARCHITECTURE.md, PROTOCOL.md
- **Issues**: Check [GitHub Issues](https://github.com/roelvangils/zen-bridge/issues)
- **Discussions**: Use GitHub Discussions for questions
- **Bug Reports**: Open an issue with reproducible example

---

## Code of Conduct

Be respectful and constructive. We're all here to build something useful together.

---

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT License).

---

**Document Status**: ✅ Baseline (current workflow documented)
**Next Update**: After Phase 0 (add tooling commands, test examples)
**Last Updated**: 2025-10-27
