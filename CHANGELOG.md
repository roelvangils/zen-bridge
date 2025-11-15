# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Unified Storage Command**: Consolidated cookies, localStorage, and sessionStorage into a single `storage` command
  - Flag-based filtering with `--cookies`, `--local`, `--session`, and `--all` flags
  - Support for multiple storage types in a single command (e.g., `inspekt storage list --cookies --local`)
  - Cookie-specific options: `--secure`, `--max-age`, `--expires`, `--same-site`, `--path`, `--domain`
  - Enhanced JSON output with aggregated totals across all storage types
  - Parallel retrieval of multiple storage types for better performance
  - Comprehensive test suite with 32 integration tests (77% code coverage)
- **Enhanced Cookie Features**:
  - Automatic JSON parsing for cookie values
  - 15 derived properties (time-based, security scores, size metrics)
  - Window message bridge for chrome.cookies API access with fallback to document.cookie
  - Enhanced cookie display with metadata (domain, path, security flags, expiration)
- **Storage API Enhancements**:
  - Unified `/api/storage` endpoint supporting all storage types
  - Cookie support in storage API with full options
  - Backward compatible `type` parameter (marked as deprecated)
  - New `types` parameter for multiple storage types: `GET /api/storage?types=cookies,local,session`

### Deprecated
- **Cookie Commands**: `inspekt cookies` command group deprecated in favor of `inspekt storage --cookies`
  - All cookie commands show deprecation warnings with migration instructions
  - Legacy commands will be removed in v2.0.0
  - Migration guide:
    - `inspekt cookies list` → `inspekt storage list --cookies`
    - `inspekt cookies get <name>` → `inspekt storage get <name> --cookies`
    - `inspekt cookies set <name> <value>` → `inspekt storage set <name> <value> --cookies`
    - `inspekt cookies delete <name>` → `inspekt storage delete <name> --cookies`
    - `inspekt cookies clear` → `inspekt storage clear --cookies`
- **Cookie API Endpoints**: `/api/cookies/*` endpoints deprecated in favor of `/api/storage`
  - HTTP deprecation headers added to all cookie endpoints
  - Sunset date: Wed, 01 Jan 2026 00:00:00 GMT
  - Endpoints remain functional during deprecation period

### Changed
- **Storage Command**: Complete rewrite with unified architecture
  - Uses new `storage_unified.js` script (557 lines) for all storage operations
  - CLI module expanded from 276 to 565 lines with enhanced functionality
  - Improved error handling and user feedback
  - Confirmation prompts for destructive operations (clear)

## [5.0.0] - 2025-01-14

### Changed - BREAKING CHANGES ⚠️

This is a major rebranding release. The project has been renamed from "Zen Browser Bridge" to "Inspekt" (with a k).

#### Package & Installation
- **Python package renamed**: `zen` → `inspekt`
  - All imports must be updated: `from zen.*` → `from inspekt.*`
  - CLI command remains `inspekt` (was already renamed in previous version)
  - Reinstallation required: `pip uninstall zen-bridge && pip install -e .`

#### Configuration
- **Config directory changed**: `~/.zen/` → `~/.inspekt/`
  - Users must manually migrate their configuration files
  - See [MIGRATION.md](MIGRATION.md) for detailed instructions

#### Browser Extensions
- **Firefox extension ID changed**: `zen-bridge@roelvangils.github.io` → `inspekt@roelvangils.github.io`
  - **Action required**: Uninstall old extension and install new version
  - Automatic updates will NOT work for this change
  - Extension name changed to "Inspekt"

- **Chrome extension**: Name updated to "Inspekt"
  - Existing installations will update automatically

#### Userscript
- **Global function renamed**: `zenStore()` → `inspektStore()`
  - Update custom scripts and DevTools workflows
  - Used for capturing inspected elements: `inspektStore($0)`

- **Command reference updated**: `zen inspected` → `inspekt inspected`

- **CSS classes renamed**:
  - `zen-control-styles` → `inspekt-control-styles`
  - `zen-pulse` → `inspekt-pulse`
  - `data-zen-control-focus` → `data-inspekt-control-focus`

#### Documentation & URLs
- **Repository**: Now at `https://github.com/roelvangils/inspekt`
- **Documentation**: Now at `https://roelvangils.github.io/inspekt/`
- **Userscript URLs**: Updated to `inspekt` repository

#### Internal Changes (No Action Required)
- All console log messages updated from "[Zen Bridge]" to "[Inspekt]"
- Internal version constants renamed
- Help text and error messages updated
- Test files and assertions updated
- CI/CD pipeline updated
- All documentation updated

### Migration
See [MIGRATION.md](MIGRATION.md) for complete migration guide with step-by-step instructions.

### Notes
- This is a clean-break release with no backward compatibility
- Version bumped from 4.x.x to 5.0.0 to indicate breaking changes
- Core functionality and APIs remain unchanged
- All features from v4.x.x are preserved

---

## [4.0.0] - Previous Release

*(Previous changelog entries would go here)*
