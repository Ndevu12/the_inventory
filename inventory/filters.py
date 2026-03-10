"""Django-filter filtersets for inventory models.

Each filterset is a class following the project's OOP standard.
"""

import django_filters

from inventory.models import Category, Product, StockLocation


class StockStatusFilter(django_filters.ChoiceFilter):
    """Custom filter for stock-level status (low / in-stock / out-of-stock)."""

    STATUS_CHOICES = [
        ("", "All"),
        ("low", "Low Stock"),
        ("in_stock", "In Stock"),
        ("out_of_stock", "Out of Stock"),
    ]

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("choices", self.STATUS_CHOICES)
        kwargs.setdefault("label", "Stock Status")
        super().__init__(*args, **kwargs)

    def filter(self, qs, value):
        if value == "low":
            return qs.low_stock()
        elif value == "in_stock":
            return qs.in_stock()
        elif value == "out_of_stock":
            return qs.out_of_stock()
        return qs


class ProductFilterSet(django_filters.FilterSet):
    """Filterset for Product listings with stock-aware filters.

    Provides filters for:
    - **category** — FK dropdown
    - **stock_status** — custom filter using ProductQuerySet methods
    - **is_active** — boolean
    - **location** — filters products that have stock at a given location
    """

    category = django_filters.ModelChoiceFilter(
        queryset=Category.objects.all(),
        label="Category",
        empty_label="All Categories",
    )
    stock_status = StockStatusFilter(field_name="stock_status")
    is_active = django_filters.BooleanFilter(
        label="Active",
    )
    location = django_filters.ModelChoiceFilter(
        field_name="stock_records__location",
        queryset=StockLocation.objects.all(),
        label="Location",
        empty_label="All Locations",
        distinct=True,
    )

    class Meta:
        model = Product
        fields = ["category", "stock_status", "is_active", "location"]
