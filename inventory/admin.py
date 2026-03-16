"""Django admin configuration for the inventory app.

Configures list displays, filters, and admin interface for
inventory models that aren't managed through Wagtail snippets.
"""

from django.contrib import admin
from .models import StockRecord, StockMovement


@admin.register(StockRecord)
class StockRecordAdmin(admin.ModelAdmin):
    """Admin interface for StockRecord."""

    list_display = (
        "get_product_sku",
        "get_product_name",
        "get_location_name",
        "quantity",
        "is_low_stock",
    )
    list_filter = (
        "product__category",
        "location",
        "product__is_active",
    )
    search_fields = (
        "product__sku",
        "product__name",
        "location__name",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
        "created_by",
    )

    fieldsets = (
        ("Product & Location", {
            "fields": ("product", "location", "quantity"),
            "description": "Link this product to a location with its current stock level.",
        }),
        ("Audit Trail", {
            "fields": ("created_at", "updated_at", "created_by"),
            "classes": ("collapse",),
        }),
    )

    def get_product_sku(self, obj):
        """Display product SKU in list."""
        return obj.product.sku
    get_product_sku.short_description = "SKU"

    def get_product_name(self, obj):
        """Display product name in list."""
        return obj.product.name
    get_product_name.short_description = "Product Name"

    def get_location_name(self, obj):
        """Display location name in list."""
        return obj.location.name
    get_location_name.short_description = "Location"


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    """Admin interface for StockMovement (immutable audit log)."""

    list_display = (
        "reference",
        "get_product_sku",
        "movement_type",
        "quantity",
        "created_at",
    )
    list_filter = (
        "movement_type",
        "created_at",
        "product__category",
    )
    search_fields = (
        "product__sku",
        "product__name",
        "reference",
        "notes",
    )
    readonly_fields = (
        "product",
        "movement_type",
        "quantity",
        "from_location",
        "to_location",
        "unit_cost",
        "reference",
        "notes",
        "created_at",
        "updated_at",
        "created_by",
    )

    fieldsets = (
        ("Movement Details", {
            "fields": (
                "reference",
                "movement_type",
                "product",
            ),
            "description": "Immutable movement record. These fields cannot be changed.",
        }),
        ("Movement Locations", {
            "fields": (
                "from_location",
                "to_location",
                "quantity",
            ),
        }),
        ("Additional Information", {
            "fields": (
                "unit_cost",
                "notes",
            ),
        }),
        ("Audit Trail", {
            "fields": (
                "created_at",
                "updated_at",
                "created_by",
            ),
            "classes": ("collapse",),
        }),
    )

    def get_product_sku(self, obj):
        """Display product SKU in list."""
        return obj.product.sku
    get_product_sku.short_description = "SKU"

    def has_add_permission(self, request):
        """Movements should only be created through the service layer."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Movements are immutable and cannot be deleted."""
        return False

    def has_change_permission(self, request, obj=None):
        """Movements are immutable and cannot be changed."""
        return False
