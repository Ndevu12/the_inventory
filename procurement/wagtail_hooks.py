"""Wagtail hooks for the procurement app.

Registers admin menu items for procurement management.
"""

from django.urls import reverse
from wagtail import hooks
from wagtail.admin.menu import MenuItem


@hooks.register("register_admin_menu_item")
def register_suppliers_menu_item():
    return MenuItem(
        "Suppliers",
        reverse("wagtailadmin_explore_root") + "?model_string=procurement.Supplier",
        icon_name="user",
        order=200,
    )


@hooks.register("register_admin_menu_item")
def register_purchase_orders_menu_item():
    return MenuItem(
        "Purchase Orders",
        reverse("wagtailadmin_explore_root") + "?model_string=procurement.PurchaseOrder",
        icon_name="doc-full-inverse",
        order=210,
    )


@hooks.register("register_admin_menu_item")
def register_grn_menu_item():
    return MenuItem(
        "Goods Received",
        reverse("wagtailadmin_explore_root") + "?model_string=procurement.GoodsReceivedNote",
        icon_name="download",
        order=220,
    )
