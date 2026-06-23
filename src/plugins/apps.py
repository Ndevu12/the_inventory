"""App config for the plugin framework itself.

On startup it auto-discovers every installed app's ``api_register`` module (the
same pattern Wagtail uses for ``wagtail_hooks`` and Celery for ``tasks``) so
plugins can populate the shared API registry, then validates plugin
dependencies. This runs during app population, before the URLconf is imported,
so ``api/urls.py`` sees a fully populated registry.
"""

from __future__ import annotations

from django.apps import AppConfig
from django.utils.module_loading import autodiscover_modules


class PluginsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "plugins"
    verbose_name = "Plugins"

    def ready(self) -> None:
        # Import each app's ``api_register`` module so its module-level
        # ``registry.register_*`` calls run. Missing modules are ignored.
        autodiscover_modules("api_register")

        # Fail fast on unsatisfied plugin dependencies.
        from plugins.manager import validate_plugins

        validate_plugins()
