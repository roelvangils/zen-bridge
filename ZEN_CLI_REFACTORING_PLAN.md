# ZEN CLI REFACTORING PLAN

## Current State Analysis

**File:** `zen/cli.py` - 4,093 lines  
**Commands:** 42 (30 top-level + 12 subcommands)  
**Complexity:** High - monolithic structure  
**Maintainability:** Low - difficult to test and modify individual commands  

## Target State

**Structure:** Modular CLI with 9-11 separate modules  
**Each Module:** <400 lines, focused on one functional area  
**Maintainability:** High - easy to test, modify, and extend  
**Organization:** Clear separation of concerns  

## Refactoring Steps

### Phase 1: Create Base Module

**File:** `zen/cli/base.py` (~150 lines)

Extract shared utilities:
- `format_output()` - Output formatting (JSON/raw/auto)
- `get_ai_language()` - Language detection for AI
- `CustomGroup` class - Enhanced Click help formatting
- Built-in saves: `_builtin_open`, `_builtin_next`
- Common imports and constants

```python
# zen/cli/base.py
import click
import json
from zen import config as zen_config, __version__

_builtin_open = open
_builtin_next = next

class CustomGroup(click.Group):
    # ... implementation

def format_output(result, format_type="auto"):
    # ... implementation

def get_ai_language(language_override=None, page_lang=None):
    # ... implementation
```

### Phase 2: Create Simple Command Modules

#### Module 2: Execution Commands
**File:** `zen/cli/exec.py` (~100 lines)
- `eval` command
- `exec` command

**Dependencies:** `base.py`, BridgeClient, click

#### Module 3: Navigation Commands
**File:** `zen/cli/navigation.py` (~150 lines)
- `open` command
- `back` command
- `forward` command
- `reload` command
- Hidden aliases: `previous`, `next`, `refresh`

**Dependencies:** `base.py`, BridgeClient, click

#### Module 4: Selection Command
**File:** `zen/cli/selection.py` (~80 lines)
- `selected` command

**Dependencies:** `base.py`, BridgeClient, click

#### Module 5: Server Commands
**File:** `zen/cli/server.py` (~100 lines)
- Server group
- `server start` subcommand
- `server status` subcommand
- `server stop` subcommand

**Dependencies:** `base.py`, BridgeClient, subprocess

### Phase 3: Create Complex Command Modules

#### Module 6: Inspection Commands
**File:** `zen/cli/inspect.py` (~150 lines)
- `inspect` command
- `inspected` command
- `screenshot` command

**Dependencies:** `base.py`, BridgeClient, base64, datetime, pathlib

#### Module 7: Interaction Commands
**File:** `zen/cli/interaction.py` (~200 lines)
- `click` command
- `double-click` command
- Hidden: `doubleclick` alias
- `right-click` command
- Hidden: `rightclick` alias
- `wait` command
- `send` command
- Helper: `_perform_click()` function

**Dependencies:** `base.py`, BridgeClient, click, json

#### Module 8: Cookie Management
**File:** `zen/cli/cookies.py` (~180 lines)
- Cookie group
- `cookies list` subcommand
- `cookies get` subcommand
- `cookies set` subcommand
- `cookies delete` subcommand
- `cookies clear` subcommand
- Helper: `_execute_cookie_action()` function

**Dependencies:** `base.py`, BridgeClient, click, json

#### Module 9: Watch and Control
**File:** `zen/cli/watch.py` (~250 lines)
- Watch group
- `watch input` subcommand
- `watch all` subcommand
- `control` command (top-level)
- Configuration handling
- Terminal mode operations

**Dependencies:** `base.py`, BridgeClient, click, json, select, termios, tty, subprocess, signal

#### Module 10: Content Extraction
**File:** `zen/cli/extraction.py` (~400 lines)
- `describe` command
- `outline` command
- `links` command
- `summarize` command
- Helper: `_enrich_link_metadata()` function
- Helper: `_enrich_external_links()` function
- AI language detection

**Dependencies:** `base.py`, BridgeClient, click, json, subprocess, re, pathlib, ThreadPoolExecutor

#### Module 11: Utility Commands
**File:** `zen/cli/util.py` (~250 lines)
- `info` command
- `repl` command
- `userscript` command
- `download` command
- `highlight` command
- Helpers:
  - `_get_domain_metrics()` function
  - `_get_response_headers()` function
  - `_get_robots_txt()` function

**Dependencies:** `base.py`, BridgeClient, click, json, requests, subprocess, socket, ssl, pathlib, urllib.parse

### Phase 4: Create Package Structure

**File:** `zen/cli/__init__.py` (~100 lines)

Register all commands and groups:

```python
# zen/cli/__init__.py
import click
from . import base
from . import exec
from . import navigation
from . import selection
from . import server
from . import inspect
from . import interaction
from . import cookies
from . import watch
from . import extraction
from . import util

# Create main CLI group
@click.group(cls=base.CustomGroup)
@click.version_option(version=__version__)
def cli():
    """Zen Browser Bridge - Execute JavaScript in your browser from the CLI."""
    pass

# Register top-level commands
cli.add_command(exec.eval)
cli.add_command(exec.exec)
cli.add_command(navigation.open)
cli.add_command(navigation.back)
cli.add_command(navigation.previous)
cli.add_command(navigation.forward)
cli.add_command(navigation.next)
cli.add_command(navigation.reload)
cli.add_command(navigation.refresh)
cli.add_command(selection.selected)
cli.add_command(inspect.inspect)
cli.add_command(inspect.inspected)
cli.add_command(inspect.screenshot)
cli.add_command(interaction.click_element)
cli.add_command(interaction.double_click)
cli.add_command(interaction.doubleclick_alias)
cli.add_command(interaction.right_click)
cli.add_command(interaction.rightclick_alias)
cli.add_command(interaction.wait)
cli.add_command(interaction.send)
cli.add_command(cookies.cookies)
cli.add_command(watch.watch)
cli.add_command(watch.control)
cli.add_command(extraction.describe)
cli.add_command(extraction.outline)
cli.add_command(extraction.links)
cli.add_command(extraction.summarize)
cli.add_command(util.info)
cli.add_command(util.repl)
cli.add_command(util.userscript)
cli.add_command(util.download)
cli.add_command(util.highlight)
cli.add_command(server.server)

def main():
    """Entry point for the CLI."""
    cli()

if __name__ == "__main__":
    main()
```

### Phase 5: Update Entry Point

**File:** `setup.py`

Change entry point from:
```python
entry_points={
    'console_scripts': [
        'zen=zen.cli:main',
    ],
},
```

To:
```python
entry_points={
    'console_scripts': [
        'zen=zen.cli:main',
    ],
},
```

(No change needed - `zen.cli` now refers to the package, not the module)

## Refactoring Benefits

### Code Organization
- Clear separation of concerns
- Each module has a single responsibility
- Easy to understand at a glance

### Maintainability
- Easier to locate specific commands
- Simpler to modify or add features
- Reduced cognitive load

### Testing
- Each module can be tested independently
- Mock dependencies easily
- Clear interfaces between modules

### Development Workflow
- Team members can work on different modules
- Reduced merge conflicts
- Better code reviews (smaller diffs)

### Performance
- Lazy loading possible (import on demand)
- Reduced initial import overhead

### Documentation
- Easier to document individual modules
- Clear dependencies listed
- Module-level docstrings

## Testing Strategy

### Unit Tests
Test each module independently:
```
tests/
├── test_exec.py           # eval, exec
├── test_navigation.py     # open, back, forward, reload
├── test_inspection.py     # inspect, inspected, screenshot
├── test_interaction.py    # click, wait, send
├── test_cookies.py        # cookies group
├── test_watch.py          # watch, control
├── test_extraction.py     # describe, outline, links, summarize
├── test_server.py         # server group
├── test_util.py           # info, repl, download, highlight
└── test_base.py           # base utilities
```

### Integration Tests
Test command registration and CLI behavior:
```
tests/
├── test_cli_integration.py  # Command registration, help, version
└── test_cli_e2e.py          # End-to-end with running server
```

## Migration Checklist

- [ ] Create `zen/cli/` directory
- [ ] Create `zen/cli/__init__.py` (empty initially)
- [ ] Create `zen/cli/base.py` - extract utilities
- [ ] Create `zen/cli/exec.py` - eval, exec commands
- [ ] Create `zen/cli/navigation.py` - navigation commands
- [ ] Create `zen/cli/selection.py` - selected command
- [ ] Create `zen/cli/server.py` - server commands
- [ ] Create `zen/cli/inspect.py` - inspect commands
- [ ] Create `zen/cli/interaction.py` - click, wait, send
- [ ] Create `zen/cli/cookies.py` - cookie commands
- [ ] Create `zen/cli/watch.py` - watch and control
- [ ] Create `zen/cli/extraction.py` - content extraction
- [ ] Create `zen/cli/util.py` - utility commands
- [ ] Update `zen/cli/__init__.py` - register all commands
- [ ] Run tests to verify functionality
- [ ] Update documentation
- [ ] Commit changes
- [ ] Remove old `zen/cli.py`

## Risk Mitigation

### Backwards Compatibility
- Command names and options unchanged
- Same help text and behavior
- Same error messages

### Rollback Plan
- Keep original `zen/cli.py` as backup during development
- Create feature branch for refactoring
- Test thoroughly before merging

### Incremental Rollout
- Can merge module by module
- Test each module before moving to next
- Each commit is self-contained

## Timeline Estimate

- Phase 1 (Base module): 2 hours
- Phase 2 (Simple modules): 3 hours
- Phase 3 (Complex modules): 8 hours
- Phase 4 (Package setup): 2 hours
- Phase 5 (Testing): 4 hours
- Total: ~19 hours

## Success Criteria

- [ ] All tests pass
- [ ] CLI functionality unchanged
- [ ] Each module <400 lines
- [ ] Clear import structure
- [ ] Good code organization
- [ ] Easier to maintain
- [ ] Easier to test

