"""Read-only serializer for the compliance audit log."""

from rest_framework import serializers

from inventory.audit_display import build_audit_summary, event_scope_for_action
from inventory.models import ComplianceAuditLog

from api.serializers.localized_strings import (
    attribute_in_display_locale,
    display_locale_from_context,
)


class ComplianceAuditLogSerializer(serializers.ModelSerializer):
    action_display = serializers.CharField(
        source="get_action_display", read_only=True,
    )
    product_sku = serializers.CharField(
        source="product.sku", read_only=True, default=None,
    )
    product_name = serializers.SerializerMethodField()
    username = serializers.CharField(
        source="user.username", read_only=True, default=None,
    )
    event_scope = serializers.SerializerMethodField()
    summary = serializers.SerializerMethodField()

    class Meta:
        model = ComplianceAuditLog
        fields = [
            "id",
            "tenant",
            "action",
            "action_display",
            "event_scope",
            "summary",
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

    def get_event_scope(self, obj):
        return event_scope_for_action(obj.action)

    def get_summary(self, obj):
        return build_audit_summary(obj)

    def get_product_name(self, obj):
        if not obj.product_id:
            return None
        return attribute_in_display_locale(
            obj.product, "name", display_locale_from_context(self.context),
        )


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
