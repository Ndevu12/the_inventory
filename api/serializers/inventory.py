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
)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = [
            "id", "name", "slug", "description", "is_active",
            "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def validate_slug(self, value):
        tenant = self.context.get("tenant") or getattr(
            self.context.get("request"), "tenant", None
        )
        qs = Category.objects.filter(slug=value)
        if tenant:
            qs = qs.filter(tenant=tenant)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                "A category with this slug already exists for this tenant."
            )
        return value


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(
        source="category.name", read_only=True, default=None,
    )
    unit_of_measure_display = serializers.CharField(
        source="get_unit_of_measure_display", read_only=True,
    )

    class Meta:
        model = Product
        fields = [
            "id", "sku", "name", "description", "category", "category_name",
            "unit_of_measure", "unit_of_measure_display",
            "unit_cost", "reorder_point", "is_active",
            "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def validate_sku(self, value):
        tenant = self.context.get("tenant") or getattr(
            self.context.get("request"), "tenant", None
        )
        qs = Product.objects.filter(sku=value)
        if tenant:
            qs = qs.filter(tenant=tenant)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                "A product with this SKU already exists for this tenant."
            )
        return value


class StockLocationSerializer(serializers.ModelSerializer):
    current_utilization = serializers.IntegerField(read_only=True)
    remaining_capacity = serializers.IntegerField(read_only=True, allow_null=True)

    class Meta:
        model = StockLocation
        fields = [
            "id", "name", "description", "is_active",
            "max_capacity", "current_utilization", "remaining_capacity",
            "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class StockRecordSerializer(serializers.ModelSerializer):
    product_sku = serializers.CharField(source="product.sku", read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)
    location_name = serializers.CharField(source="location.name", read_only=True)
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


class StockLotSerializer(serializers.ModelSerializer):
    """Read-only serializer for lot/batch records."""

    product_sku = serializers.CharField(source="product.sku", read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    days_to_expiry = serializers.IntegerField(read_only=True)

    class Meta:
        model = StockLot
        fields = [
            "id", "product", "product_sku", "lot_number", "serial_number",
            "manufacturing_date", "expiry_date", "received_date",
            "quantity_received", "quantity_remaining",
            "is_active", "is_expired", "days_to_expiry",
            "supplier", "purchase_order",
            "created_at", "updated_at",
        ]
        read_only_fields = fields


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
    movement_type_display = serializers.CharField(
        source="get_movement_type_display", read_only=True,
    )
    from_location_name = serializers.CharField(
        source="from_location.name", read_only=True, default=None,
    )
    to_location_name = serializers.CharField(
        source="to_location.name", read_only=True, default=None,
    )
    lot_allocations = StockMovementLotSerializer(many=True, read_only=True)

    class Meta:
        model = StockMovement
        fields = [
            "id", "product", "product_sku",
            "movement_type", "movement_type_display",
            "quantity", "unit_cost",
            "from_location", "from_location_name",
            "to_location", "to_location_name",
            "reference", "notes",
            "lot_allocations",
            "created_at", "created_by",
        ]
        read_only_fields = fields


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
        choices=[("FIFO", "FIFO"), ("LIFO", "LIFO")],
        required=False,
        default="FIFO",
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
