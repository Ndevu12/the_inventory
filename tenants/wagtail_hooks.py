"""Wagtail admin integration for tenant management."""

from django.urls import reverse
from wagtail import hooks
from wagtail.admin.menu import MenuItem


@hooks.register("register_admin_menu_item")
def register_tenants_menu():
    return MenuItem(
        "Tenants",
        reverse("admin:tenants_tenant_changelist"),
        icon_name="group",
        order=10000,
    )
