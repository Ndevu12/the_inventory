"""Runtime plugin registry: enumerate loaded plugins and validate dependencies.

Unlike :mod:`plugins.discovery` (which runs at settings-load time to decide
*which* apps to install), this module operates on the populated Django app
registry.  It answers "which installed apps are plugins?" and "are their
declared dependencies satisfied?".
"""

from __future__ import annotations

from django.apps import apps
from django.core.exceptions import ImproperlyConfigured

from plugins.base import PluginConfig
from plugins.versioning import parse_requirement, satisfies


def get_plugin_configs() -> list[PluginConfig]:
    """Return every installed app whose ``AppConfig`` is a :class:`PluginConfig`."""
    return [cfg for cfg in apps.get_app_configs() if isinstance(cfg, PluginConfig)]


def get_loaded_plugins() -> list[dict]:
    """Serialisable metadata for every loaded plugin, sorted by name."""
    return sorted(
        (cfg.plugin_metadata() for cfg in get_plugin_configs()),
        key=lambda meta: meta["name"],
    )


def validate_plugins() -> None:
    """Validate every plugin's declared dependencies.

    Raises :class:`~django.core.exceptions.ImproperlyConfigured` if a required
    plugin is missing or installed at an incompatible version. Called from
    :meth:`plugins.apps.PluginsConfig.ready` so configuration errors surface at
    startup rather than at first request.
    """
    by_name = {cfg.resolved_plugin_name: cfg for cfg in get_plugin_configs()}

    for cfg in get_plugin_configs():
        for spec in cfg.plugin_requires:
            name, operator, target = parse_requirement(spec)
            required = by_name.get(name)
            if required is None:
                raise ImproperlyConfigured(
                    f"Plugin {cfg.resolved_plugin_name!r} requires plugin "
                    f"{name!r}, which is not installed."
                )
            if operator and not satisfies(required.plugin_version, operator, target):
                raise ImproperlyConfigured(
                    f"Plugin {cfg.resolved_plugin_name!r} requires "
                    f"{spec!r}, but {name!r} is at version "
                    f"{required.plugin_version}."
                )
