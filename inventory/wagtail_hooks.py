"""Wagtail hooks for the inventory app.

Registers admin menu items, URL routes, dashboard panels, and custom CSS
for inventory management and customization.
"""

from django.templatetags.static import static
from django.urls import path, reverse
from wagtail import hooks
from wagtail.admin.menu import MenuItem

from inventory.imports.views import DataImportView
from inventory.panels import (
    LowStockPanel,
    MovementTrendChart,
    OrderStatusChart,
    RecentMovementsPanel,
    StockByLocationChart,
    StockSummaryPanel,
)
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
        path(
            "inventory/import/",
            DataImportView.as_view(),
            name="inventory_import",
        ),
    ]


# Core Inventory Management Items
@hooks.register("register_admin_menu_item")
def register_products_menu_item():
    """Add Products link to the Wagtail admin sidebar."""
    return MenuItem(
        "Products",
        reverse("wagtailadmin_explore_root") + "?model_string=inventory.Product",
        icon_name="form",
        order=100,
    )


@hooks.register("register_admin_menu_item")
def register_categories_menu_item():
    """Add Categories link to the Wagtail admin sidebar."""
    return MenuItem(
        "Categories",
        reverse("wagtailadmin_explore_root") + "?model_string=inventory.Category",
        icon_name="folder-open-1",
        order=110,
    )


@hooks.register("register_admin_menu_item")
def register_product_tags_menu_item():
    """Add Product Tags link to the Wagtail admin sidebar."""
    return MenuItem(
        "Product Tags",
        reverse("wagtailadmin_explore_root") + "?model_string=inventory.ProductTag",
        icon_name="tag",
        order=120,
    )


# Stock Management Items
@hooks.register("register_admin_menu_item")
def register_stock_locations_menu_item():
    """Add Stock Locations link to the Wagtail admin sidebar."""
    return MenuItem(
        "Stock Locations",
        reverse("wagtailadmin_explore_root") + "?model_string=inventory.StockLocation",
        icon_name="site",
        order=130,
    )


@hooks.register("register_admin_menu_item")
def register_stock_records_menu_item():
    """Add Stock Records link to the Wagtail admin sidebar."""
    return MenuItem(
        "Stock Records",
        reverse("wagtailadmin_explore_root") + "?model_string=inventory.StockRecord",
        icon_name="doc-full",
        order=140,
    )


@hooks.register("register_admin_menu_item")
def register_stock_movements_menu_item():
    """Add Stock Movements link to the Wagtail admin sidebar."""
    return MenuItem(
        "Stock Movements",
        reverse("wagtailadmin_explore_root") + "?model_string=inventory.StockMovement",
        icon_name="arrow-right",
        order=150,
    )


# Monitoring & Analytics Items
@hooks.register("register_admin_menu_item")
def register_low_stock_menu_item():
    """Add Low Stock Alerts link to the Wagtail admin sidebar."""
    return MenuItem(
        "Low Stock Alerts",
        reverse("inventory_low_stock"),
        icon_name="warning",
        order=160,
    )


@hooks.register("register_admin_menu_item")
def register_inventory_search_menu_item():
    """Add Inventory Search link to the Wagtail admin sidebar."""
    return MenuItem(
        "Inventory Search",
        reverse("inventory_search"),
        icon_name="search",
        order=170,
    )


@hooks.register("register_admin_menu_item")
def register_import_menu_item():
    """Add Data Import link to the Wagtail admin sidebar."""
    return MenuItem(
        "Import Data",
        reverse("inventory_import"),
        icon_name="upload",
        order=180,
    )


@hooks.register("construct_homepage_panels")
def add_inventory_dashboard_panels(request, panels):
    """Add inventory health panels to the Wagtail admin dashboard."""
    panels.append(StockSummaryPanel())
    panels.append(LowStockPanel())
    panels.append(RecentMovementsPanel())
    panels.append(StockByLocationChart())
    panels.append(MovementTrendChart())
    panels.append(OrderStatusChart())


@hooks.register("insert_global_admin_css")
def register_inventory_admin_css():
    """Register custom CSS for inventory admin styling."""
    return f'<link rel="stylesheet" href="{static("css/inventory-admin.css")}">'
