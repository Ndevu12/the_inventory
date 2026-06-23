"""Register the framework's own API routes.

This dogfoods the plugin contribution mechanism: the ``/api/v1/plugins/``
endpoint is wired through the same registry that third-party plugins use,
rather than being hard-coded in ``api/urls.py``.
"""

from __future__ import annotations

from django.urls import path

from plugins.registry import registry
from plugins.views import InstalledPluginsView

registry.register_route(
    path("plugins/", InstalledPluginsView.as_view(), name="api-plugins"),
    source="plugins",
)
