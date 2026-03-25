"""Serializers for inventory models."""

from rest_framework import serializers

from inventory.models import (
    Category,
    MovementType,
    Product,
    StockLocation,
    StockLot,
    StockMovement,
    StockMovementLot,
    StockRecord,
    Warehouse,
)
from inventory.models.reservation import AllocationStrategy
from tenants.middleware import get_effective_tenant

from api.serializers.localized_strings import (
    attribute_in_display_locale,
    display_locale_from_context,
)
from api.serializers.translatable_representation import TranslatableRepresentationMixin
from api.serializers.translatable_writable import TranslatableWritableMixin


class CategorySerializer(
    TranslatableWritableMixin,
    TranslatableRepresentationMixin,
    serializers.ModelSerializer,
):
    """Translatable (per Wagtail locale): ``name``, ``slug``, ``description``."""

    translatable_overlay_fields = ("name", "slug", "description")

    class Meta:
        model = Category
        fields = [
            "id", "name", "slug", "description", "is_active",
            "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def _create_canonical_row(self, validated_data):
        tenant = validated_data.pop("tenant")
        created_by = validated_data.pop("created_by", None)
        loc = validated_data.pop("locale")
        return Category.add_root(
            tenant=tenant,
            created_by=created_by,
            locale=loc,
            **validated_data,
        )

    def validate_slug(self, value):
        request = self.context.get("request")
        tenant = self.context.get("tenant") or (
            get_effective_tenant(request) if request else None
        )
        loc = self.context.get("wagtail_write_locale")
        qs = Category.objects.filter(slug=value)
        if tenant:
            qs = qs.filter(tenant=tenant)
        if loc:
            qs = qs.filter(locale_id=loc.id)
        qs = self._same_translation_group_qs(qs, self.instance)
        if qs.exists():
            raise serializers.ValidationError(
                "A category with this slug already exists for this tenant."
            )
        return value


class ProductSerializer(
    TranslatableWritableMixin,
    TranslatableRepresentationMixin,
    serializers.ModelSerializer,
):
    """Translatable: ``name``, ``description``. ``category_name`` follows the same display locale."""

    translatable_overlay_fields = ("name", "description")

    category_name = serializers.SerializerMethodField()
    unit_of_measure_display = serializers.CharField(
        source="get_unit_of_measure_display", read_only=True,
    )
    tracking_mode_display = serializers.CharField(
        source="get_tracking_mode_display", read_only=True,
    )

    class Meta:
        model = Product
        fields = [
            "id", "sku", "name", "description", "category", "category_name",
            "unit_of_measure", "unit_of_measure_display",
            "tracking_mode", "tracking_mode_display",
            "unit_cost", "reorder_point", "is_active",
            "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def get_category_name(self, obj):
        category = obj.category
        if category is None:
            return None
        return attribute_in_display_locale(
            category, "name", display_locale_from_context(self.context),
        )

    def validate_sku(self, value):
        request = self.context.get("request")
        tenant = self.context.get("tenant") or (
            get_effective_tenant(request) if request else None
        )
        loc = self.context.get("wagtail_write_locale")
        qs = Product.objects.filter(sku=value)
        if tenant:
            qs = qs.filter(tenant=tenant)
        if loc:
            qs = qs.filter(locale_id=loc.id)
        qs = self._same_translation_group_qs(qs, self.instance)
        if qs.exists():
            raise serializers.ValidationError(
                "A product with this SKU already exists for this tenant."
            )
        return value


class WarehouseSerializer(serializers.ModelSerializer):
    """Tenant-scoped storage facility (DC, site)."""

    class Meta:
        model = Warehouse
        fields = [
            "id",
            "name",
            "description",
            "is_active",
            "timezone_name",
            "address",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class WarehouseQuickStatsSerializer(serializers.ModelSerializer):
    """Per-warehouse aggregates for dashboard / location UX (see ``warehouses/quick-stats/``)."""

    location_count = serializers.IntegerField(read_only=True)
    total_on_hand = serializers.IntegerField(read_only=True)
    reserved_quantity = serializers.IntegerField(read_only=True)
    available_quantity = serializers.SerializerMethodField()
    capacity_total = serializers.IntegerField(read_only=True)
    utilization_percent = serializers.SerializerMethodField()
    low_stock_line_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Warehouse
        fields = [
            "id",
            "name",
            "is_active",
            "location_count",
            "total_on_hand",
            "reserved_quantity",
            "available_quantity",
            "capacity_total",
            "utilization_percent",
            "low_stock_line_count",
        ]

    def get_available_quantity(self, obj):
        return (obj.total_on_hand or 0) - (obj.reserved_quantity or 0)

    def get_utilization_percent(self, obj):
        cap = obj.capacity_total or 0
        if cap <= 0:
            return None
        on = obj.total_on_hand or 0
        return round(100.0 * on / cap, 2)


class StockLocationSerializer(serializers.ModelSerializer):
    """Stock locations optionally linked to a :class:`~inventory.models.Warehouse`.

    Reads return nested ``warehouse`` and ``warehouse_id`` (nullable for retail-only trees).
    Writes accept ``warehouse_id`` (null clears the link on roots where allowed by the model).

    MP tree fields: ``depth``, ``parent_id``, ``materialized_path`` align with treebeard.
    ``ancestor_ids`` is set only on retrieve (for deep-link / expand-ancestor UX).
    """

    warehouse = WarehouseSerializer(read_only=True, allow_null=True)
    warehouse_id = serializers.PrimaryKeyRelatedField(
        queryset=Warehouse.objects.all(),
        source="warehouse",
        allow_null=True,
        required=False,
        write_only=True,
    )
    current_utilization = serializers.IntegerField(read_only=True)
    remaining_capacity = serializers.IntegerField(read_only=True, allow_null=True)
    stock_line_count = serializers.SerializerMethodField()
    depth = serializers.IntegerField(read_only=True)
    parent_id = serializers.SerializerMethodField()
    materialized_path = serializers.CharField(source="path", read_only=True)
    ancestor_ids = serializers.SerializerMethodField()

    class Meta:
        model = StockLocation
        fields = [
            "id", "name", "description", "is_active",
            "max_capacity", "warehouse", "warehouse_id",
            "current_utilization", "remaining_capacity", "stock_line_count",
            "depth", "parent_id", "materialized_path", "ancestor_ids",
            "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def get_stock_line_count(self, obj):
        try:
            return obj.stock_line_count
        except AttributeError:
            return obj.stock_records.count()

    def get_parent_id(self, obj):
        parent_map = self.context.get("parent_id_map")
        if parent_map is not None:
            return parent_map.get(obj.pk)
        if obj.depth <= 1:
            return None
        parent = obj.get_parent()
        return parent.pk if parent else None

    def get_ancestor_ids(self, obj):
        if not self.context.get("with_ancestor_ids"):
            return None
        return [a.pk for a in obj.get_ancestors()]

    def validate_warehouse(self, warehouse):
        if warehouse is None:
            return None
        request = self.context.get("request")
        tenant = self.context.get("tenant") or (
            get_effective_tenant(request) if request else None
        )
        if tenant is not None and warehouse.tenant_id != tenant.pk:
            raise serializers.ValidationError(
                "Warehouse does not belong to the current tenant.",
            )
        return warehouse

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["warehouse_id"] = instance.warehouse_id
        return data


class StockRecordSerializer(serializers.ModelSerializer):
    """``product_name`` uses the request display locale when ``product`` is translatable."""

    product_sku = serializers.CharField(source="product.sku", read_only=True)
    product_name = serializers.SerializerMethodField()
    location_name = serializers.SerializerMethodField()
    reserved_quantity = serializers.IntegerField(read_only=True)
    available_quantity = serializers.IntegerField(read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = StockRecord
        fields = [
            "id", "product", "product_sku", "product_name",
            "location", "location_name", "quantity",
            "reserved_quantity", "available_quantity", "is_low_stock",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "product", "location", "quantity",
            "created_at", "updated_at",
        ]

    def get_product_name(self, obj):
        return attribute_in_display_locale(
            obj.product, "name", display_locale_from_context(self.context),
        )

    def get_location_name(self, obj):
        return attribute_in_display_locale(
            obj.location, "name", display_locale_from_context(self.context),
        )


class StockLotSerializer(serializers.ModelSerializer):
    """Read-only serializer for lot/batch records."""

    product_sku = serializers.CharField(source="product.sku", read_only=True)
    product_name = serializers.SerializerMethodField()
    is_expired = serializers.BooleanField(read_only=True)
    days_to_expiry = serializers.IntegerField(read_only=True)

    class Meta:
        model = StockLot
        fields = [
            "id", "product", "product_sku", "product_name", "lot_number", "serial_number",
            "manufacturing_date", "expiry_date", "received_date",
            "quantity_received", "quantity_remaining",
            "is_active", "is_expired", "days_to_expiry",
            "supplier", "purchase_order",
            "created_at", "updated_at",
        ]
        read_only_fields = fields

    def get_product_name(self, obj):
        return attribute_in_display_locale(
            obj.product, "name", display_locale_from_context(self.context),
        )


class StockMovementLotSerializer(serializers.ModelSerializer):
    """Read-only serializer for lot allocations on a movement."""

    lot_number = serializers.CharField(source="stock_lot.lot_number", read_only=True)
    lot_id = serializers.IntegerField(source="stock_lot.id", read_only=True)

    class Meta:
        model = StockMovementLot
        fields = ["id", "lot_id", "lot_number", "quantity"]
        read_only_fields = fields


class StockMovementSerializer(serializers.ModelSerializer):
    product_sku = serializers.CharField(source="product.sku", read_only=True)
    product_name = serializers.SerializerMethodField()
    movement_type_display = serializers.CharField(
        source="get_movement_type_display", read_only=True,
    )
    from_location_name = serializers.SerializerMethodField()
    to_location_name = serializers.SerializerMethodField()
    lot_allocations = StockMovementLotSerializer(many=True, read_only=True)

    class Meta:
        model = StockMovement
        fields = [
            "id", "product", "product_sku", "product_name",
            "movement_type", "movement_type_display",
            "quantity", "unit_cost",
            "from_location", "from_location_name",
            "to_location", "to_location_name",
            "reference", "notes",
            "lot_allocations",
            "created_at", "created_by",
        ]
        read_only_fields = fields

    def get_product_name(self, obj):
        return attribute_in_display_locale(
            obj.product, "name", display_locale_from_context(self.context),
        )

    def get_from_location_name(self, obj):
        loc = obj.from_location
        if loc is None:
            return None
        return attribute_in_display_locale(
            loc, "name", display_locale_from_context(self.context),
        )

    def get_to_location_name(self, obj):
        loc = obj.to_location
        if loc is None:
            return None
        return attribute_in_display_locale(
            loc, "name", display_locale_from_context(self.context),
        )


class StockMovementCreateSerializer(serializers.Serializer):
    """Write serializer for creating stock movements via StockService.

    When any lot field is provided the view routes through
    ``StockService.process_movement_with_lots()``; otherwise
    ``process_movement()`` is used for backward compatibility.
    """

    LOT_FIELDS = frozenset({
        "lot_number", "serial_number", "manufacturing_date",
        "expiry_date", "allocation_strategy",
    })

    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
    )
    movement_type = serializers.ChoiceField(choices=MovementType.choices)
    quantity = serializers.IntegerField(min_value=1)
    from_location = serializers.PrimaryKeyRelatedField(
        queryset=StockLocation.objects.all(),
        required=False,
        allow_null=True,
        default=None,
    )
    to_location = serializers.PrimaryKeyRelatedField(
        queryset=StockLocation.objects.all(),
        required=False,
        allow_null=True,
        default=None,
    )
    unit_cost = serializers.DecimalField(
        max_digits=10, decimal_places=2,
        required=False, allow_null=True, default=None,
    )
    reference = serializers.CharField(
        required=False, allow_blank=True, default="",
    )
    notes = serializers.CharField(
        required=False, allow_blank=True, default="",
    )

    # Optional lot fields
    lot_number = serializers.CharField(
        required=False, allow_blank=True, default="",
    )
    serial_number = serializers.CharField(
        required=False, allow_blank=True, default="",
    )
    manufacturing_date = serializers.DateField(
        required=False, allow_null=True, default=None,
    )
    expiry_date = serializers.DateField(
        required=False, allow_null=True, default=None,
    )
    allocation_strategy = serializers.ChoiceField(
        choices=AllocationStrategy.choices,
        required=False,
        default=AllocationStrategy.FIFO,
    )

    @property
    def has_lot_fields(self) -> bool:
        """Return True if the request explicitly includes lot-related data.

        Checks both ``lot_number`` (for RECEIVE) and whether
        ``allocation_strategy`` was explicitly sent (for ISSUE/TRANSFER).
        """
        data = self.validated_data
        if bool(data.get("lot_number")):
            return True
        raw = self.initial_data
        if "allocation_strategy" in raw:
            return True
        return False
