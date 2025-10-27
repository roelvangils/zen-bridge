# Refactor Plan: Zen Bridge

## Executive Summary

This document outlines a phased refactoring plan for the Zen Bridge project to improve modularity, testability, reliability, and long-term maintainability while preserving the stable public CLI interface.

**Status**: Draft - Awaiting approval before implementation
**Last Updated**: 2025-10-27

---

## Audit Findings

### Current State Metrics
- **Total Python LOC**: ~4,807 lines
- **Main modules**: 5 files (cli.py, bridge_ws.py, client.py, config.py, __init__.py)
- **Largest file**: cli.py (3,946 lines, 55+ functions/classes)
- **JavaScript files**: 25 scripts (~3,700 LOC)
- **Test coverage**: 0% (no tests exist)
- **Type coverage**: Minimal (~26 type hints across all files, no return types)
- **Documentation**: README.md only (no architecture docs)
- **CI/CD**: None (.github/ directory does not exist)

### Code Smells & Issues Identified

#### 🔴 CRITICAL Issues

1. **Monolithic CLI Module** (`zen/cli.py:3946`)
   - Single 3,946-line file with 55+ functions
   - Violates Single Responsibility Principle
   - Difficult to test, maintain, and understand
   - High cognitive load for contributors
   - **Impact**: High - central to all operations

2. **Zero Test Coverage**
   - No unit tests
   - No integration tests
   - No E2E tests
   - No test infrastructure
   - **Impact**: Critical - no safety net for refactoring

3. **Blocking I/O in Async Context** (`zen/bridge_ws.py:117, 275, 340`)
   ```python
   async def websocket_handler(request):
       # ... async context
       with open(script_path) as f:  # ❌ Blocking I/O!
           CACHED_CONTROL_SCRIPT = f.read()
   ```
   - File I/O operations block the event loop
   - Degrades WebSocket server performance
   - **Impact**: High - affects real-time responsiveness

4. **No Type Safety**
   - Only 26 type hints total across all files
   - No return type annotations
   - No mypy or type checking in workflow
   - Untyped WebSocket message protocol
   - **Impact**: High - runtime errors, poor IDE support

#### 🟡 HIGH Priority Issues

5. **Unvalidated WebSocket Protocol**
   - JSON messages lack schema validation
   - No Pydantic models for message types
   - String-based message type checking
   - Version mismatch warnings but no protocol versioning
   - **Impact**: Medium-High - protocol drift, breaking changes

6. **No Structured Configuration Management**
   - Config validation is manual and scattered
   - No single source of truth for schema
   - Error handling via try/except fallback to defaults
   - **Impact**: Medium - silent failures, difficult to extend

7. **Module Organization**
   - Flat structure: all code in `zen/` directory
   - No clear separation of concerns
   - Scripts directory mixed with Python modules
   - **Impact**: Medium - poor discoverability, harder onboarding

8. **Security Considerations**
   - ✅ Server binds to 127.0.0.1 by default (good!)
   - ⚠️  No explicit origin validation in WebSocket handler
   - ⚠️  No authentication/token mechanism documented
   - ⚠️  Arbitrary JavaScript execution (by design, but needs docs)
   - **Impact**: Medium - needs security documentation

#### 🟢 MEDIUM Priority Issues

9. **No Import Dependency Management**
   - ✅ No circular imports detected (good!)
   - ⚠️  No import layer enforcement
   - ⚠️  No tools to prevent future circular deps
   - **Impact**: Low-Medium - preventive measure

10. **Build and Tooling**
    - Uses setup.py (legacy, should migrate to pyproject.toml)
    - No linting configuration (ruff, black, isort)
    - No pre-commit hooks
    - No editor config
    - Python 3.7+ requirement (consider 3.11+ for modern features)
    - **Impact**: Low-Medium - developer experience

11. **Documentation Gaps**
    - No ARCHITECTURE.md
    - No CONTRIBUTING.md
    - No PROTOCOL.md
    - No docstring consistency (some modules have none)
    - **Impact**: Medium - onboarding friction

12. **Duplication and Code Reuse**
    - Multiple file read patterns (27 `open()` calls in cli.py alone)
    - Repeated error handling patterns
    - Similar JSON response formatting across handlers
    - **Impact**: Low - maintenance burden

---

## Refactoring Strategy

### Guiding Principles

1. **Behavior Preservation**: All CLI commands must work identically
2. **Incremental Safety**: Each phase must be independently testable
3. **No Big Bang**: Small, verifiable changes with tests at each step
4. **Dependency Hygiene**: Clear import layers, no circular dependencies
5. **Type Safety First**: Add types before refactoring logic

### Import Layer Architecture (Target)

```
Layer 0: Core/Domain (pure Python, no I/O, no external deps)
  └─ domain/models.py       - Pydantic models for protocol, config
  └─ domain/validation.py   - Pure validation logic

Layer 1: Adapters (I/O, external systems)
  └─ adapters/filesystem.py - File operations (async-aware)
  └─ adapters/websocket.py  - WebSocket handling
  └─ adapters/http.py       - HTTP client wrapper

Layer 2: Services (business logic, orchestration)
  └─ services/script_loader.py     - Load and cache JS scripts
  └─ services/bridge_executor.py   - Execute code via bridge
  └─ services/ai_integration.py    - AI language detection/processing
  └─ services/control_manager.py   - Control mode orchestration

Layer 3: Application (CLI, server entry points)
  └─ app/cli/              - CLI command groups
      ├─ base.py           - Shared CLI utilities
      ├─ eval_commands.py  - eval, exec
      ├─ extract_commands.py - extract-links, extract-article, etc.
      ├─ control_commands.py - control sub-commands
      ├─ server_commands.py  - server start/stop/status
  └─ app/server.py         - WebSocket server (refactored bridge_ws.py)
  └─ app/main.py           - Main CLI entry point
```

**Rules**:
- Higher layers can import lower layers
- Lower layers NEVER import higher layers
- Same-layer imports allowed within reason
- Enforce with ruff import rules

---

## Phase 0: Foundation & Infrastructure (REQUIRED FIRST)

**Goal**: Set up tooling, testing infrastructure, and baseline documentation without touching application code.

### Tasks

1. **Tooling Setup**
   - [ ] Create `pyproject.toml` (migrate from setup.py)
   - [ ] Configure ruff (linting + formatting)
   - [ ] Configure mypy (start with basic, progress to --strict)
   - [ ] Create `.editorconfig`
   - [ ] Set up pre-commit hooks (ruff, mypy, trailing whitespace)
   - [ ] Update Python requirement to 3.11+ (leverage modern features)

2. **Testing Infrastructure**
   - [ ] Create `tests/` directory structure
     ```
     tests/
       ├─ unit/           - Pure function tests
       ├─ integration/    - WebSocket, HTTP client tests
       ├─ e2e/            - Playwright browser tests
       ├─ fixtures/       - Test data, mock scripts
       └─ conftest.py     - Pytest fixtures
     ```
   - [ ] Install test dependencies: pytest, pytest-cov, pytest-asyncio, playwright
   - [ ] Create first "smoke test": import all modules successfully
   - [ ] Set up coverage reporting (pytest-cov)

3. **CI/CD Pipeline**
   - [ ] Create `.github/workflows/ci.yml`
     - Matrix: Python 3.11, 3.12, 3.13
     - Steps: lint (ruff), typecheck (mypy), test (pytest), coverage upload
     - Cache pip dependencies
   - [ ] Add status badges to README.md

4. **Baseline Documentation**
   - [ ] Create CONTRIBUTING.md (setup, scripts, commit conventions)
   - [ ] Create PROTOCOL.md stub (document current WebSocket protocol)
   - [ ] Add docstrings to existing functions (focus on public APIs first)

5. **Makefile / Task Runner**
   ```makefile
   .PHONY: dev test lint format typecheck e2e

   dev:
       pip install -e ".[dev]"

   test:
       pytest tests/ -v --cov=zen --cov-report=html

   lint:
       ruff check zen/

   format:
       ruff format zen/

   typecheck:
       mypy zen/

   e2e:
       pytest tests/e2e/ -v
   ```

### Verification Checklist (Phase 0)

- [ ] `make dev` installs all dependencies successfully
- [ ] `make lint` runs without errors
- [ ] `make format` formats code consistently
- [ ] `make typecheck` runs (may have errors, but runs)
- [ ] `make test` runs smoke test successfully
- [ ] CI pipeline runs on GitHub (all steps green on main branch)
- [ ] All existing CLI commands still work identically
- [ ] Documentation files exist and are readable

### Risks (Phase 0)
- **Low risk**: No code logic changes
- Potential friction: Team must adopt new tools (ruff, mypy)
- Mitigation: Provide clear CONTRIBUTING.md with examples

---

## Phase 1: Type Safety & Protocol Validation (FOUNDATION)

**Goal**: Add comprehensive type hints and validated message schemas before any structural refactoring.

### Tasks

1. **Create Domain Models** (`zen/domain/models.py`)
   ```python
   from pydantic import BaseModel, Field
   from typing import Literal, Optional

   class ExecuteRequest(BaseModel):
       type: Literal["execute"]
       request_id: str
       code: str

   class ExecuteResult(BaseModel):
       type: Literal["result"]
       request_id: str
       ok: bool
       result: Optional[Any] = None
       error: Optional[str] = None
       url: Optional[str] = None
       title: Optional[str] = None

   class ReinitControlRequest(BaseModel):
       type: Literal["reinit_control"]
       config: dict[str, Any]

   # ... more message types

   class ControlConfig(BaseModel):
       auto_refocus: Literal["always", "only-spa", "never"] = "only-spa"
       focus_outline: Literal["custom", "original", "none"] = "custom"
       # ... all control settings with validation
   ```

2. **Add Type Hints to Existing Code**
   - [ ] Add return types to all functions in `config.py`
   - [ ] Add return types to all functions in `client.py`
   - [ ] Add return types to all functions in `bridge_ws.py`
   - [ ] Add parameter types where missing
   - [ ] Use `from __future__ import annotations` for forward refs

3. **Integrate Pydantic Validation**
   - [ ] Validate all WebSocket incoming messages with models
   - [ ] Validate all HTTP request bodies with models
   - [ ] Update `config.py` to use `ControlConfig` Pydantic model
   - [ ] Add error handling for validation errors

4. **Protocol Documentation**
   - [ ] Document all message types in PROTOCOL.md
   - [ ] Add JSON schema examples for each message type
   - [ ] Document version handshake mechanism
   - [ ] Document error response format

5. **Type Checking**
   - [ ] Enable mypy in CI with strict mode
   - [ ] Fix all mypy errors (aim for 0 errors)
   - [ ] Add `py.typed` marker file

### Unit Tests (Phase 1)

- [ ] `tests/unit/test_models.py`: Validate all Pydantic models
- [ ] `tests/unit/test_config.py`: Test config loading, merging, validation
- [ ] Test invalid configs raise appropriate errors
- [ ] Test config file precedence (local > ~/.zen > defaults)

### Verification Checklist (Phase 1)

- [ ] `mypy zen/ --strict` passes with 0 errors
- [ ] All WebSocket messages are validated (test with invalid messages)
- [ ] All config loads are validated (test with invalid JSON)
- [ ] Unit tests: ≥80% coverage on config.py, models.py
- [ ] PROTOCOL.md documents all message types with examples
- [ ] All existing CLI commands still work identically
- [ ] CI pipeline includes type checking step

### Risks (Phase 1)
- **Medium risk**: Type hints may reveal hidden bugs
- Pydantic validation may reject previously "accepted" malformed messages
- Mitigation: Thorough testing with real browser + userscript
- Mitigation: Document breaking changes (consider version bump)

---

## Phase 2: Extract Core Logic & Services (REFACTOR)

**Goal**: Break up monolithic cli.py into focused modules and extract business logic into services.

### Tasks

1. **Create Service Layer**

   **A. Script Loader Service** (`zen/services/script_loader.py`)
   - [ ] Extract all script loading logic from cli.py
   - [ ] Implement async file reading
   - [ ] Cache scripts in memory (like control.js)
   - [ ] Handle template substitution (ACTION_PLACEHOLDER, etc.)

   **B. Bridge Executor Service** (`zen/services/bridge_executor.py`)
   - [ ] Extract BridgeClient wrapper logic
   - [ ] Standardize error handling
   - [ ] Add retry logic (configurable)
   - [ ] Handle result formatting

   **C. AI Integration Service** (`zen/services/ai_integration.py`)
   - [ ] Extract language detection logic
   - [ ] Extract AI prompt construction
   - [ ] Handle AI service calls (currently in CLI)

   **D. Control Manager Service** (`zen/services/control_manager.py`)
   - [ ] Extract control mode state management
   - [ ] Handle refocus notifications
   - [ ] Manage auto-reinit logic

2. **Create Adapter Layer**

   **A. Filesystem Adapter** (`zen/adapters/filesystem.py`)
   ```python
   from pathlib import Path
   import aiofiles

   async def read_text_async(path: Path) -> str:
       """Async file reading for use in async contexts."""
       async with aiofiles.open(path, 'r') as f:
           return await f.read()

   def read_text_sync(path: Path) -> str:
       """Sync file reading for use in sync contexts."""
       with open(path, 'r') as f:
           return f.read()
   ```
   - [ ] Replace all direct file I/O with adapter calls
   - [ ] Use async version in bridge_ws.py
   - [ ] Use sync version in CLI

   **B. WebSocket Adapter** (`zen/adapters/websocket.py`)
   - [ ] Extract WebSocket connection management
   - [ ] Implement reconnect logic
   - [ ] Handle connection pooling if needed

3. **Refactor bridge_ws.py** (becomes `zen/app/server.py`)
   - [ ] Replace blocking file I/O with `filesystem.read_text_async()`
   - [ ] Use Pydantic models for all message handling
   - [ ] Extract handler functions to use services
   - [ ] Separate HTTP handlers into `zen/app/server/handlers.py`
   - [ ] Move WebSocket logic to adapter

4. **Split cli.py into Command Groups**

   Create `zen/app/cli/` with:
   - [ ] `base.py`: Shared utilities (format_output, CustomGroup, etc.)
   - [ ] `eval_commands.py`: eval, exec commands
   - [ ] `extract_commands.py`: All extract-* commands
   - [ ] `inspect_commands.py`: inspect, get, screenshot commands
   - [ ] `control_commands.py`: control start/stop/next/prev/click/etc.
   - [ ] `interaction_commands.py`: click, type, wait, watch commands
   - [ ] `server_commands.py`: server start/stop/status
   - [ ] `ai_commands.py`: describe, summarize commands
   - [ ] `main.py`: Main CLI group that imports all command groups

   Each command group:
   - Imports only what it needs from services
   - Maximum 300 lines per file
   - Well-documented with docstrings

5. **Update Entry Point**
   - [ ] Update setup.py entry point to `zen.app.cli.main:cli`
   - [ ] Test installation with `pip install -e .`

### Unit Tests (Phase 2)

- [ ] `tests/unit/test_script_loader.py`: Test script loading, caching, substitution
- [ ] `tests/unit/test_bridge_executor.py`: Test execution flow (mock client)
- [ ] `tests/unit/test_ai_integration.py`: Test language detection, prompt building
- [ ] `tests/unit/test_filesystem.py`: Test async/sync file reading
- [ ] `tests/unit/test_cli_commands.py`: Test CLI command parsing (mock services)

### Integration Tests (Phase 2)

- [ ] `tests/integration/test_bridge_loop.py`:
  - Start bridge_ws server
  - Mock browser WebSocket client
  - Send execute request
  - Verify response format
- [ ] `tests/integration/test_client.py`:
  - Test BridgeClient with real server
  - Test timeout handling
  - Test version checking

### Verification Checklist (Phase 2)

- [ ] All unit tests pass with ≥80% coverage on services
- [ ] All integration tests pass
- [ ] No file in `zen/app/cli/` exceeds 400 lines
- [ ] All imports follow layer architecture (enforce with ruff)
- [ ] No circular dependencies (test with import-linter or manual)
- [ ] `mypy zen/ --strict` still passes
- [ ] All existing CLI commands still work identically
- [ ] `pip install -e .` works
- [ ] `zen --help` shows all commands
- [ ] Manual test: Run 5 different CLI commands successfully

### Risks (Phase 2)
- **High risk**: Major structural changes
- Import path changes may break external users (if any)
- Services may have subtle behavior differences
- Mitigation: Comprehensive integration tests
- Mitigation: Manual E2E testing checklist
- Mitigation: Keep old cli.py as backup during transition

---

## Phase 3: Testing, E2E, Documentation (VALIDATION)

**Goal**: Achieve comprehensive test coverage, set up E2E tests, and complete all documentation.

### Tasks

1. **E2E Test Suite with Playwright**

   Create `tests/e2e/test_browser_integration.py`:
   ```python
   import pytest
   from playwright.sync_api import sync_playwright

   @pytest.fixture
   def browser_with_userscript():
       """Launch browser with userscript injected."""
       # Setup: Start bridge server, inject userscript, open test page
       # Yield browser page
       # Teardown: Close browser, stop server

   def test_eval_command(browser_with_userscript):
       """Test: zen eval 'document.title' returns page title."""
       # Run CLI command
       # Assert output matches browser title

   def test_extract_links(browser_with_userscript):
       """Test: zen extract-links returns valid link JSON."""
       # Navigate to test page with known links
       # Run CLI command
       # Assert all expected links present

   def test_control_mode_navigation(browser_with_userscript):
       """Test: control next navigates focus correctly."""
       # Start control mode
       # Send 'next' command
       # Assert focus moved in browser
   ```

   - [ ] Test page: Create `tests/fixtures/test_page.html` with known elements
   - [ ] Test 10+ critical CLI commands end-to-end
   - [ ] Test WebSocket reconnection after page reload
   - [ ] Test control mode auto-reinit

2. **Complete Documentation**

   **A. ARCHITECTURE.md**
   - [ ] High-level architecture diagram (ASCII or Mermaid)
   - [ ] Module dependency graph
   - [ ] Data flow: CLI → Server → Browser → Response
   - [ ] Import layer architecture
   - [ ] Extension points (adding new commands, scripts)

   **B. PROTOCOL.md** (complete)
   - [ ] Protocol versioning strategy
   - [ ] Handshake flow
   - [ ] All message types with JSON schemas
   - [ ] Error handling and retries
   - [ ] Backpressure / rate limiting (if any)

   **C. CONTRIBUTING.md** (complete)
   - [ ] Setup guide (uv/poetry options)
   - [ ] Development workflow (make commands)
   - [ ] Running tests (unit, integration, E2E)
   - [ ] Conventional Commits guide
   - [ ] Branching strategy
   - [ ] Code review checklist
   - [ ] How to add a new CLI command
   - [ ] How to add a new JavaScript script

   **D. SECURITY.md**
   - [ ] Threat model (localhost-only by design)
   - [ ] No remote binding by default
   - [ ] Arbitrary JS execution is intentional (user must trust scripts)
   - [ ] No secrets in logs or output
   - [ ] Version compatibility checks

   **E. SUMMARY.md** (this file)
   - [ ] Current state overview
   - [ ] Key risks and mitigations
   - [ ] Refactor highlights
   - [ ] How to run/test
   - [ ] Quick start for contributors

3. **Code Quality**
   - [ ] Add missing docstrings (Google or NumPy style)
   - [ ] Ensure all public APIs have docstrings
   - [ ] Add type hints to all functions (100% coverage)
   - [ ] Run coverage report: `pytest --cov=zen --cov-report=html`
   - [ ] Achieve ≥80% coverage on critical paths

4. **Performance & Reliability**
   - [ ] Benchmark WebSocket throughput (requests/sec)
   - [ ] Test with 100+ rapid commands
   - [ ] Test server restart with pending requests
   - [ ] Test browser disconnect/reconnect scenarios
   - [ ] Add logging (structlog or stdlib logging)

### Verification Checklist (Phase 3)

- [ ] All E2E tests pass in real browser (Playwright)
- [ ] Test coverage ≥80% on zen/ (check with `pytest --cov`)
- [ ] All documentation files exist and are comprehensive
- [ ] `make dev && make test && make e2e` all succeed
- [ ] `make lint && make format && make typecheck` all pass
- [ ] CI pipeline runs all checks and tests
- [ ] Manual walkthrough: Install fresh, run 10 commands, all work
- [ ] Performance: Server handles 100 requests in <10s
- [ ] Reliability: Browser reconnect works, pending requests complete

### Risks (Phase 3)
- **Low risk**: Mostly additive (tests, docs)
- E2E tests may be flaky (timing issues, browser inconsistencies)
- Mitigation: Explicit waits, retry logic in tests
- Mitigation: Playwright's auto-wait features

---

## Success Metrics

After completing all phases, the following must be true:

### Functional Requirements
- [ ] All 33+ CLI commands work identically to v1.0.0
- [ ] WebSocket server runs stably for >1 hour under load
- [ ] Browser reconnect works seamlessly after page reload
- [ ] Control mode auto-reinit works correctly
- [ ] CLI installable via `pipx install zen-bridge`

### Quality Metrics
- [ ] Test coverage ≥80% on critical modules (services, adapters, server)
- [ ] E2E coverage: ≥10 browser tests passing
- [ ] `mypy --strict` passes with 0 errors
- [ ] `ruff check` passes with 0 warnings
- [ ] No circular dependencies (verified with import checks)

### Maintainability Metrics
- [ ] Largest Python file ≤400 lines
- [ ] All modules follow import layer architecture
- [ ] All public APIs have docstrings
- [ ] All message types validated with Pydantic
- [ ] Clear separation: app → services → adapters → domain

### Documentation Metrics
- [ ] SUMMARY.md, ARCHITECTURE.md, PROTOCOL.md, CONTRIBUTING.md, SECURITY.md all exist
- [ ] Protocol versioned and documented
- [ ] Architecture diagram shows data flow
- [ ] Developer setup takes <10 minutes following docs

### CI/CD Metrics
- [ ] CI runs on Python 3.11, 3.12, 3.13
- [ ] All CI steps pass (lint, typecheck, test, e2e)
- [ ] Coverage report uploaded to CI artifacts

---

## Rollout & Validation Plan

### After Each Phase

1. **Run Full Verification Checklist** (see phase sections)
2. **Manual Testing**: Run 10 representative CLI commands
3. **Browser Testing**: Test in Chrome, Firefox, Edge (Tampermonkey)
4. **Performance Check**: Measure latency, throughput
5. **Code Review**: Peer review all changes
6. **Commit**: Conventional commit message (e.g., `refactor(phase1): add type safety`)
7. **Tag**: Git tag (e.g., `refactor-phase1-complete`)

### Final Validation (After Phase 3)

1. **Fresh Install Test**
   ```bash
   python3.11 -m venv test_env
   source test_env/bin/activate
   pip install -e .
   zen --version
   zen server start  # Terminal 1
   zen eval "document.title"  # Terminal 2
   ```

2. **Cross-Platform Test** (if applicable)
   - macOS (primary)
   - Linux (CI)
   - Windows (optional, document known issues)

3. **Load Test**
   - Start server
   - Run 100 `zen eval` commands in parallel
   - No errors, all complete in reasonable time

4. **Documentation Review**
   - Ask fresh contributor to follow CONTRIBUTING.md
   - Gather feedback, iterate

5. **Tag Release**
   - `git tag v2.0.0-refactor`
   - Update CHANGELOG.md

---

## Dependencies & Installation

### Phase 0 Dependencies (add to pyproject.toml)

```toml
[project]
name = "zen-bridge"
version = "2.0.0"
requires-python = ">=3.11"
dependencies = [
    "click>=8.1.0",
    "requests>=2.31.0",
    "aiohttp>=3.9.0",
    "pydantic>=2.5.0",
    "aiofiles>=23.2.0",  # For async file I/O
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "pytest-asyncio>=0.21.0",
    "playwright>=1.40.0",
    "mypy>=1.7.0",
    "ruff>=0.1.6",
    "pre-commit>=3.5.0",
]

[tool.ruff]
line-length = 100
target-version = "py311"
select = ["E", "F", "I", "UP", "B", "SIM", "TCH"]
ignore = ["E501"]  # Line too long (handled by formatter)

[tool.ruff.lint.isort]
force-single-line = false
known-first-party = ["zen"]

[tool.mypy]
python_version = "3.11"
strict = true
warn_redundant_casts = true
warn_unused_ignores = true
disallow_untyped_defs = true
disallow_any_generics = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"
addopts = "-v --cov=zen --cov-report=term-missing"

[tool.coverage.run]
source = ["zen"]
omit = ["tests/*", "zen/__pycache__/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
]
```

---

## Risk Summary & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Breaking CLI behavior | High | Low | Comprehensive E2E tests, manual validation checklist |
| Type hints reveal bugs | Medium | Medium | Fix bugs incrementally, add tests |
| Async refactor breaks WS server | High | Low | Integration tests, load tests |
| Import refactor breaks installs | Medium | Low | Test `pip install -e .` in CI |
| E2E tests flaky | Low | Medium | Use Playwright auto-wait, explicit waits, retries |
| Team rejects new tooling | Low | Medium | Clear CONTRIBUTING.md, provide examples, training |
| Refactor takes too long | Low | High | Phased approach, each phase delivers value independently |
| Protocol changes break userscript | Medium | Low | Version checking, document breaking changes |

---

## Timeline Estimate

Assuming 1 developer, full-time:

- **Phase 0**: 3-5 days (tooling, CI, baseline tests)
- **Phase 1**: 5-7 days (types, Pydantic, protocol docs)
- **Phase 2**: 10-14 days (split cli.py, services, adapters)
- **Phase 3**: 7-10 days (E2E tests, docs, final validation)

**Total**: 25-36 days (5-7 weeks)

Part-time or multiple contributors: Adjust accordingly.

---

## Open Questions (To Resolve Before Starting)

1. **Python Version**: Bump to 3.11+ required? (Recommendation: Yes)
2. **Pydantic v2**: OK to use Pydantic v2? (Recommendation: Yes, it's stable)
3. **Breaking Changes**: Is v2.0.0 acceptable for this refactor? (Recommendation: Yes)
4. **External Users**: Any known external projects depending on internal APIs? (Check before refactor)
5. **AI Service**: What AI service is used for describe/summarize? (Document in ARCHITECTURE.md)
6. **Control Mode**: Is control mode a first-class feature? (Impacts testing priority)

---

## Approval & Sign-Off

**Prepared by**: Assistant (Claude Code)
**Date**: 2025-10-27
**Status**: ⏳ Awaiting Review

**Approved by**: _________________
**Date**: _________________

**Notes**:
- Review each phase independently
- Provide feedback on risks, timeline, approach
- Confirm Python 3.11+ requirement OK
- Confirm v2.0.0 semver bump OK

---

## Next Steps (After Approval)

1. Create GitHub Project/Issues for each phase
2. Branch strategy: `refactor-phase0`, `refactor-phase1`, etc.
3. Set up Slack/Discord for refactor questions
4. Kick off Phase 0
