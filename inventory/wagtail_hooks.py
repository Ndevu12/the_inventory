"""Wagtail hooks for the inventory app.

Registers admin menu items and URL routes for custom inventory views.
"""

from django.urls import path, reverse
from wagtail import hooks
from wagtail.admin.menu import MenuItem

from inventory.views import LowStockAlertView


@hooks.register("register_admin_urls")
def register_inventory_admin_urls():
    """Register custom inventory URLs under the Wagtail admin."""
    return [
        path(
            "inventory/low-stock/",
            LowStockAlertView.as_view(),
            name="inventory_low_stock",
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
