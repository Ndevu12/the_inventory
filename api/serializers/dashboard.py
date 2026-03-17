"""Serializers for dashboard API responses."""

from rest_framework import serializers


class DashboardSummarySerializer(serializers.Serializer):
    total_products = serializers.IntegerField()
    total_locations = serializers.IntegerField()
    low_stock_count = serializers.IntegerField()
    total_stock_records = serializers.IntegerField()
    purchase_orders = serializers.IntegerField()
    sales_orders = serializers.IntegerField()


class ChartDatasetSerializer(serializers.Serializer):
    labels = serializers.ListField(child=serializers.CharField())
    data = serializers.ListField(child=serializers.IntegerField())


class OrderStatusSerializer(serializers.Serializer):
    purchase_orders = ChartDatasetSerializer()
    sales_orders = ChartDatasetSerializer()
