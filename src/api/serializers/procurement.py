"""Serializers for procurement models."""

import uuid

from rest_framework import serializers

from procurement.models import (
    GoodsReceivedNote,
    PurchaseOrder,
    PurchaseOrderLine,
    Supplier,
)

from api.serializers.localized_strings import (
    attribute_in_display_locale,
    display_locale_from_context,
)
from tenants.middleware import get_effective_tenant

from api.serializers.translatable_representation import TranslatableRepresentationMixin
from api.serializers.translatable_writable import TranslatableWritableMixin


class SupplierSerializer(
    TranslatableWritableMixin,
    TranslatableRepresentationMixin,
    serializers.ModelSerializer,
):
    """Translatable: ``name``, ``contact_name``, ``address``, ``notes``."""

    translatable_overlay_fields = ("name", "contact_name", "address", "notes")
    payment_terms_display = serializers.CharField(
        source="get_payment_terms_display", read_only=True,
    )

    class Meta:
        model = Supplier
        fields = [
            "id", "code", "name", "contact_name", "email", "phone",
            "address", "lead_time_days", "payment_terms",
            "payment_terms_display", "is_active", "notes",
            "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def validate_code(self, value):
        request = self.context.get("request")
        tenant = self.context.get("tenant") or (
            get_effective_tenant(request) if request else None
        )
        loc = self.context.get("wagtail_write_locale")
        qs = Supplier.objects.filter(code=value)
        if tenant:
            qs = qs.filter(tenant=tenant)
        if loc:
            qs = qs.filter(locale_id=loc.id)
        qs = self._same_translation_group_qs(qs, self.instance)
        if qs.exists():
            raise serializers.ValidationError(
                "A supplier with this code already exists for this tenant."
            )
        return value


class PurchaseOrderLineSerializer(serializers.ModelSerializer):
    """``product_name`` uses the request display locale for translated catalog products."""

    product_sku = serializers.CharField(source="product.sku", read_only=True)
    product_name = serializers.SerializerMethodField()
    line_total = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True,
    )

    class Meta:
        model = PurchaseOrderLine
        fields = [
            "id", "purchase_order", "product", "product_sku",
            "product_name", "quantity", "unit_cost", "line_total",
        ]
        read_only_fields = ["id"]

    def get_product_name(self, obj):
        return attribute_in_display_locale(
            obj.product, "name", display_locale_from_context(self.context),
        )


class PurchaseOrderLineWriteSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(
        queryset=PurchaseOrderLine._meta.get_field("product").related_model.objects.all(),
    )
    quantity = serializers.IntegerField(min_value=1)
    unit_cost = serializers.DecimalField(max_digits=10, decimal_places=2)


class PurchaseOrderSerializer(serializers.ModelSerializer):
    """``supplier_name`` uses the request display locale for translated suppliers."""

    supplier_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(
        source="get_status_display", read_only=True,
    )
    lines = PurchaseOrderLineSerializer(many=True, read_only=True)
    total_cost = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True,
    )

    class Meta:
        model = PurchaseOrder
        fields = [
            "id", "order_number", "supplier", "supplier_name",
            "status", "status_display", "order_date",
            "expected_delivery_date", "notes", "lines", "total_cost",
            "created_at", "updated_at",
        ]
        read_only_fields = ["status", "created_at", "updated_at"]
        extra_kwargs = {
            "order_number": {"required": False, "allow_blank": True},
        }

    def get_supplier_name(self, obj):
        return attribute_in_display_locale(
            obj.supplier, "name", display_locale_from_context(self.context),
        )

    def create(self, validated_data):
        lines_raw = self.initial_data.get("lines", [])
        line_serializer = PurchaseOrderLineWriteSerializer(data=lines_raw, many=True)
        line_serializer.is_valid(raise_exception=True)
        if not line_serializer.validated_data:
            raise serializers.ValidationError(
                {"lines": ["At least one line item is required."]},
            )

        order_number = validated_data.get("order_number")
        if order_number is None or not str(order_number).strip():
            validated_data["order_number"] = f"PO-{uuid.uuid4().hex[:10].upper()}"
        else:
            validated_data["order_number"] = str(order_number).strip()

        order = PurchaseOrder.objects.create(**validated_data)
        for line in line_serializer.validated_data:
            PurchaseOrderLine.objects.create(purchase_order=order, **line)
        return order


class GoodsReceivedNoteSerializer(serializers.ModelSerializer):
    purchase_order_number = serializers.CharField(
        source="purchase_order.order_number", read_only=True,
    )
    location_name = serializers.CharField(
        source="location.name", read_only=True,
    )
    warehouse_id = serializers.IntegerField(
        source="location.warehouse_id", read_only=True, allow_null=True,
    )
    warehouse_name = serializers.SerializerMethodField()

    class Meta:
        model = GoodsReceivedNote
        fields = [
            "id", "grn_number", "purchase_order",
            "purchase_order_number", "received_date",
            "location", "location_name",
            "warehouse_id", "warehouse_name",
            "notes", "is_processed",
            "created_at", "updated_at",
        ]
        read_only_fields = ["is_processed", "created_at", "updated_at"]

    def get_warehouse_name(self, obj):
        loc = obj.location
        if loc is None or not loc.warehouse_id:
            return None
        return loc.warehouse.name
