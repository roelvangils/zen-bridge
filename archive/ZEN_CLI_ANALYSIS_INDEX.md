# ZEN CLI ANALYSIS - COMPLETE INDEX

This directory contains comprehensive documentation of the zen/cli.py file structure for refactoring.

## Documents Overview

### 1. ZEN_CLI_SUMMARY.txt
**Best for:** Quick overview and executive summary  
**Contents:**
- File statistics (4,093 lines, 42 commands)
- Command breakdown by 11 categories
- Shared utilities listing
- Dependency analysis
- Proposed refactoring structure (8-11 modules)
- Key statistics and patterns
- Error handling overview
- Usage examples by category

**Read first if:** You want a quick understanding of the entire structure

---

### 2. ZEN_CLI_STRUCTURE.md
**Best for:** Deep structural analysis  
**Contents:**
- Detailed command categorization with line numbers
- Shared utilities (format_output, get_ai_language, CustomGroup)
- Command dependencies and relationships
- Proposed modular architecture
- Import analysis
- Command line patterns (6 patterns identified)
- Error handling patterns

**Read when:** You need to understand how commands relate to each other

---

### 3. ZEN_CLI_COMMANDS.md
**Best for:** Command reference and implementation details  
**Contents:**
- Complete command summary table (42 commands)
- Detailed breakdown by module
- Usage examples for each command
- Options and arguments
- Helper functions and scripts
- Execution flow patterns (6 patterns)
- Module dependencies

**Read when:** You need to understand a specific command or module

---

### 4. ZEN_CLI_REFACTORING_PLAN.md
**Best for:** Implementation roadmap  
**Contents:**
- Current vs. target state analysis
- Step-by-step refactoring phases (5 phases)
- Module structure with dependencies
- Code examples for new package structure
- Testing strategy
- Migration checklist
- Risk mitigation
- Timeline estimate (~19 hours)
- Success criteria

**Read when:** You're ready to execute the refactoring

---

## Quick Reference: Command Categories

### By Functional Group

**Execution (2 commands)**
- eval, exec

**Navigation (7 commands)**
- open, back, forward, reload + 3 hidden aliases

**Inspection (3 commands)**
- inspect, inspected, screenshot

**Interaction (8 commands)**
- click, double-click, right-click, wait, send + 2 aliases

**Cookies (6 commands)**
- cookies (group) + list, get, set, delete, clear

**Selection (1 command)**
- selected

**Watch & Control (3 commands)**
- watch (group) + input, all; control

**Content Extraction (4 commands)**
- describe, outline, links, summarize

**Server (4 commands)**
- server (group) + start, status, stop

**Utilities (5 commands)**
- info, repl, userscript, download, highlight

---

## Quick Reference: Line Numbers

| Command | Line | Type |
|---------|------|------|
| eval | 145 | Execution |
| exec | 202 | Execution |
| info | 426 | Utility |
| server (group) | 1407 | Server |
| server start | 1415 | Server |
| server status | 1456 | Server |
| server stop | 1475 | Server |
| repl | 1482 | Utility |
| highlight | 1538 | Utility |
| userscript | 1607 | Utility |
| download | 1635 | Utility |
| send | 1893 | Interaction |
| inspect | 1961 | Inspection |
| inspected | 2030 | Inspection |
| click | 2194 | Interaction |
| double-click | 2214 | Interaction |
| right-click | 2237 | Interaction |
| wait | 2317 | Interaction |
| open | 2425 | Navigation |
| back | 2507 | Navigation |
| forward | 2544 | Navigation |
| reload | 2582 | Navigation |
| cookies (group) | 2639 | Cookies |
| cookies list | 2645 | Cookies |
| cookies get | 2657 | Cookies |
| cookies set | 2680 | Cookies |
| cookies delete | 2706 | Cookies |
| cookies clear | 2717 | Cookies |
| selected | 2807 | Selection |
| screenshot | 2909 | Inspection |
| watch (group) | 2998 | Watch |
| watch input | 3004 | Watch |
| control | 3087 | Control |
| watch all | 3347 | Watch |
| describe | 3448 | Extraction |
| outline | 3558 | Extraction |
| links | 3792 | Extraction |
| summarize | 3960 | Extraction |

---

## Quick Reference: Helper Functions

| Function | Line | Purpose |
|----------|------|---------|
| format_output() | 25 | Output formatting |
| get_ai_language() | 48 | Language detection |
| _perform_click() | 2258 | Click abstraction |
| _execute_cookie_action() | 2727 | Cookie operations |
| _enrich_link_metadata() | 3625 | Link metadata |
| _enrich_external_links() | 3733 | Parallel enrichment |
| _get_domain_metrics() | 225 | Domain analysis |
| _get_response_headers() | 340 | HTTP headers |
| _get_robots_txt() | 369 | Robots.txt parsing |

---

## Key Findings

### 1. High Reusability
- `format_output()` - Used by 3+ commands
- `get_ai_language()` - Used by 2 commands
- Helper functions reduce code duplication

### 2. Clear Patterns
- Standard browser command pattern (20+ commands)
- Group + subcommands pattern (4 groups)
- Polling loops (watch, control)
- Script template injection (8 commands)
- AI integration (describe, summarize)
- Alias/delegation (previous, next, refresh)

### 3. Script Dependencies
- 14 helper scripts in zen/scripts/
- Unchanged by refactoring
- Used by 20+ commands

### 4. External Tools Required
- mods: AI operations
- curl: HTTP metadata
- say: macOS accessibility

### 5. Error Handling
- Consistent pattern across all commands
- Server availability check
- Exception handling (ConnectionError, TimeoutError, RuntimeError)

---

## Proposed Module Structure

```
zen/cli/
├── __init__.py              # Entry point, command registration
├── base.py (~150)           # Shared utilities
├── exec.py (~100)           # eval, exec
├── navigation.py (~150)     # open, back, forward, reload
├── selection.py (~80)       # selected
├── server.py (~100)         # server group + subcommands
├── inspect.py (~150)        # inspect, inspected, screenshot
├── interaction.py (~200)    # click*, wait, send
├── cookies.py (~180)        # cookies group + 5 subcommands
├── watch.py (~250)          # watch group + control
├── extraction.py (~400)     # describe, outline, links, summarize
└── util.py (~250)           # info, repl, userscript, download, highlight
```

**Total:** ~2,080 lines across 12 modules (vs. 4,093 in monolith)

---

## Refactoring Priority

### Priority 1 (Critical Path)
1. `base.py` - Foundation for all modules
2. `exec.py` - Simplest to refactor
3. `navigation.py` - Simple and isolated

### Priority 2 (Medium Complexity)
4. `inspection.py` - Related commands
5. `cookies.py` - Self-contained group
6. `selection.py` - Simple and isolated
7. `server.py` - Self-contained group

### Priority 3 (High Complexity)
8. `interaction.py` - Uses shared helper
9. `watch.py` - Complex control logic
10. `extraction.py` - Largest module
11. `util.py` - Mixed utilities

### Final Step
12. `__init__.py` - Command registration

---

## Dependencies Summary

### Imports used by all modules
- click (CLI framework)
- json (formatting)
- sys (exit codes)
- BridgeClient (from zen.client)
- zen.config (configuration)

### Module-specific imports
See individual module documentation in ZEN_CLI_COMMANDS.md

### External tools
- mods: describe, summarize
- curl: link enrichment
- say: control command accessibility

---

## Testing Approach

### Unit Tests (per module)
- test_exec.py
- test_navigation.py
- test_inspection.py
- test_interaction.py
- test_cookies.py
- test_watch.py
- test_extraction.py
- test_server.py
- test_util.py
- test_base.py

### Integration Tests
- test_cli_integration.py (command registration)
- test_cli_e2e.py (end-to-end)

### Backwards Compatibility
- All command names unchanged
- All options unchanged
- All outputs unchanged

---

## Using These Documents

### For Refactoring
1. Start with ZEN_CLI_SUMMARY.txt for overview
2. Read ZEN_CLI_STRUCTURE.md for architecture
3. Use ZEN_CLI_COMMANDS.md for implementation details
4. Follow ZEN_CLI_REFACTORING_PLAN.md for execution

### For Understanding Commands
1. Use this index to find line numbers
2. Refer to ZEN_CLI_COMMANDS.md for command details
3. Check ZEN_CLI_STRUCTURE.md for dependencies

### For Maintenance
1. Keep this index updated after refactoring
2. Update module documentation as changes are made
3. Maintain consistency with helper scripts

---

## Statistics

| Metric | Count |
|--------|-------|
| Total commands | 42 |
| Top-level commands | 30 |
| Subcommands | 12 |
| Command groups | 4 |
| Hidden/alias commands | 4 |
| Helper functions | 9 |
| Helper scripts | 14 |
| Current lines | 4,093 |
| Proposed lines | ~2,080 |
| Modules | 12 |
| Avg. lines per module | ~173 |
| Max lines per module | ~400 |

---

## Next Steps

1. Read ZEN_CLI_SUMMARY.txt for context
2. Review ZEN_CLI_STRUCTURE.md for architecture
3. Examine ZEN_CLI_COMMANDS.md for implementation
4. Follow ZEN_CLI_REFACTORING_PLAN.md for execution

Good luck with the refactoring!

