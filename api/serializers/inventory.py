"""Serializers for inventory models."""

from rest_framework import serializers

from inventory.models import (
    Category,
    MovementType,
    Product,
    StockLocation,
    StockMovement,
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


class StockLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockLocation
        fields = [
            "id", "name", "description", "is_active",
            "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class StockRecordSerializer(serializers.ModelSerializer):
    product_sku = serializers.CharField(source="product.sku", read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)
    location_name = serializers.CharField(source="location.name", read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = StockRecord
        fields = [
            "id", "product", "product_sku", "product_name",
            "location", "location_name", "quantity", "is_low_stock",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "product", "location", "quantity",
            "created_at", "updated_at",
        ]


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

    class Meta:
        model = StockMovement
        fields = [
            "id", "product", "product_sku",
            "movement_type", "movement_type_display",
            "quantity", "unit_cost",
            "from_location", "from_location_name",
            "to_location", "to_location_name",
            "reference", "notes",
            "created_at", "created_by",
        ]
        read_only_fields = fields


class StockMovementCreateSerializer(serializers.Serializer):
    """Write serializer for creating stock movements via StockService."""

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
