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


class PlatformAuditLogSerializer(ComplianceAuditLogSerializer):
    """Platform-wide audit log serializer with tenant info (superuser only)."""

    tenant_name = serializers.CharField(
        source="tenant.name", read_only=True,
    )
    tenant_slug = serializers.CharField(
        source="tenant.slug", read_only=True,
    )
    object_type = serializers.SerializerMethodField()
    object_id = serializers.SerializerMethodField()

    class Meta(ComplianceAuditLogSerializer.Meta):
        fields = list(ComplianceAuditLogSerializer.Meta.fields) + [
            "tenant_name",
            "tenant_slug",
            "object_type",
            "object_id",
        ]
        read_only_fields = fields

    def get_object_type(self, obj):
        """Derive object type from associated entity (e.g. product, general)."""
        if obj.product_id:
            return "product"
        if obj.details and isinstance(obj.details, dict) and "object_type" in obj.details:
            return obj.details["object_type"]
        return "general"

    def get_object_id(self, obj):
        """Return primary object id when applicable (e.g. product_id)."""
        if obj.product_id:
            return str(obj.product_id)
        if obj.details and isinstance(obj.details, dict):
            for key in ("object_id", "cycle_id", "reservation_id", "lot_id"):
                if obj.details.get(key) is not None:
                    return str(obj.details[key])
        return ""
