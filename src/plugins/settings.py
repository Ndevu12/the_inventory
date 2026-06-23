"""Namespaced settings access for plugins.

Plugins should not scatter top-level Django settings; instead they read from a
single ``PLUGIN_SETTINGS`` dict, namespaced by plugin name::

    # settings/base.py (or via env in production settings)
    PLUGIN_SETTINGS = {
        "barcodes": {"SYMBOLOGY": "ean13", "ENABLED": True},
    }

    # my_plugin/views.py
    from plugins.settings import plugin_setting
    symbology = plugin_setting("barcodes", "SYMBOLOGY", default="code128")
"""

from __future__ import annotations

from typing import Any

from django.conf import settings

_SENTINEL = object()


def plugin_settings(plugin_name: str) -> dict[str, Any]:
    """Return the settings dict for ``plugin_name`` (empty if unconfigured)."""
    return dict(getattr(settings, "PLUGIN_SETTINGS", {}).get(plugin_name, {}))


def plugin_setting(plugin_name: str, key: str, default: Any = None) -> Any:
    """Return a single namespaced setting, falling back to ``default``."""
    value = plugin_settings(plugin_name).get(key, _SENTINEL)
    return default if value is _SENTINEL else value
