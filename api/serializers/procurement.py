"""Serializers for procurement models."""

from rest_framework import serializers

from procurement.models import (
    GoodsReceivedNote,
    PurchaseOrder,
    PurchaseOrderLine,
    Supplier,
)


class SupplierSerializer(serializers.ModelSerializer):
    payment_terms_display = serializers.CharField(
        source="get_payment_terms_display", read_only=True,
    )

    class Meta:
        model = Supplier
        fields = [
            "id", "code", "name", "contact_name", "email", "phone",
            "address", "lead_time_days", "payment_terms",
            "payment_terms_display", "is_active", "notes",
            "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class PurchaseOrderLineSerializer(serializers.ModelSerializer):
    product_sku = serializers.CharField(source="product.sku", read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)
    line_total = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True,
    )

    class Meta:
        model = PurchaseOrderLine
        fields = [
            "id", "purchase_order", "product", "product_sku",
            "product_name", "quantity", "unit_cost", "line_total",
        ]
        read_only_fields = ["id"]


class PurchaseOrderSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(
        source="supplier.name", read_only=True,
    )
    status_display = serializers.CharField(
        source="get_status_display", read_only=True,
    )
    lines = PurchaseOrderLineSerializer(many=True, read_only=True)
    total_cost = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True,
    )

    class Meta:
        model = PurchaseOrder
        fields = [
            "id", "order_number", "supplier", "supplier_name",
            "status", "status_display", "order_date",
            "expected_delivery_date", "notes", "lines", "total_cost",
            "created_at", "updated_at",
        ]
        read_only_fields = ["status", "created_at", "updated_at"]


class GoodsReceivedNoteSerializer(serializers.ModelSerializer):
    purchase_order_number = serializers.CharField(
        source="purchase_order.order_number", read_only=True,
    )
    location_name = serializers.CharField(
        source="location.name", read_only=True,
    )

    class Meta:
        model = GoodsReceivedNote
        fields = [
            "id", "grn_number", "purchase_order",
            "purchase_order_number", "received_date",
            "location", "location_name", "notes", "is_processed",
            "created_at", "updated_at",
        ]
        read_only_fields = ["is_processed", "created_at", "updated_at"]
