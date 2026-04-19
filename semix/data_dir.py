"""User-data directory resolution.

Follows XDG on Linux, Application Support on macOS, and %LOCALAPPDATA% on
Windows. The user can override with ``SEMIX_DATA_DIR``.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

_APP = "semix"


def data_dir() -> Path:
    """The root data directory for this package (created if missing)."""
    override = os.environ.get("SEMIX_DATA_DIR")
    if override:
        p = Path(override).expanduser()
    elif sys.platform == "darwin":
        p = Path.home() / "Library" / "Application Support" / _APP
    elif os.name == "nt":
        p = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / _APP
    else:
        xdg = os.environ.get("XDG_DATA_HOME")
        p = Path(xdg).expanduser() if xdg else Path.home() / ".local" / "share" / _APP
    p.mkdir(parents=True, exist_ok=True)
    return p


def cache_dir() -> Path:
    """Subdirectory for downloaded source archives."""
    p = data_dir() / "cache"
    p.mkdir(parents=True, exist_ok=True)
    return p
