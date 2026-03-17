"""Wagtail admin integration for platform management.

Registers platform-level dashboard panels and admin CSS.
The Tenants menu item is provided by ``TenantSnippetViewSet``
in ``tenants/snippets.py`` (via ``add_to_admin_menu = True``).
"""

from django.templatetags.static import static
from wagtail import hooks

import tenants.snippets  # noqa: F401 — triggers register_snippet() at startup
from tenants.panels import (
    PlatformOverviewPanel,
    RecentTenantsPanel,
    SubscriptionStatsPanel,
)


@hooks.register("construct_homepage_panels")
def add_platform_dashboard_panels(request, panels):
    """Replace default Wagtail homepage panels with platform management panels."""
    panels.append(PlatformOverviewPanel())
    panels.append(SubscriptionStatsPanel())
    panels.append(RecentTenantsPanel())


@hooks.register("insert_global_admin_css")
def register_platform_admin_css():
    """Register custom CSS for platform admin styling."""
    return f'<link rel="stylesheet" href="{static("css/platform-admin.css")}">'
