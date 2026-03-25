"""Serializers for sales models."""

import uuid

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


def _derived_warehouse_from_sales_order(sales_order):
    """Derive facility warehouse from dispatches when unambiguous.

    Returns ``(warehouse_pk, warehouse_name)``. ``SalesOrder`` has no direct
    location FK; dispatches carry ``from_location``. If there are no
    dispatches, or locations span more than one facility warehouse, or mix
    retail-only locations with a facility, returns ``(None, None)``.
    """
    warehouse_ids = []
    for dispatch in sales_order.dispatches.all():
        loc = dispatch.from_location
        if loc is None:
            continue
        warehouse_ids.append(loc.warehouse_id)
    if not warehouse_ids:
        return None, None
    distinct = set(warehouse_ids)
    if distinct == {None}:
        return None, None
    if None in distinct or len(distinct) > 1:
        return None, None
    wid = distinct.pop()
    for dispatch in sales_order.dispatches.all():
        loc = dispatch.from_location
        if loc is not None and loc.warehouse_id == wid:
            return wid, loc.warehouse.name
    return None, None


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
        extra_kwargs = {
            "code": {"required": False, "allow_blank": True},
        }

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if self.instance is not None and "code" in attrs:
            raw = attrs.get("code")
            if raw is not None and str(raw).strip() == "":
                attrs.pop("code")
        return attrs

    def validate_code(self, value):
        if value is None or (isinstance(value, str) and not str(value).strip()):
            return value
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

    def create(self, validated_data):
        raw = validated_data.get("code")
        if raw is None or not str(raw).strip():
            validated_data["code"] = f"C-{uuid.uuid4().hex[:10].upper()}"
        else:
            validated_data["code"] = str(raw).strip()
        return super().create(validated_data)

    def update(self, instance, validated_data):
        raw = validated_data.get("code", None)
        if raw is not None:
            if not str(raw).strip():
                validated_data.pop("code", None)
            else:
                validated_data["code"] = str(raw).strip()
        return super().update(instance, validated_data)


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
    warehouse_id = serializers.SerializerMethodField()
    warehouse_name = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._sales_order_warehouse_cache = {}

    def _cached_derived_warehouse(self, obj):
        key = obj.pk if obj.pk is not None else id(obj)
        if key not in self._sales_order_warehouse_cache:
            self._sales_order_warehouse_cache[key] = _derived_warehouse_from_sales_order(
                obj,
            )
        return self._sales_order_warehouse_cache[key]

    class Meta:
        model = SalesOrder
        fields = [
            "id", "order_number", "customer", "customer_name",
            "status", "status_display", "order_date", "notes",
            "lines", "total_price", "can_fulfill",
            "warehouse_id", "warehouse_name",
            "created_at", "updated_at",
        ]
        read_only_fields = ["status", "created_at", "updated_at"]
        extra_kwargs = {
            "order_number": {"required": False, "allow_blank": True},
        }

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

    def get_warehouse_id(self, obj):
        wid, _ = self._cached_derived_warehouse(obj)
        return wid

    def get_warehouse_name(self, obj):
        _, name = self._cached_derived_warehouse(obj)
        return name

    def create(self, validated_data):
        lines_data = self.initial_data.get("lines", [])
        line_serializer = SalesOrderLineWriteSerializer(data=lines_data, many=True)
        line_serializer.is_valid(raise_exception=True)
        if not line_serializer.validated_data:
            raise serializers.ValidationError(
                {"lines": ["At least one line item is required."]},
            )

        order_number = validated_data.get("order_number")
        if order_number is None or not str(order_number).strip():
            validated_data["order_number"] = f"SO-{uuid.uuid4().hex[:10].upper()}"
        else:
            validated_data["order_number"] = str(order_number).strip()

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
    warehouse_id = serializers.IntegerField(
        source="from_location.warehouse_id", read_only=True, allow_null=True,
    )
    warehouse_name = serializers.SerializerMethodField()

    class Meta:
        model = Dispatch
        fields = [
            "id", "dispatch_number", "sales_order",
            "sales_order_number", "dispatch_date",
            "from_location", "from_location_name",
            "warehouse_id", "warehouse_name",
            "notes", "is_processed",
            "created_at", "updated_at",
        ]
        read_only_fields = ["is_processed", "created_at", "updated_at"]
        extra_kwargs = {
            "dispatch_number": {"required": False, "allow_blank": True},
        }

    def get_warehouse_name(self, obj):
        loc = obj.from_location
        if loc is None or not loc.warehouse_id:
            return None
        return loc.warehouse.name

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if self.instance is not None and "dispatch_number" in attrs:
            raw = attrs.get("dispatch_number")
            if raw is not None and str(raw).strip() == "":
                attrs.pop("dispatch_number")
        return attrs

    def create(self, validated_data):
        raw = validated_data.get("dispatch_number")
        if raw is None or not str(raw).strip():
            validated_data["dispatch_number"] = f"DSP-{uuid.uuid4().hex[:10].upper()}"
        else:
            validated_data["dispatch_number"] = str(raw).strip()
        return super().create(validated_data)

    def update(self, instance, validated_data):
        raw = validated_data.get("dispatch_number", None)
        if raw is not None:
            if not str(raw).strip():
                validated_data.pop("dispatch_number", None)
            else:
                validated_data["dispatch_number"] = str(raw).strip()
        return super().update(instance, validated_data)
