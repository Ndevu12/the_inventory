"""Serializers for sales models."""

from rest_framework import serializers

from inventory.models import StockRecord
from sales.models import (
    Customer,
    Dispatch,
    SalesOrder,
    SalesOrderLine,
)

from api.serializers.localized_strings import (
    attribute_in_display_locale,
    display_locale_from_context,
)
from tenants.middleware import get_effective_tenant

from api.serializers.translatable_representation import TranslatableRepresentationMixin
from api.serializers.translatable_writable import TranslatableWritableMixin


class CustomerSerializer(
    TranslatableWritableMixin,
    TranslatableRepresentationMixin,
    serializers.ModelSerializer,
):
    """Translatable: ``name``, ``contact_name``, ``address``, ``notes``."""

    translatable_overlay_fields = ("name", "contact_name", "address", "notes")

    class Meta:
        model = Customer
        fields = [
            "id", "code", "name", "contact_name", "email", "phone",
            "address", "is_active", "notes",
            "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def validate_code(self, value):
        request = self.context.get("request")
        tenant = self.context.get("tenant") or (
            get_effective_tenant(request) if request else None
        )
        loc = self.context.get("wagtail_write_locale")
        qs = Customer.objects.filter(code=value)
        if tenant:
            qs = qs.filter(tenant=tenant)
        if loc:
            qs = qs.filter(locale_id=loc.id)
        qs = self._same_translation_group_qs(qs, self.instance)
        if qs.exists():
            raise serializers.ValidationError(
                "A customer with this code already exists for this tenant."
            )
        return value


class SalesOrderLineSerializer(serializers.ModelSerializer):
    """``product_name`` uses the request display locale for translated catalog products."""

    product_sku = serializers.CharField(source="product.sku", read_only=True)
    product_name = serializers.SerializerMethodField()
    line_total = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True,
    )

    class Meta:
        model = SalesOrderLine
        fields = [
            "id", "sales_order", "product", "product_sku",
            "product_name", "quantity", "unit_price", "line_total",
        ]
        read_only_fields = ["id"]

    def get_product_name(self, obj):
        return attribute_in_display_locale(
            obj.product, "name", display_locale_from_context(self.context),
        )


class SalesOrderLineWriteSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(
        queryset=SalesOrderLine._meta.get_field("product").related_model.objects.all(),
    )
    quantity = serializers.IntegerField(min_value=1)
    unit_price = serializers.DecimalField(max_digits=12, decimal_places=2)


class SalesOrderSerializer(serializers.ModelSerializer):
    """``customer_name`` uses the request display locale for translated customers."""

    customer_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(
        source="get_status_display", read_only=True,
    )
    lines = SalesOrderLineSerializer(many=True, read_only=True)
    total_price = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True,
    )
    can_fulfill = serializers.SerializerMethodField()

    class Meta:
        model = SalesOrder
        fields = [
            "id", "order_number", "customer", "customer_name",
            "status", "status_display", "order_date", "notes",
            "lines", "total_price", "can_fulfill",
            "created_at", "updated_at",
        ]
        read_only_fields = ["status", "created_at", "updated_at"]

    def get_customer_name(self, obj):
        return attribute_in_display_locale(
            obj.customer, "name", display_locale_from_context(self.context),
        )

    def get_can_fulfill(self, obj):
        """True when every order line can be met by available stock across all locations."""
        for line in obj.lines.select_related("product").all():
            total_available = sum(
                sr.available_quantity
                for sr in StockRecord.objects.filter(product=line.product)
            )
            if total_available < line.quantity:
                return False
        return True

    def create(self, validated_data):
        lines_data = self.initial_data.get("lines", [])
        line_serializer = SalesOrderLineWriteSerializer(data=lines_data, many=True)
        line_serializer.is_valid(raise_exception=True)

        order = SalesOrder.objects.create(**validated_data)
        for line in line_serializer.validated_data:
            SalesOrderLine.objects.create(sales_order=order, **line)
        return order


class DispatchSerializer(serializers.ModelSerializer):
    sales_order_number = serializers.CharField(
        source="sales_order.order_number", read_only=True,
    )
    from_location_name = serializers.CharField(
        source="from_location.name", read_only=True,
    )

    class Meta:
        model = Dispatch
        fields = [
            "id", "dispatch_number", "sales_order",
            "sales_order_number", "dispatch_date",
            "from_location", "from_location_name",
            "notes", "is_processed",
            "created_at", "updated_at",
        ]
        read_only_fields = ["is_processed", "created_at", "updated_at"]
