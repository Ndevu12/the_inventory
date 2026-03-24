"""Parse OS environment for project settings (URLs, CORS, TTLs, etc.).

Django and Wagtail core structure (INSTALLED_APPS, middleware classes, etc.)
stay in code; tunable deployment values use these helpers.
"""

from __future__ import annotations

import os


def env_str(name: str, default: str = "") -> str:
    v = os.environ.get(name)
    if v is None:
        return default
    return v.strip()


def env_bool(name: str, default: bool = False) -> bool:
    v = os.environ.get(name)
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "on")


def env_int(name: str, default: int) -> int:
    v = os.environ.get(name)
    if v is None or not str(v).strip():
        return default
    try:
        return int(str(v).strip(), 10)
    except ValueError:
        return default


def env_list(name: str, default: list[str] | None = None) -> list[str]:
    """Comma-separated list. Missing key → copy of *default*. Present but empty → []."""
    v = os.environ.get(name)
    if v is None:
        return list(default) if default is not None else []
    parts = [x.strip() for x in v.split(",") if x.strip()]
    if not parts and default is not None:
        return list(default)
    return parts
