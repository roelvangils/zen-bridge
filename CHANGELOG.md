# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
