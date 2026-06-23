"""Register the hello plugin's API route.

Auto-discovered at startup by ``plugins.apps.PluginsConfig.ready`` (only when
this app is in ``INSTALLED_APPS``, i.e. when ``PLUGINS`` includes it).
"""

from __future__ import annotations

from django.urls import path

from plugins.examples.hello.views import HelloView
from plugins.registry import registry

registry.register_route(
    path("hello/", HelloView.as_view(), name="api-hello"),
    source="hello",
)
