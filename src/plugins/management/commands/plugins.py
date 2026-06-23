"""``manage.py plugins`` — list loaded plugins and their API contributions."""

from __future__ import annotations

from django.core.management.base import BaseCommand

from plugins.manager import get_loaded_plugins
from plugins.registry import registry


class Command(BaseCommand):
    help = "List installed plugins, their versions, dependencies, and API routes."

    def handle(self, *args, **options):
        plugins = get_loaded_plugins()
        if not plugins:
            self.stdout.write("No plugins installed.")
        else:
            self.stdout.write(self.style.MIGRATE_HEADING(f"Loaded plugins ({len(plugins)}):"))
            for meta in plugins:
                requires = ", ".join(meta["requires"]) or "—"
                self.stdout.write(
                    f"  {meta['name']} {meta['version']}"
                    f"  (app: {meta['app_label']}, requires: {requires})"
                )
                if meta["description"]:
                    self.stdout.write(f"      {meta['description']}")

        contributions = registry.contributions()
        viewsets, routes = contributions["viewsets"], contributions["routes"]
        if viewsets or routes:
            self.stdout.write("")
            self.stdout.write(self.style.MIGRATE_HEADING("Registered API contributions:"))
            for vs in viewsets:
                self.stdout.write(
                    f"  [viewset/{vs['scope']}] {vs['prefix']} "
                    f"(basename={vs['basename']}, source={vs['source']})"
                )
            for route in routes:
                self.stdout.write(f"  [route] {route['pattern']} (source={route['source']})")
