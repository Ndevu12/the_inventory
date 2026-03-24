"""Wagtail admin integration for platform management.

Registers platform-level dashboard panels and admin CSS.
The Tenants menu item is provided by ``TenantSnippetViewSet``
in ``tenants/snippets.py`` (via ``add_to_admin_menu = True``).
"""

from urllib.parse import urlencode

from django.templatetags.static import static
from django.urls import reverse
from wagtail import hooks
from wagtail.admin.widgets.button import Button

import tenants.snippets  # noqa: F401 — triggers register_snippet() at startup
from tenants.models import Tenant
from tenants.panels import (
    PlatformOverviewPanel,
    RecentTenantsPanel,
    SubscriptionStatsPanel,
)


@hooks.register("register_snippet_listing_buttons")
def add_tenant_oversight_buttons(snippet, user, next_url=None):
    """Add Force deactivate / Reactivate buttons for Tenant (superusers only)."""
    if not isinstance(snippet, Tenant) or not (user.is_authenticated and user.is_superuser):
        return
    viewset = getattr(Tenant, "snippet_viewset", None)
    if not viewset:
        return

    def _url(name):
        path = reverse(viewset.get_url_name(name), args=[snippet.pk])
        if next_url:
            path += "?" + urlencode({"next": next_url})
        return path

    if snippet.is_active:
        yield Button(
            label="Force deactivate",
            url=_url("deactivate"),
            icon_name="cross",
            classname="button-secondary",
            priority=50,
        )
    else:
        yield Button(
            label="Reactivate",
            url=_url("reactivate"),
            icon_name="tick",
            classname="button-secondary",
            priority=50,
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
