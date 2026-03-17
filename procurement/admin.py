"""Django admin configuration for the procurement app.

Supplier is managed via Wagtail snippets.  Purchase orders, line items,
and goods received notes are configured here for the Django admin.
"""

from django.contrib import admin

from .models import GoodsReceivedNote, PurchaseOrder, PurchaseOrderLine


class PurchaseOrderLineInline(admin.TabularInline):
    model = PurchaseOrderLine
    extra = 1
    fields = ("product", "quantity", "unit_cost")


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_number",
        "get_supplier_name",
        "status",
        "order_date",
        "expected_delivery_date",
    )
    list_filter = ("status", "order_date", "supplier")
    search_fields = ("order_number", "supplier__name", "supplier__code")
    readonly_fields = ("created_at", "updated_at", "created_by")
    inlines = [PurchaseOrderLineInline]

    fieldsets = (
        ("Order Details", {
            "fields": (
                "order_number",
                "supplier",
                "status",
                "order_date",
                "expected_delivery_date",
            ),
        }),
        ("Notes", {
            "fields": ("notes",),
        }),
        ("Audit Trail", {
            "fields": ("created_at", "updated_at", "created_by"),
            "classes": ("collapse",),
        }),
    )

    def get_supplier_name(self, obj):
        return obj.supplier.name
    get_supplier_name.short_description = "Supplier"

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(GoodsReceivedNote)
class GoodsReceivedNoteAdmin(admin.ModelAdmin):
    list_display = (
        "grn_number",
        "get_po_number",
        "received_date",
        "get_location_name",
        "is_processed",
    )
    list_filter = ("is_processed", "received_date")
    search_fields = (
        "grn_number",
        "purchase_order__order_number",
    )
    readonly_fields = ("is_processed", "created_at", "updated_at", "created_by")

    fieldsets = (
        ("GRN Details", {
            "fields": (
                "grn_number",
                "purchase_order",
                "received_date",
                "location",
            ),
        }),
        ("Notes", {
            "fields": ("notes",),
        }),
        ("Processing", {
            "fields": ("is_processed",),
        }),
        ("Audit Trail", {
            "fields": ("created_at", "updated_at", "created_by"),
            "classes": ("collapse",),
        }),
    )

    def get_po_number(self, obj):
        return obj.purchase_order.order_number
    get_po_number.short_description = "Purchase Order"

    def get_location_name(self, obj):
        return obj.location.name
    get_location_name.short_description = "Location"

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
