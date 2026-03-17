"""Django admin configuration for the sales app.

Customer is managed via Wagtail snippets.  Sales orders, line items,
and dispatches are configured here for the Django admin.
"""

from django.contrib import admin

from .models import Dispatch, SalesOrder, SalesOrderLine


class SalesOrderLineInline(admin.TabularInline):
    model = SalesOrderLine
    extra = 1
    fields = ("product", "quantity", "unit_price")


@admin.register(SalesOrder)
class SalesOrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_number",
        "get_customer_name",
        "status",
        "order_date",
    )
    list_filter = ("status", "order_date", "customer")
    search_fields = ("order_number", "customer__name", "customer__code")
    readonly_fields = ("created_at", "updated_at", "created_by")
    inlines = [SalesOrderLineInline]

    fieldsets = (
        ("Order Details", {
            "fields": (
                "order_number",
                "customer",
                "status",
                "order_date",
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

    def get_customer_name(self, obj):
        return obj.customer.name
    get_customer_name.short_description = "Customer"

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Dispatch)
class DispatchAdmin(admin.ModelAdmin):
    list_display = (
        "dispatch_number",
        "get_so_number",
        "dispatch_date",
        "get_location_name",
        "is_processed",
    )
    list_filter = ("is_processed", "dispatch_date")
    search_fields = (
        "dispatch_number",
        "sales_order__order_number",
    )
    readonly_fields = ("is_processed", "created_at", "updated_at", "created_by")

    fieldsets = (
        ("Dispatch Details", {
            "fields": (
                "dispatch_number",
                "sales_order",
                "dispatch_date",
                "from_location",
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

    def get_so_number(self, obj):
        return obj.sales_order.order_number
    get_so_number.short_description = "Sales Order"

    def get_location_name(self, obj):
        return obj.from_location.name
    get_location_name.short_description = "From Location"

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
