"""Pytest configuration and shared fixtures."""

from pathlib import Path

import pytest


@pytest.fixture
def project_root():
    """Return the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def scripts_dir(project_root):
    """Return the scripts directory."""
    return project_root / "inspekt" / "scripts"


@pytest.fixture
def sample_config():
    """Return a sample configuration dictionary."""
    return {
        "ai-language": "en",
        "control": {
            "auto-refocus": "only-spa",
            "focus-outline": "custom",
            "speak-name": False,
            "speak-all": True,
            "announce-role": False,
            "announce-on-page-load": False,
            "navigation-wrap": True,
            "scroll-on-focus": True,
            "click-delay": 0,
            "focus-color": "#0066ff",
            "focus-size": 3,
            "focus-animation": True,
            "focus-glow": True,
            "sound-on-focus": "none",
            "selector-strategy": "id-first",
            "refocus-timeout": 2000,
            "verbose": True,
            "verbose-logging": False,
        },
    }
