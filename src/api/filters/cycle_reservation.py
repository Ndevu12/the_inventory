"""django-filter :class:`~django_filters.FilterSet` classes for cycle and reservation APIs."""

import django_filters

from inventory.models import StockReservation
from inventory.models.cycle import InventoryCycle


class InventoryCycleFilter(django_filters.FilterSet):
    """Supports ``location__warehouse`` and retail-partition null checks."""

    location__warehouse__isnull = django_filters.BooleanFilter(
        field_name="location__warehouse",
        lookup_expr="isnull",
    )

    class Meta:
        model = InventoryCycle
        fields = {
            "status": ["exact"],
            "location": ["exact"],
            "location__warehouse": ["exact"],
        }


class StockReservationFilter(django_filters.FilterSet):
    """Supports ``location__warehouse`` and retail-partition null checks."""

    location__warehouse__isnull = django_filters.BooleanFilter(
        field_name="location__warehouse",
        lookup_expr="isnull",
    )

    class Meta:
        model = StockReservation
        fields = {
            "status": ["exact"],
            "product": ["exact"],
            "location": ["exact"],
            "location__warehouse": ["exact"],
        }
