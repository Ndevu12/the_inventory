"""Serializers for cycle count endpoints."""

from rest_framework import serializers

from api.serializers.localized_strings import (
    attribute_in_display_locale,
    display_locale_from_context,
)
from inventory.models import Product, StockLocation, Warehouse
from tenants.middleware import get_effective_tenant
from inventory.models.cycle import (
    CycleCountLine,
    InventoryCycle,
    InventoryVariance,
    VarianceResolution,
)


class CycleCountLineSerializer(serializers.ModelSerializer):
    product_sku = serializers.CharField(source="product.sku", read_only=True)
    product_name = serializers.SerializerMethodField()
    location_name = serializers.SerializerMethodField()
    warehouse_id = serializers.IntegerField(
        source="location.warehouse_id", read_only=True, allow_null=True,
    )
    warehouse_name = serializers.SerializerMethodField()
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
            "warehouse_id", "warehouse_name",
            "system_quantity", "counted_quantity",
            "counted_by", "counted_by_username", "counted_at",
            "variance",
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


class InventoryVarianceSerializer(serializers.ModelSerializer):
    product_sku = serializers.CharField(source="product.sku", read_only=True)
    product_name = serializers.SerializerMethodField()
    location_name = serializers.SerializerMethodField()
    variance_type_display = serializers.CharField(
        source="get_variance_type_display", read_only=True,
    )
    resolution_display = serializers.CharField(
        source="get_resolution_display", read_only=True, default=None,
    )
    resolved_by_username = serializers.CharField(
        source="resolved_by.username", read_only=True, default=None,
    )
    warehouse_id = serializers.IntegerField(
        source="location.warehouse_id", read_only=True, allow_null=True,
    )
    warehouse_name = serializers.SerializerMethodField()

    class Meta:
        model = InventoryVariance
        fields = [
            "id",
            "cycle", "count_line",
            "product", "product_sku", "product_name",
            "location", "location_name",
            "warehouse_id", "warehouse_name",
            "variance_type", "variance_type_display",
            "system_quantity", "physical_quantity", "variance_quantity",
            "resolution", "resolution_display",
            "adjustment_movement",
            "resolved_by", "resolved_by_username", "resolved_at",
            "root_cause",
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


class InventoryCycleSerializer(serializers.ModelSerializer):
    location_name = serializers.SerializerMethodField()
    warehouse_id = serializers.SerializerMethodField()
    warehouse_name = serializers.SerializerMethodField()
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
            "warehouse_id", "warehouse_name",
            "status", "status_display",
            "scheduled_date",
            "started_at", "completed_at",
            "started_by", "started_by_username",
            "total_lines", "counted_lines",
            "notes",
            "created_at", "updated_at",
        ]
        read_only_fields = fields

    def get_location_name(self, obj: InventoryCycle):
        loc = obj.location
        if loc is None:
            return None
        return attribute_in_display_locale(
            loc, "name", display_locale_from_context(self.context),
        )

    def get_warehouse_id(self, obj: InventoryCycle):
        if obj.location_id:
            return obj.location.warehouse_id
        return None

    def get_warehouse_name(self, obj: InventoryCycle):
        if obj.location_id and obj.location.warehouse_id:
            return obj.location.warehouse.name
        return None

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
    warehouse = serializers.PrimaryKeyRelatedField(
        queryset=Warehouse.objects.all(),
        required=False,
        allow_null=True,
        default=None,
    )
    scheduled_date = serializers.DateField()
    notes = serializers.CharField(required=False, allow_blank=True, default="")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        tenant = get_effective_tenant(request) if request else None
        if tenant:
            self.fields["location"].queryset = StockLocation.objects.filter(tenant=tenant)
            self.fields["warehouse"].queryset = Warehouse.objects.filter(tenant=tenant)

    def validate(self, attrs):
        location = attrs.get("location")
        warehouse = attrs.get("warehouse")
        if location is not None and warehouse is not None:
            lw = location.warehouse_id
            if lw != warehouse.pk:
                raise serializers.ValidationError(
                    {
                        "warehouse": (
                            "Must match the selected location's warehouse "
                            "(or omit warehouse when using location)."
                        ),
                    },
                )
        return attrs


class RecordCountSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    location = serializers.PrimaryKeyRelatedField(queryset=StockLocation.objects.all())
    counted_quantity = serializers.IntegerField(min_value=0)
    notes = serializers.CharField(required=False, allow_blank=True, default="")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        tenant = get_effective_tenant(request) if request else None
        if tenant:
            self.fields["product"].queryset = Product.objects.filter(tenant=tenant)
            self.fields["location"].queryset = StockLocation.objects.filter(tenant=tenant)


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
