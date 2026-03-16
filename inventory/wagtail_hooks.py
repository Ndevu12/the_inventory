"""Wagtail hooks for the inventory app.

Registers admin menu items, URL routes, dashboard panels, and custom CSS
for inventory management and customization.
"""

from django.templatetags.static import static
from django.urls import path, reverse
from wagtail import hooks
from wagtail.admin.menu import MenuItem

from inventory.panels import LowStockPanel, RecentMovementsPanel, StockSummaryPanel
from inventory.views import InventorySearchView, LowStockAlertView


@hooks.register("register_admin_urls")
def register_inventory_admin_urls():
    """Register custom inventory URLs under the Wagtail admin."""
    return [
        path(
            "inventory/low-stock/",
            LowStockAlertView.as_view(),
            name="inventory_low_stock",
        ),
        path(
            "inventory/search/",
            InventorySearchView.as_view(),
            name="inventory_search",
        ),
    ]


@hooks.register("register_admin_menu_item")
def register_low_stock_menu_item():
    """Add a 'Low Stock Alerts' link to the Wagtail admin sidebar."""
    return MenuItem(
        "Low Stock",
        reverse("inventory_low_stock"),
        icon_name="warning",
        order=900,
    )


@hooks.register("register_admin_menu_item")
def register_inventory_search_menu_item():
    """Add an 'Inventory Search' link to the Wagtail admin sidebar."""
    return MenuItem(
        "Inventory Search",
        reverse("inventory_search"),
        icon_name="search",
        order=850,
    )


@hooks.register("construct_homepage_panels")
def add_inventory_dashboard_panels(request, panels):
    """Add inventory health panels to the Wagtail admin dashboard."""
    panels.append(StockSummaryPanel())
    panels.append(LowStockPanel())
    panels.append(RecentMovementsPanel())


@hooks.register("insert_global_admin_css")
def register_inventory_admin_css():
    """Register custom CSS for inventory admin styling."""
    return f'<link rel="stylesheet" href="{static("css/inventory-admin.css")}">'
