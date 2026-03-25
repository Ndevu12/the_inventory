"""Serializers for bulk stock operations API endpoints."""

from rest_framework import serializers

from inventory.models import StockLocation
from inventory.utils.warehouse_scope import (
    WAREHOUSE_SCOPE_UNSPECIFIED,
    parse_report_warehouse_scope,
)
from tenants.middleware import get_effective_tenant


# ---------------------------------------------------------------------------
# Shared response serializer
# ---------------------------------------------------------------------------


class BulkItemErrorSerializer(serializers.Serializer):
    index = serializers.IntegerField()
    product_id = serializers.IntegerField()
    error = serializers.CharField()


class BulkItemResultSerializer(serializers.Serializer):
    index = serializers.IntegerField()
    product_id = serializers.IntegerField()
    status = serializers.CharField()


class BulkOperationResultSerializer(serializers.Serializer):
    success_count = serializers.IntegerField()
    failure_count = serializers.IntegerField()
    total_count = serializers.IntegerField()
    errors = BulkItemErrorSerializer(many=True)
    results = BulkItemResultSerializer(many=True)


# ---------------------------------------------------------------------------
# Bulk Transfer
# ---------------------------------------------------------------------------


class BulkTransferItemSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1)


class BulkTransferSerializer(serializers.Serializer):
    """Payload for ``POST /api/v1/bulk-operations/transfer/``."""

    items = BulkTransferItemSerializer(many=True, min_length=1)
    from_location = serializers.PrimaryKeyRelatedField(
        queryset=StockLocation.objects.none(),
    )
    to_location = serializers.PrimaryKeyRelatedField(
        queryset=StockLocation.objects.none(),
    )
    warehouse_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        write_only=True,
        help_text="When set, only locations in this facility are valid. JSON null means retail-only locations.",
    )
    retail_locations_only = serializers.BooleanField(
        required=False,
        default=False,
        write_only=True,
    )
    reference = serializers.CharField(
        required=False, allow_blank=True, default="",
    )
    notes = serializers.CharField(
        required=False, allow_blank=True, default="",
    )
    fail_fast = serializers.BooleanField(required=False, default=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        tenant = get_effective_tenant(request) if request else None
        data = kwargs.get("data")
        loc_qs = StockLocation.objects.none()
        if tenant:
            loc_qs = StockLocation.objects.filter(tenant=tenant)
            if isinstance(data, dict):
                try:
                    scope, wid = parse_report_warehouse_scope(
                        warehouse_id=data.get("warehouse_id", WAREHOUSE_SCOPE_UNSPECIFIED),
                        retail_locations_only=bool(data.get("retail_locations_only")),
                    )
                except ValueError:
                    scope = "all"
                if scope == "retail":
                    loc_qs = loc_qs.filter(warehouse_id__isnull=True)
                elif scope == "facility":
                    loc_qs = loc_qs.filter(warehouse_id=wid)
        self.fields["from_location"].queryset = loc_qs
        self.fields["to_location"].queryset = loc_qs

    def validate(self, attrs):
        wh_raw = attrs.pop("warehouse_id", WAREHOUSE_SCOPE_UNSPECIFIED)
        retail = attrs.pop("retail_locations_only", False)
        try:
            scope, wid = parse_report_warehouse_scope(
                warehouse_id=wh_raw,
                retail_locations_only=retail,
            )
        except ValueError as exc:
            raise serializers.ValidationError(str(exc)) from exc

        from_loc = attrs["from_location"]
        to_loc = attrs["to_location"]
        if scope != "all":
            for label, loc in (("from_location", from_loc), ("to_location", to_loc)):
                if scope == "retail" and loc.warehouse_id is not None:
                    raise serializers.ValidationError({
                        label: "Location is not in the retail-only warehouse scope.",
                    })
                if scope == "facility" and loc.warehouse_id != wid:
                    raise serializers.ValidationError({
                        label: "Location does not belong to the requested warehouse.",
                    })

        if from_loc == to_loc:
            raise serializers.ValidationError({
                "to_location": "Source and destination must be different.",
            })
        if not attrs.get("items"):
            raise serializers.ValidationError({
                "items": "At least one item is required.",
            })
        return attrs


# ---------------------------------------------------------------------------
# Bulk Adjustment
# ---------------------------------------------------------------------------


class BulkAdjustmentItemSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(min_value=1)
    new_quantity = serializers.IntegerField(min_value=0)


class BulkAdjustmentSerializer(serializers.Serializer):
    """Payload for ``POST /api/v1/bulk-operations/adjust/``."""

    items = BulkAdjustmentItemSerializer(many=True, min_length=1)
    location = serializers.PrimaryKeyRelatedField(
        queryset=StockLocation.objects.none(),
    )
    warehouse_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        write_only=True,
    )
    retail_locations_only = serializers.BooleanField(
        required=False,
        default=False,
        write_only=True,
    )
    notes = serializers.CharField(
        required=False, allow_blank=True, default="",
    )
    fail_fast = serializers.BooleanField(required=False, default=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        tenant = get_effective_tenant(request) if request else None
        data = kwargs.get("data")
        loc_qs = StockLocation.objects.none()
        if tenant:
            loc_qs = StockLocation.objects.filter(tenant=tenant)
            if isinstance(data, dict):
                try:
                    scope, wid = parse_report_warehouse_scope(
                        warehouse_id=data.get("warehouse_id", WAREHOUSE_SCOPE_UNSPECIFIED),
                        retail_locations_only=bool(data.get("retail_locations_only")),
                    )
                except ValueError:
                    scope = "all"
                if scope == "retail":
                    loc_qs = loc_qs.filter(warehouse_id__isnull=True)
                elif scope == "facility":
                    loc_qs = loc_qs.filter(warehouse_id=wid)
        self.fields["location"].queryset = loc_qs

    def validate(self, attrs):
        wh_raw = attrs.pop("warehouse_id", WAREHOUSE_SCOPE_UNSPECIFIED)
        retail = attrs.pop("retail_locations_only", False)
        try:
            scope, wid = parse_report_warehouse_scope(
                warehouse_id=wh_raw,
                retail_locations_only=retail,
            )
        except ValueError as exc:
            raise serializers.ValidationError(
                "Invalid warehouse scope parameters."
            ) from exc
        loc = attrs["location"]
        if scope != "all":
            if scope == "retail" and loc.warehouse_id is not None:
                raise serializers.ValidationError({
                    "location": "Location is not in the retail-only warehouse scope.",
                })
            if scope == "facility" and loc.warehouse_id != wid:
                raise serializers.ValidationError({
                    "location": "Location does not belong to the requested warehouse.",
                })
        return attrs

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("At least one item is required.")
        return value


# ---------------------------------------------------------------------------
# Bulk Revalue
# ---------------------------------------------------------------------------


class BulkRevalueItemSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(min_value=1)
    new_unit_cost = serializers.DecimalField(
        max_digits=10, decimal_places=2, min_value=0,
    )


class BulkRevalueSerializer(serializers.Serializer):
    """Payload for ``POST /api/v1/bulk-operations/revalue/``."""

    items = BulkRevalueItemSerializer(many=True, min_length=1)
    fail_fast = serializers.BooleanField(required=False, default=False)

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("At least one item is required.")
        return value
