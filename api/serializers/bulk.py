"""Serializers for bulk stock operations API endpoints."""

from rest_framework import serializers

from inventory.models import StockLocation


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
        queryset=StockLocation.objects.all(),
    )
    to_location = serializers.PrimaryKeyRelatedField(
        queryset=StockLocation.objects.all(),
    )
    reference = serializers.CharField(
        required=False, allow_blank=True, default="",
    )
    notes = serializers.CharField(
        required=False, allow_blank=True, default="",
    )
    fail_fast = serializers.BooleanField(required=False, default=False)

    def validate(self, attrs):
        if attrs["from_location"] == attrs["to_location"]:
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
        queryset=StockLocation.objects.all(),
    )
    notes = serializers.CharField(
        required=False, allow_blank=True, default="",
    )
    fail_fast = serializers.BooleanField(required=False, default=False)

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
