"""Serializers for sales models."""

from rest_framework import serializers

from sales.models import (
    Customer,
    Dispatch,
    SalesOrder,
    SalesOrderLine,
)


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = [
            "id", "code", "name", "contact_name", "email", "phone",
            "address", "is_active", "notes",
            "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class SalesOrderLineSerializer(serializers.ModelSerializer):
    product_sku = serializers.CharField(source="product.sku", read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)
    line_total = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True,
    )

    class Meta:
        model = SalesOrderLine
        fields = [
            "id", "sales_order", "product", "product_sku",
            "product_name", "quantity", "unit_price", "line_total",
        ]
        read_only_fields = ["id"]


class SalesOrderSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(
        source="customer.name", read_only=True,
    )
    status_display = serializers.CharField(
        source="get_status_display", read_only=True,
    )
    lines = SalesOrderLineSerializer(many=True, read_only=True)
    total_price = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True,
    )

    class Meta:
        model = SalesOrder
        fields = [
            "id", "order_number", "customer", "customer_name",
            "status", "status_display", "order_date", "notes",
            "lines", "total_price",
            "created_at", "updated_at",
        ]
        read_only_fields = ["status", "created_at", "updated_at"]


class DispatchSerializer(serializers.ModelSerializer):
    sales_order_number = serializers.CharField(
        source="sales_order.order_number", read_only=True,
    )
    from_location_name = serializers.CharField(
        source="from_location.name", read_only=True,
    )

    class Meta:
        model = Dispatch
        fields = [
            "id", "dispatch_number", "sales_order",
            "sales_order_number", "dispatch_date",
            "from_location", "from_location_name",
            "notes", "is_processed",
            "created_at", "updated_at",
        ]
        read_only_fields = ["is_processed", "created_at", "updated_at"]
