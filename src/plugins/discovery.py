"""Settings-time discovery of plugin apps to add to ``INSTALLED_APPS``.

This runs while ``settings/base.py`` is importing, *before* Django's app
registry exists, so it must not touch ``django.apps``.  It only resolves the
list of app paths to install, from two sources:

* the ``PLUGINS`` environment variable — a comma-separated list of dotted app
  paths (handy for in-tree/local plugins during development);
* the ``the_inventory.plugins`` entry-point group — populated by pip-installed
  distributions, each pointing at a Django app (its ``apps.py`` config path or
  package path).

Order is preserved and duplicates / already-installed apps are dropped.
"""

from __future__ import annotations

import os
from importlib.metadata import entry_points

ENTRY_POINT_GROUP = "the_inventory.plugins"


def _env_plugin_apps() -> list[str]:
    raw = os.environ.get("PLUGINS", "")
    return [item.strip() for item in raw.split(",") if item.strip()]


def _entry_point_plugin_apps() -> list[str]:
    apps: list[str] = []
    try:
        eps = entry_points(group=ENTRY_POINT_GROUP)
    except TypeError:  # pragma: no cover - very old importlib.metadata
        eps = entry_points().get(ENTRY_POINT_GROUP, [])  # type: ignore[attr-defined]
    for ep in eps:
        # The entry-point value is the dotted app path to install.
        apps.append(ep.value)
    return apps


def discover_plugin_apps(already_installed: list[str] | tuple[str, ...] = ()) -> list[str]:
    """Return plugin app paths to append to ``INSTALLED_APPS``.

    ``already_installed`` lets the caller pass the core ``INSTALLED_APPS`` so
    apps listed there are not added twice.
    """
    seen = set(already_installed)
    resolved: list[str] = []
    for app in _env_plugin_apps() + _entry_point_plugin_apps():
        if app in seen:
            continue
        seen.add(app)
        resolved.append(app)
    return resolved
