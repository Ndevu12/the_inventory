"""Base ``AppConfig`` that plugin apps subclass to declare metadata.

Subclassing is optional for the simplest plugins (a plain app with an
``api_register.py`` already works), but :class:`PluginConfig` is what unlocks
dependency declaration, version reporting, and the ``/api/v1/plugins/``
introspection endpoint.

Example::

    # my_plugin/apps.py
    from plugins.base import PluginConfig

    class MyPluginConfig(PluginConfig):
        name = "my_plugin"
        plugin_name = "my_plugin"
        plugin_version = "1.0.0"
        plugin_verbose_name = "Barcode Scanning"
        plugin_description = "Adds barcode lookup endpoints."
        plugin_requires = ["inventory"]  # or ["inventory>=1.0"]
"""

from __future__ import annotations

from django.apps import AppConfig


class PluginConfig(AppConfig):
    """An ``AppConfig`` carrying plugin metadata.

    Defaults are derived from the Django app so a minimal subclass that only
    sets ``name`` still produces a sensible plugin record.
    """

    default_auto_field = "django.db.models.BigAutoField"

    #: Stable, human-meaningful identifier other plugins depend on. Defaults to
    #: the Django app ``label``.
    plugin_name: str = ""
    #: Semantic-ish version string used for dependency specifiers.
    plugin_version: str = "0.0.0"
    #: Friendly name for admin/introspection. Defaults to ``verbose_name``.
    plugin_verbose_name: str = ""
    #: One-line description shown by ``manage.py plugins`` and the API.
    plugin_description: str = ""
    #: Requirement specifiers referencing other plugins' ``plugin_name``,
    #: e.g. ``["inventory", "barcodes>=1.2"]``.
    plugin_requires: list[str] = []

    @property
    def resolved_plugin_name(self) -> str:
        return self.plugin_name or self.label

    @property
    def resolved_verbose_name(self) -> str:
        return self.plugin_verbose_name or str(self.verbose_name)

    def plugin_metadata(self) -> dict:
        """Serialisable record of this plugin, used by introspection tools."""
        return {
            "name": self.resolved_plugin_name,
            "app_label": self.label,
            "version": self.plugin_version,
            "verbose_name": self.resolved_verbose_name,
            "description": self.plugin_description,
            "requires": list(self.plugin_requires),
        }
