"""Read-only serializer for the compliance audit log."""

from rest_framework import serializers

from inventory.models import ComplianceAuditLog


class ComplianceAuditLogSerializer(serializers.ModelSerializer):
    action_display = serializers.CharField(
        source="get_action_display", read_only=True,
    )
    product_sku = serializers.CharField(
        source="product.sku", read_only=True, default=None,
    )
    product_name = serializers.CharField(
        source="product.name", read_only=True, default=None,
    )
    username = serializers.CharField(
        source="user.username", read_only=True, default=None,
    )

    class Meta:
        model = ComplianceAuditLog
        fields = [
            "id",
            "tenant",
            "action",
            "action_display",
            "product",
            "product_sku",
            "product_name",
            "user",
            "username",
            "timestamp",
            "ip_address",
            "details",
        ]
        read_only_fields = fields
