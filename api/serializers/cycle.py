"""Serializers for cycle count endpoints."""

from rest_framework import serializers

from inventory.models import Product, StockLocation
from inventory.models.cycle import (
    CycleCountLine,
    InventoryCycle,
    InventoryVariance,
    VarianceResolution,
)


class CycleCountLineSerializer(serializers.ModelSerializer):
    product_sku = serializers.CharField(source="product.sku", read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)
    location_name = serializers.CharField(source="location.name", read_only=True)
    counted_by_username = serializers.CharField(
        source="counted_by.username", read_only=True, default=None,
    )
    variance = serializers.IntegerField(read_only=True)

    class Meta:
        model = CycleCountLine
        fields = [
            "id",
            "cycle",
            "product", "product_sku", "product_name",
            "location", "location_name",
            "system_quantity", "counted_quantity",
            "counted_by", "counted_by_username", "counted_at",
            "variance",
            "notes",
            "created_at", "updated_at",
        ]
        read_only_fields = fields


class InventoryVarianceSerializer(serializers.ModelSerializer):
    product_sku = serializers.CharField(source="product.sku", read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)
    location_name = serializers.CharField(source="location.name", read_only=True)
    variance_type_display = serializers.CharField(
        source="get_variance_type_display", read_only=True,
    )
    resolution_display = serializers.CharField(
        source="get_resolution_display", read_only=True, default=None,
    )
    resolved_by_username = serializers.CharField(
        source="resolved_by.username", read_only=True, default=None,
    )

    class Meta:
        model = InventoryVariance
        fields = [
            "id",
            "cycle", "count_line",
            "product", "product_sku", "product_name",
            "location", "location_name",
            "variance_type", "variance_type_display",
            "system_quantity", "physical_quantity", "variance_quantity",
            "resolution", "resolution_display",
            "adjustment_movement",
            "resolved_by", "resolved_by_username", "resolved_at",
            "root_cause",
            "created_at", "updated_at",
        ]
        read_only_fields = fields


class InventoryCycleSerializer(serializers.ModelSerializer):
    location_name = serializers.CharField(
        source="location.name", read_only=True, default=None,
    )
    status_display = serializers.CharField(
        source="get_status_display", read_only=True,
    )
    started_by_username = serializers.CharField(
        source="started_by.username", read_only=True, default=None,
    )
    total_lines = serializers.SerializerMethodField()
    counted_lines = serializers.SerializerMethodField()

    class Meta:
        model = InventoryCycle
        fields = [
            "id",
            "name",
            "location", "location_name",
            "status", "status_display",
            "scheduled_date",
            "started_at", "completed_at",
            "started_by", "started_by_username",
            "total_lines", "counted_lines",
            "notes",
            "created_at", "updated_at",
        ]
        read_only_fields = fields

    def get_total_lines(self, obj: InventoryCycle) -> int:
        return obj.lines.count()

    def get_counted_lines(self, obj: InventoryCycle) -> int:
        return obj.lines.filter(counted_quantity__isnull=False).count()


class InventoryCycleDetailSerializer(InventoryCycleSerializer):
    lines = CycleCountLineSerializer(many=True, read_only=True)
    variances = InventoryVarianceSerializer(many=True, read_only=True)
    variance_summary = serializers.SerializerMethodField()

    class Meta(InventoryCycleSerializer.Meta):
        fields = InventoryCycleSerializer.Meta.fields + [
            "lines", "variances", "variance_summary",
        ]

    def get_variance_summary(self, obj: InventoryCycle) -> dict:
        from inventory.services.cycle import CycleCountService
        return CycleCountService().get_variance_summary(obj)


class CycleCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    location = serializers.PrimaryKeyRelatedField(
        queryset=StockLocation.objects.all(),
        required=False,
        allow_null=True,
        default=None,
    )
    scheduled_date = serializers.DateField()
    notes = serializers.CharField(required=False, allow_blank=True, default="")


class RecordCountSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    location = serializers.PrimaryKeyRelatedField(queryset=StockLocation.objects.all())
    counted_quantity = serializers.IntegerField(min_value=0)
    notes = serializers.CharField(required=False, allow_blank=True, default="")


class LineResolutionSerializer(serializers.Serializer):
    resolution = serializers.ChoiceField(choices=VarianceResolution.choices)
    root_cause = serializers.CharField(required=False, allow_blank=True, default="")


class ReconcileSerializer(serializers.Serializer):
    resolutions = serializers.DictField(child=LineResolutionSerializer())

    def validate_resolutions(self, value):
        validated = {}
        for line_id_str, resolution_data in value.items():
            try:
                line_id = int(line_id_str)
            except (ValueError, TypeError):
                raise serializers.ValidationError(
                    f"Resolution key '{line_id_str}' must be a valid integer line ID."
                )
            validated[line_id] = resolution_data
        return validated
