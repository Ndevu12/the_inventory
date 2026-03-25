"""Serializers for stock reservation endpoints."""

from rest_framework import serializers

from inventory.models import Product, StockLocation, StockReservation
from sales.models.order import SalesOrder
from tenants.middleware import get_effective_tenant

from api.serializers.localized_strings import (
    attribute_in_display_locale,
    display_locale_from_context,
)


class StockReservationSerializer(serializers.ModelSerializer):
    """Read serializer — includes nested product, location, and sales order details."""

    product_sku = serializers.CharField(source="product.sku", read_only=True)
    product_name = serializers.SerializerMethodField()
    location_name = serializers.SerializerMethodField()
    sales_order_number = serializers.CharField(
        source="sales_order.order_number", read_only=True, default=None,
    )
    status_display = serializers.CharField(
        source="get_status_display", read_only=True,
    )
    reserved_by_username = serializers.CharField(
        source="reserved_by.username", read_only=True, default=None,
    )
    warehouse_id = serializers.IntegerField(
        source="location.warehouse_id", read_only=True, allow_null=True,
    )
    warehouse_name = serializers.SerializerMethodField()

    class Meta:
        model = StockReservation
        fields = [
            "id",
            "product", "product_sku", "product_name",
            "location", "location_name",
            "warehouse_id", "warehouse_name",
            "quantity",
            "sales_order", "sales_order_number",
            "reserved_by", "reserved_by_username",
            "status", "status_display",
            "expires_at",
            "fulfilled_movement",
            "notes",
            "created_at", "updated_at",
        ]
        read_only_fields = fields

    def get_product_name(self, obj):
        return attribute_in_display_locale(
            obj.product, "name", display_locale_from_context(self.context),
        )

    def get_location_name(self, obj):
        return attribute_in_display_locale(
            obj.location, "name", display_locale_from_context(self.context),
        )

    def get_warehouse_name(self, obj):
        loc = obj.location
        if loc is None or not loc.warehouse_id:
            return None
        return loc.warehouse.name


class StockReservationCreateSerializer(serializers.Serializer):
    """Write serializer — validates inputs for ReservationService.create_reservation."""

    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.none())
    location = serializers.PrimaryKeyRelatedField(queryset=StockLocation.objects.none())
    quantity = serializers.IntegerField(min_value=1)
    sales_order = serializers.PrimaryKeyRelatedField(
        queryset=SalesOrder.objects.none(),
        required=False,
        allow_null=True,
        default=None,
    )
    notes = serializers.CharField(required=False, allow_blank=True, default="")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        tenant = get_effective_tenant(request) if request else None
        if tenant:
            self.fields["product"].queryset = Product.objects.filter(tenant=tenant)
            self.fields["location"].queryset = StockLocation.objects.filter(tenant=tenant)
            self.fields["sales_order"].queryset = SalesOrder.objects.filter(tenant=tenant)
