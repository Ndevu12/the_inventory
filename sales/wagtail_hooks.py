"""Wagtail hooks for the sales app.

Registers admin menu items for sales management.
"""

from django.urls import reverse
from wagtail import hooks
from wagtail.admin.menu import MenuItem


@hooks.register("register_admin_menu_item")
def register_customers_menu_item():
    return MenuItem(
        "Customers",
        reverse("wagtailadmin_explore_root") + "?model_string=sales.Customer",
        icon_name="group",
        order=300,
    )


@hooks.register("register_admin_menu_item")
def register_sales_orders_menu_item():
    return MenuItem(
        "Sales Orders",
        reverse("wagtailadmin_explore_root") + "?model_string=sales.SalesOrder",
        icon_name="doc-full-inverse",
        order=310,
    )


@hooks.register("register_admin_menu_item")
def register_dispatches_menu_item():
    return MenuItem(
        "Dispatches",
        reverse("wagtailadmin_explore_root") + "?model_string=sales.Dispatch",
        icon_name="upload",
        order=320,
    )
