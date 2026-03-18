"""Serializers for stock reservation endpoints."""

from rest_framework import serializers

from inventory.models import Product, StockLocation, StockReservation
from sales.models.order import SalesOrder


class StockReservationSerializer(serializers.ModelSerializer):
    """Read serializer — includes nested product, location, and sales order details."""

    product_sku = serializers.CharField(source="product.sku", read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)
    location_name = serializers.CharField(source="location.name", read_only=True)
    sales_order_number = serializers.CharField(
        source="sales_order.order_number", read_only=True, default=None,
    )
    status_display = serializers.CharField(
        source="get_status_display", read_only=True,
    )
    reserved_by_username = serializers.CharField(
        source="reserved_by.username", read_only=True, default=None,
    )

    class Meta:
        model = StockReservation
        fields = [
            "id",
            "product", "product_sku", "product_name",
            "location", "location_name",
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


class StockReservationCreateSerializer(serializers.Serializer):
    """Write serializer — validates inputs for ReservationService.create_reservation."""

    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    location = serializers.PrimaryKeyRelatedField(queryset=StockLocation.objects.all())
    quantity = serializers.IntegerField(min_value=1)
    sales_order = serializers.PrimaryKeyRelatedField(
        queryset=SalesOrder.objects.all(),
        required=False,
        allow_null=True,
        default=None,
    )
    notes = serializers.CharField(required=False, allow_blank=True, default="")
