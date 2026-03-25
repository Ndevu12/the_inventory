"""Serializers for dashboard API responses."""

from rest_framework import serializers


class DashboardSummarySerializer(serializers.Serializer):
    total_products = serializers.IntegerField()
    total_locations = serializers.IntegerField()
    active_warehouses = serializers.IntegerField()
    locations_with_warehouse = serializers.IntegerField()
    locations_retail_site = serializers.IntegerField()
    low_stock_count = serializers.IntegerField()
    total_stock_records = serializers.IntegerField()
    total_reserved = serializers.IntegerField()
    total_available = serializers.IntegerField()
    purchase_orders = serializers.IntegerField()
    sales_orders = serializers.IntegerField()
    reserved_stock_value = serializers.CharField()


class ChartDatasetSerializer(serializers.Serializer):
    labels = serializers.ListField(child=serializers.CharField())
    data = serializers.ListField(child=serializers.IntegerField())


class StockBySiteSerializer(serializers.Serializer):
    warehouse_id = serializers.IntegerField(allow_null=True)
    label = serializers.CharField()
    kind = serializers.ChoiceField(choices=["warehouse", "retail_site"])
    total_quantity = serializers.IntegerField()
    reserved = serializers.IntegerField()
    available = serializers.IntegerField()


class StockByLocationSerializer(serializers.Serializer):
    labels = serializers.ListField(child=serializers.CharField())
    data = serializers.ListField(child=serializers.IntegerField())
    reserved = serializers.ListField(child=serializers.IntegerField())
    available = serializers.ListField(child=serializers.IntegerField())
    by_site = StockBySiteSerializer(many=True)


class OrderStatusSerializer(serializers.Serializer):
    purchase_orders = ChartDatasetSerializer()
    sales_orders = ChartDatasetSerializer()


class ReservationBreakdownSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    units = serializers.IntegerField()


class PendingReservationsSerializer(serializers.Serializer):
    reservation_count = serializers.IntegerField()
    total_units = serializers.IntegerField()
    total_value = serializers.FloatField()
    pending = ReservationBreakdownSerializer()
    confirmed = ReservationBreakdownSerializer()


class ExpiringLotItemSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    lot_number = serializers.CharField()
    product_sku = serializers.CharField()
    product_name = serializers.CharField()
    expiry_date = serializers.DateField()
    days_to_expiry = serializers.IntegerField(allow_null=True)
    quantity_remaining = serializers.IntegerField()


class ExpiringLotsSerializer(serializers.Serializer):
    has_lot_data = serializers.BooleanField()
    expiring_lots = ExpiringLotItemSerializer(many=True)
