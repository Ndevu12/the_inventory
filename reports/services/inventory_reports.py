"""Inventory reporting service.

Provides read-only calculations for stock valuation, low-stock/overstock
analysis, and movement history.  No persistent models — all data is
derived from ``inventory`` app models.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from django.db.models import F, Q, Sum
from django.db.models.functions import Coalesce

from inventory.models import MovementType, Product, StockMovement, StockRecord


@dataclass
class ProductValuation:
    """Stock valuation result for a single product."""

    product: Product
    total_quantity: int
    unit_cost: Decimal
    total_value: Decimal
    method: str


class InventoryReportService:
    """Read-only reporting on stock valuation, levels, and movements.

    All methods return querysets or lists of dataclasses — no mutations.

    Usage::

        service = InventoryReportService()
        valuations = service.get_stock_valuation(method="weighted_average")
        movements = service.get_movement_history(date_from=date(2026, 1, 1))
    """

    # ------------------------------------------------------------------
    # Stock Valuation
    # ------------------------------------------------------------------

    VALUATION_METHODS = ("weighted_average", "latest_cost")

    def get_stock_valuation(
        self, *, method: str = "weighted_average",
    ) -> list[ProductValuation]:
        """Calculate the total stock value for every active product.

        Parameters
        ----------
        method : str
            ``"weighted_average"`` — weighted average cost from receive
            movements.  ``"latest_cost"`` — uses ``Product.unit_cost``.

        Returns a list of :class:`ProductValuation` dataclasses sorted
        by product SKU.
        """
        if method not in self.VALUATION_METHODS:
            raise ValueError(
                f"Unknown valuation method '{method}'. "
                f"Choose from: {', '.join(self.VALUATION_METHODS)}"
            )

        products = (
            Product.objects
            .filter(is_active=True)
            .annotate(
                total_stock=Coalesce(
                    Sum("stock_records__quantity"), 0,
                ),
            )
            .filter(total_stock__gt=0)
            .select_related("category")
            .order_by("sku")
        )

        results = []
        for product in products:
            unit_cost = self._calculate_unit_cost(product, method)
            total_qty = product.total_stock
            results.append(ProductValuation(
                product=product,
                total_quantity=total_qty,
                unit_cost=unit_cost,
                total_value=unit_cost * total_qty,
                method=method,
            ))
        return results

    def get_valuation_summary(
        self, *, method: str = "weighted_average",
    ) -> dict:
        """Aggregate stock valuation across all products.

        Returns a dict with ``total_products``, ``total_quantity``,
        and ``total_value``.
        """
        valuations = self.get_stock_valuation(method=method)
        return {
            "total_products": len(valuations),
            "total_quantity": sum(v.total_quantity for v in valuations),
            "total_value": sum(v.total_value for v in valuations),
            "method": method,
        }

    def _calculate_unit_cost(
        self, product: Product, method: str,
    ) -> Decimal:
        if method == "latest_cost":
            return product.unit_cost or Decimal("0.00")

        # weighted_average: total cost / total received quantity
        agg = (
            StockMovement.objects
            .filter(
                product=product,
                movement_type=MovementType.RECEIVE,
                unit_cost__isnull=False,
            )
            .aggregate(
                total_cost=Sum(F("quantity") * F("unit_cost")),
                total_qty=Sum("quantity"),
            )
        )
        total_cost = agg["total_cost"]
        total_qty = agg["total_qty"]

        if total_cost and total_qty:
            return (total_cost / total_qty).quantize(Decimal("0.01"))

        return product.unit_cost or Decimal("0.00")

    # ------------------------------------------------------------------
    # Stock Level Reports
    # ------------------------------------------------------------------

    def get_low_stock_products(self):
        """Return active products where any location is at or below reorder point.

        Excludes products with ``reorder_point = 0`` (no alert configured).
        """
        return (
            Product.objects
            .filter(is_active=True)
            .low_stock()
            .select_related("category")
            .prefetch_related("stock_records", "stock_records__location")
            .order_by("sku")
        )

    def get_overstock_products(self, *, threshold_multiplier: int = 3):
        """Return products where total stock exceeds reorder_point * multiplier.

        Useful for identifying overstocked items that tie up capital.
        Only includes products with a configured reorder point > 0.
        """
        return (
            Product.objects
            .filter(is_active=True, reorder_point__gt=0)
            .annotate(
                total_stock=Coalesce(
                    Sum("stock_records__quantity"), 0,
                ),
            )
            .filter(
                total_stock__gt=F("reorder_point") * threshold_multiplier,
            )
            .select_related("category")
            .order_by("sku")
        )

    # ------------------------------------------------------------------
    # Movement History
    # ------------------------------------------------------------------

    def get_movement_history(
        self,
        *,
        date_from: date | None = None,
        date_to: date | None = None,
        product: Product | None = None,
        movement_type: str | None = None,
        location=None,
    ):
        """Return a filtered queryset of stock movements.

        All parameters are optional — omit to get the full history.
        """
        qs = (
            StockMovement.objects
            .select_related(
                "product", "from_location", "to_location", "created_by",
            )
            .order_by("-created_at")
        )

        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)
        if product:
            qs = qs.filter(product=product)
        if movement_type:
            qs = qs.filter(movement_type=movement_type)
        if location:
            qs = qs.filter(
                Q(from_location=location) | Q(to_location=location),
            )
        return qs

    def get_movement_summary(
        self,
        *,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> dict:
        """Aggregate movement counts and quantities by type.

        Returns a dict keyed by movement type with ``count`` and
        ``total_quantity`` for each.
        """
        qs = StockMovement.objects.all()
        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)

        summary = {}
        for mt_value, mt_label in MovementType.choices:
            agg = qs.filter(movement_type=mt_value).aggregate(
                count=Coalesce(Sum("quantity", default=0), 0),
                total_quantity=Coalesce(Sum("quantity"), 0),
            )
            summary[mt_value] = {
                "label": mt_label,
                "count": qs.filter(movement_type=mt_value).count(),
                "total_quantity": agg["total_quantity"],
            }
        return summary
