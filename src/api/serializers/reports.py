"""Serializers for report API responses."""

from rest_framework import serializers


class StockValuationItemSerializer(serializers.Serializer):
    sku = serializers.CharField()
    product_name = serializers.CharField()
    category = serializers.CharField(allow_null=True)
    total_quantity = serializers.IntegerField()
    unit_cost = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_value = serializers.DecimalField(max_digits=14, decimal_places=2)
    method = serializers.CharField()


class StockValuationResponseSerializer(serializers.Serializer):
    method = serializers.CharField()
    total_products = serializers.IntegerField()
    total_quantity = serializers.IntegerField()
    total_value = serializers.DecimalField(max_digits=14, decimal_places=2)
    items = StockValuationItemSerializer(many=True)


class MovementHistoryItemSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    product_sku = serializers.CharField()
    product_name = serializers.CharField()
    movement_type = serializers.CharField()
    quantity = serializers.IntegerField()
    unit_cost = serializers.DecimalField(max_digits=12, decimal_places=2, allow_null=True)
    from_location = serializers.CharField(allow_null=True)
    to_location = serializers.CharField(allow_null=True)
    reference = serializers.CharField(allow_blank=True)
    created_at = serializers.DateTimeField()
    created_by = serializers.CharField(allow_null=True)


class LowStockItemSerializer(serializers.Serializer):
    sku = serializers.CharField()
    product_name = serializers.CharField()
    category = serializers.CharField(allow_null=True)
    reorder_point = serializers.IntegerField()
    total_stock = serializers.IntegerField()
    deficit = serializers.IntegerField()


class OverstockItemSerializer(serializers.Serializer):
    sku = serializers.CharField()
    product_name = serializers.CharField()
    category = serializers.CharField(allow_null=True)
    reorder_point = serializers.IntegerField()
    total_stock = serializers.IntegerField()
    threshold = serializers.IntegerField()
    excess = serializers.IntegerField()


class PeriodSummaryItemSerializer(serializers.Serializer):
    period = serializers.DateField()
    order_count = serializers.IntegerField()
    total = serializers.DecimalField(max_digits=14, decimal_places=2)
