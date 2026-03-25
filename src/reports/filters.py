"""Report filters for date-range and category/type selection."""

import django_filters

from inventory.models import Category, MovementType, Product, StockLocation, Warehouse
from inventory.services.stock import filter_stock_movements_by_warehouse_scope


class DateRangeFilter(django_filters.FilterSet):
    """Base filterset providing date_from and date_to fields.

    Subclasses can add model-specific filters alongside these.
    """

    date_from = django_filters.DateFilter(
        field_name="date_from",
        method="filter_noop",
        label="From Date",
    )
    date_to = django_filters.DateFilter(
        field_name="date_to",
        method="filter_noop",
        label="To Date",
    )

    def filter_noop(self, queryset, name, value):
        """Dates are applied in the service layer, not on the queryset."""
        return queryset


class MovementHistoryFilter(django_filters.FilterSet):
    """Filters for the movement history report."""

    tenant = None  # set by the view: MovementHistoryFilter(..., tenant=tenant)

    date_from = django_filters.DateFilter(
        field_name="created_at",
        lookup_expr="date__gte",
        label="From Date",
    )
    date_to = django_filters.DateFilter(
        field_name="created_at",
        lookup_expr="date__lte",
        label="To Date",
    )
    movement_type = django_filters.ChoiceFilter(
        choices=[("", "All Types")] + list(MovementType.choices),
        label="Movement Type",
    )
    location = django_filters.ModelChoiceFilter(
        method="filter_by_location",
        queryset=StockLocation.objects.filter(is_active=True),
        label="Location",
        empty_label="All Locations",
    )
    category = django_filters.ModelChoiceFilter(
        field_name="product__category",
        queryset=Category.objects.filter(is_active=True),
        label="Category",
        empty_label="All Categories",
    )
    warehouse = django_filters.ModelChoiceFilter(
        queryset=Warehouse.objects.none(),
        method="filter_warehouse_facility",
        label="Warehouse (facility)",
        empty_label="All facilities / retail",
    )
    retail_locations_only = django_filters.BooleanFilter(
        method="filter_retail_site_scope",
        label="Retail locations only",
    )

    def __init__(self, data=None, queryset=None, *, tenant=None, **kwargs):
        super().__init__(data=data, queryset=queryset, **kwargs)
        self.tenant = tenant
        wh_field = self.filters["warehouse"]
        if tenant is not None:
            wh_field.queryset = Warehouse.objects.filter(tenant=tenant, is_active=True)
        else:
            wh_field.queryset = Warehouse.objects.none()

    def filter_warehouse_facility(self, queryset, name, value):
        if not value or self.tenant is None:
            return queryset
        return filter_stock_movements_by_warehouse_scope(
            queryset,
            tenant_id=self.tenant.pk,
            warehouse_id=value.pk,
        )

    def filter_retail_site_scope(self, queryset, name, value):
        if not value or self.tenant is None:
            return queryset
        return filter_stock_movements_by_warehouse_scope(
            queryset,
            tenant_id=self.tenant.pk,
            warehouse_id=None,
        )

    def filter_by_location(self, queryset, name, value):
        """Filter movements that touch a given location (source or dest)."""
        from django.db.models import Q
        return queryset.filter(
            Q(from_location=value) | Q(to_location=value),
        )


class ExpiryReportFilter(django_filters.FilterSet):
    """Filters for the lot expiry report."""

    days_ahead = django_filters.NumberFilter(
        method="filter_noop",
        label="Days Ahead",
    )
    product = django_filters.ModelChoiceFilter(
        queryset=Product.objects.filter(is_active=True),
        label="Product",
        empty_label="All Products",
    )
    location = django_filters.ModelChoiceFilter(
        method="filter_noop",
        queryset=StockLocation.objects.filter(is_active=True),
        label="Location",
        empty_label="All Locations",
    )

    def filter_noop(self, queryset, name, value):
        """Filtering is applied in the service layer."""
        return queryset


class OrderSummaryFilter(django_filters.FilterSet):
    """Filters for purchase/sales summary reports."""

    PERIOD_CHOICES = [
        ("monthly", "Monthly"),
        ("weekly", "Weekly"),
        ("daily", "Daily"),
    ]

    date_from = django_filters.DateFilter(
        field_name="date_from",
        method="filter_noop",
        label="From Date",
    )
    date_to = django_filters.DateFilter(
        field_name="date_to",
        method="filter_noop",
        label="To Date",
    )
    period = django_filters.ChoiceFilter(
        choices=PERIOD_CHOICES,
        method="filter_noop",
        label="Group By",
    )

    def filter_noop(self, queryset, name, value):
        return queryset
