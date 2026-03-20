"""Inventory reporting service.

Provides read-only calculations for stock valuation, low-stock/overstock
analysis, movement history, and lot/expiry reporting.  No persistent
models — all data is derived from ``inventory`` app models.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING

from django.db.models import Count, F, Q, Sum
from django.db.models.functions import Coalesce

from tenants.context import get_current_tenant

from inventory.models import (
    InventoryCycle,
    InventoryVariance,
    MovementType,
    Product,
    ReservationStatus,
    StockLot,
    StockMovement,
    StockMovementLot,
    StockReservation,
    VarianceType,
)

if TYPE_CHECKING:
    from tenants.models import Tenant

if TYPE_CHECKING:
    from tenants.models import Tenant


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
    All methods accept an optional ``tenant`` parameter; if not provided,
    ``get_current_tenant()`` is used. Raises ``ValueError`` if no tenant
    can be determined.

    Usage::

        service = InventoryReportService()
        valuations = service.get_stock_valuation(method="weighted_average")
        movements = service.get_movement_history(date_from=date(2026, 1, 1))
    """

    # ------------------------------------------------------------------
    # Stock Valuation
    # ------------------------------------------------------------------

    VALUATION_METHODS = ("weighted_average", "latest_cost")

    def _resolve_tenant(self, tenant: Tenant | None = None):
        """Resolve tenant from parameter or context. Raises ValueError if none."""
        resolved = tenant or get_current_tenant()
        if not resolved:
            raise ValueError("No tenant provided or found in context")
        return resolved

    def get_stock_valuation(
        self, *, method: str = "weighted_average", tenant: Tenant | None = None,
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

        tenant = self._resolve_tenant(tenant)

        products = (
            Product.objects
            .filter(tenant=tenant, is_active=True)
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
            unit_cost = self._calculate_unit_cost(product, method, tenant)
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
        self, *, method: str = "weighted_average", tenant: Tenant | None = None,
    ) -> dict:
        """Aggregate stock valuation across all products.

        Returns a dict with ``total_products``, ``total_quantity``,
        and ``total_value``.
        """
        valuations = self.get_stock_valuation(method=method, tenant=tenant)
        return {
            "total_products": len(valuations),
            "total_quantity": sum(v.total_quantity for v in valuations),
            "total_value": sum(v.total_value for v in valuations),
            "method": method,
        }

    def _calculate_unit_cost(
        self, product: Product, method: str, tenant,
    ) -> Decimal:
        if method == "latest_cost":
            return product.unit_cost or Decimal("0.00")

        # weighted_average: total cost / total received quantity
        agg = (
            StockMovement.objects
            .filter(
                tenant=tenant,
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

    def get_low_stock_products(self, *, tenant: Tenant | None = None):
        """Return active products where any location's available quantity is at or below reorder point.

        Available quantity accounts for active reservations (pending/confirmed).
        Excludes products with ``reorder_point = 0`` (no alert configured).
        """
        tenant = self._resolve_tenant(tenant)
        return (
            Product.objects
            .filter(tenant=tenant, is_active=True)
            .low_stock()
            .select_related("category")
            .prefetch_related("stock_records", "stock_records__location")
            .order_by("sku")
        )

    def get_overstock_products(self, *, threshold_multiplier: int = 3, tenant: Tenant | None = None):
        """Return products where total stock exceeds reorder_point * multiplier.

        Useful for identifying overstocked items that tie up capital.
        Only includes products with a configured reorder point > 0.
        """
        tenant = self._resolve_tenant(tenant)
        return (
            Product.objects
            .filter(tenant=tenant, is_active=True, reorder_point__gt=0)
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
        tenant: Tenant | None = None,
    ):
        """Return a filtered queryset of stock movements.

        All parameters are optional — omit to get the full history.
        """
        tenant = self._resolve_tenant(tenant)

        qs = (
            StockMovement.objects
            .filter(tenant=tenant)
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
        tenant: Tenant | None = None,
    ) -> dict:
        """Aggregate movement counts and quantities by type.

        Returns a dict keyed by movement type with ``count`` and
        ``total_quantity`` for each.
        """
        tenant = self._resolve_tenant(tenant)
        qs = StockMovement.objects.filter(tenant=tenant)
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

    # ------------------------------------------------------------------
    # Reservation & Availability Reports
    # ------------------------------------------------------------------

    ACTIVE_RESERVATION_STATUSES = [
        ReservationStatus.PENDING,
        ReservationStatus.CONFIRMED,
    ]

    def get_reservation_summary(self, *, tenant: Tenant | None = None) -> dict:
        """Aggregate reservation counts and quantities by status.

        Returns a dict with ``by_status`` breakdown and top-level
        ``total_active_reservations`` / ``total_reserved_quantity``.
        """
        tenant = self._resolve_tenant(tenant)
        by_status = (
            StockReservation.objects
            .filter(tenant=tenant)
            .values("status")
            .annotate(
                count=Count("id"),
                total_quantity=Coalesce(Sum("quantity"), 0),
            )
            .order_by("status")
        )

        status_map = {}
        total_active = 0
        total_reserved_qty = 0

        for row in by_status:
            status_val = row["status"]
            label = dict(ReservationStatus.choices).get(status_val, status_val)
            status_map[status_val] = {
                "label": label,
                "count": row["count"],
                "total_quantity": row["total_quantity"],
            }
            if status_val in self.ACTIVE_RESERVATION_STATUSES:
                total_active += row["count"]
                total_reserved_qty += row["total_quantity"]

        return {
            "by_status": status_map,
            "total_active_reservations": total_active,
            "total_reserved_quantity": total_reserved_qty,
        }

    def get_availability_report(
        self,
        *,
        category_id: int | None = None,
        product_id: int | None = None,
        tenant: Tenant | None = None,
    ) -> list[dict]:
        """Per-product availability: total qty, reserved, available.

        Optionally filter by ``category_id`` or ``product_id``.
        Returns a list of dicts sorted by product SKU.
        """
        tenant = self._resolve_tenant(tenant)
        qs = (
            Product.objects
            .filter(tenant=tenant, is_active=True)
            .annotate(
                total_quantity=Coalesce(
                    Sum("stock_records__quantity"), 0,
                ),
            )
            .select_related("category")
            .order_by("sku")
        )

        if category_id is not None:
            qs = qs.filter(category_id=category_id)
        if product_id is not None:
            qs = qs.filter(pk=product_id)

        reserved_qs = (
            StockReservation.objects
            .filter(tenant=tenant, status__in=self.ACTIVE_RESERVATION_STATUSES)
            .values("product_id")
            .annotate(reserved=Coalesce(Sum("quantity"), 0))
        )
        reserved_map = {
            row["product_id"]: row["reserved"] for row in reserved_qs
        }

        results = []
        for product in qs:
            total_qty = product.total_quantity
            reserved = reserved_map.get(product.pk, 0)
            available = total_qty - reserved
            results.append({
                "product_id": product.pk,
                "sku": product.sku,
                "product_name": product.name,
                "category": str(product.category) if product.category else None,
                "total_quantity": total_qty,
                "reserved_quantity": reserved,
                "available_quantity": available,
                "unit_cost": product.unit_cost,
                "reserved_value": reserved * product.unit_cost,
            })
        return results

    def get_reserved_stock_value(self, *, tenant: Tenant | None = None) -> Decimal:
        """Total value of actively reserved stock across all products.

        Used as a dashboard KPI: ``reserved_qty * unit_cost`` per product.
        """
        availability = self.get_availability_report(tenant=tenant)
        return sum(
            (item["reserved_value"] for item in availability),
            Decimal("0.00"),
        )

    # ------------------------------------------------------------------
    # Variance & Cycle Count Reports
    # ------------------------------------------------------------------

    def get_variance_report(
        self,
        *,
        cycle_id: int | None = None,
        product_id: int | None = None,
        variance_type: str | None = None,
        tenant: Tenant | None = None,
    ):
        """Return a filtered queryset of inventory variances.

        Parameters
        ----------
        cycle_id : int | None
            Filter to variances from a specific cycle count.
        product_id : int | None
            Filter to variances for a specific product.
        variance_type : str | None
            One of ``VarianceType`` values (``"shortage"``,
            ``"surplus"``, ``"match"``).

        Returns
        -------
        QuerySet[InventoryVariance]
        """
        tenant = self._resolve_tenant(tenant)
        qs = (
            InventoryVariance.objects
            .filter(tenant=tenant)
            .select_related(
                "cycle", "product", "location",
                "count_line", "resolved_by",
            )
            .order_by("-created_at")
        )

        if cycle_id is not None:
            qs = qs.filter(cycle_id=cycle_id)
        if product_id is not None:
            qs = qs.filter(product_id=product_id)
        if variance_type is not None:
            qs = qs.filter(variance_type=variance_type)

        return qs

    def get_variance_summary(
        self,
        *,
        cycle_id: int | None = None,
        tenant: Tenant | None = None,
    ) -> dict:
        """Aggregate variance counts and net quantity by type.

        Returns a dict with ``by_type`` breakdown, ``total_variances``,
        and ``net_variance`` (sum of all variance quantities).
        """
        tenant = self._resolve_tenant(tenant)
        qs = InventoryVariance.objects.filter(tenant=tenant)
        if cycle_id is not None:
            qs = qs.filter(cycle_id=cycle_id)

        by_type = (
            qs.values("variance_type")
            .annotate(
                count=Count("id"),
                total_quantity=Coalesce(Sum("variance_quantity"), 0),
            )
            .order_by("variance_type")
        )

        type_map = {}
        for row in by_type:
            vtype = row["variance_type"]
            label = dict(VarianceType.choices).get(vtype, vtype)
            type_map[vtype] = {
                "label": label,
                "count": row["count"],
                "total_quantity": row["total_quantity"],
            }

        total = qs.count()
        net = qs.aggregate(net=Coalesce(Sum("variance_quantity"), 0))["net"]

        return {
            "by_type": type_map,
            "total_variances": total,
            "net_variance": net,
        }

    def get_cycle_history(self, *, tenant: Tenant | None = None) -> list[dict]:
        """Summary of past inventory cycles and their reconciliation status.

        Returns a list of dicts ordered by scheduled date (most recent
        first), each containing cycle metadata plus variance statistics.
        """
        tenant = self._resolve_tenant(tenant)
        cycles = (
            InventoryCycle.objects
            .filter(tenant=tenant)
            .annotate(
                total_lines=Count("lines", distinct=True),
                total_variances=Count("variances", distinct=True),
                shortage_count=Count(
                    "variances",
                    filter=Q(variances__variance_type=VarianceType.SHORTAGE),
                    distinct=True,
                ),
                surplus_count=Count(
                    "variances",
                    filter=Q(variances__variance_type=VarianceType.SURPLUS),
                    distinct=True,
                ),
                match_count=Count(
                    "variances",
                    filter=Q(variances__variance_type=VarianceType.MATCH),
                    distinct=True,
                ),
                net_variance=Coalesce(
                    Sum("variances__variance_quantity"), 0,
                ),
            )
            .select_related("location", "started_by")
            .order_by("-scheduled_date")
        )

        results = []
        for cycle in cycles:
            results.append({
                "id": cycle.pk,
                "name": cycle.name,
                "status": cycle.status,
                "status_display": cycle.get_status_display(),
                "location": str(cycle.location) if cycle.location else None,
                "scheduled_date": cycle.scheduled_date,
                "started_at": cycle.started_at,
                "completed_at": cycle.completed_at,
                "started_by": str(cycle.started_by) if cycle.started_by else None,
                "total_lines": cycle.total_lines,
                "total_variances": cycle.total_variances,
                "shortages": cycle.shortage_count,
                "surpluses": cycle.surplus_count,
                "matches": cycle.match_count,
                "net_variance": cycle.net_variance,
            })
        return results

    # ------------------------------------------------------------------
    # Lot & Expiry Reports
    # ------------------------------------------------------------------

    def get_expiring_lots(
        self,
        *,
        days_ahead: int = 30,
        product: Product | None = None,
        location=None,
        tenant: Tenant | None = None,
    ):
        """Return active lots expiring within *days_ahead* days.

        Only includes lots with ``quantity_remaining > 0`` and an expiry
        date set.  Results are ordered by expiry date (soonest first).

        Parameters
        ----------
        days_ahead : int
            Number of days to look ahead from today.
        product : Product | None
            Restrict to a single product.
        location : StockLocation | None
            If provided, only lots whose product has stock at this location.
        tenant : Tenant | None
            Tenant to filter by. Defaults to current tenant from context.
        """
        tenant = self._resolve_tenant(tenant)

        cutoff = date.today() + timedelta(days=days_ahead)
        qs = (
            StockLot.objects
            .filter(tenant=tenant)
            .filter(
                is_active=True,
                expiry_date__isnull=False,
                expiry_date__gt=date.today(),
                expiry_date__lte=cutoff,
                quantity_remaining__gt=0,
            )
            .select_related("product", "product__category", "supplier")
            .order_by("expiry_date", "pk")
        )

        if product is not None:
            qs = qs.filter(product=product)
        if location is not None:
            qs = qs.filter(product__stock_records__location=location).distinct()

        return qs

    def get_expired_lots(
        self,
        *,
        product: Product | None = None,
        location=None,
        include_depleted: bool = False,
        tenant: Tenant | None = None,
    ):
        """Return lots that have passed their expiry date.

        By default only lots with ``quantity_remaining > 0`` are returned,
        since depleted expired lots are usually not actionable.

        Parameters
        ----------
        product : Product | None
            Restrict to a single product.
        location : StockLocation | None
            If provided, only lots whose product has stock at this location.
        include_depleted : bool
            If True, also include lots with ``quantity_remaining = 0``.
        tenant : Tenant | None
            Tenant to filter by. Defaults to current tenant from context.
        """
        tenant = self._resolve_tenant(tenant)

        qs = (
            StockLot.objects
            .filter(tenant=tenant)
            .filter(
                is_active=True,
                expiry_date__isnull=False,
                expiry_date__lte=date.today(),
            )
            .select_related("product", "product__category", "supplier")
            .order_by("expiry_date", "pk")
        )

        if not include_depleted:
            qs = qs.filter(quantity_remaining__gt=0)
        if product is not None:
            qs = qs.filter(product=product)
        if location is not None:
            qs = qs.filter(product__stock_records__location=location).distinct()

        return qs

    def get_lot_history(
        self, product: Product, lot_number: str, *, tenant: Tenant | None = None,
    ):
        """Return the full movement chain for a specific lot.

        Returns a queryset of :class:`StockMovement` instances that
        consumed or produced units in the given lot, ordered
        chronologically (newest first).
        """
        tenant = self._resolve_tenant(tenant)
        movement_ids = (
            StockMovementLot.objects
            .filter(
                stock_lot__product=product,
                stock_lot__lot_number=lot_number,
                stock_lot__tenant=tenant,
            )
            .values_list("stock_movement_id", flat=True)
        )

        return (
            StockMovement.objects
            .filter(tenant=tenant, pk__in=movement_ids)
            .select_related(
                "product", "from_location", "to_location", "created_by",
            )
            .prefetch_related("lot_allocations", "lot_allocations__stock_lot")
            .order_by("-created_at")
        )

    # ------------------------------------------------------------------
    # Product Traceability (GS1)
    # ------------------------------------------------------------------

    _ACTION_MAP = {
        MovementType.RECEIVE: "received",
        MovementType.TRANSFER: "transferred",
        MovementType.ISSUE: "issued",
        MovementType.ADJUSTMENT: "adjusted",
    }

    def get_product_traceability(
        self,
        *,
        sku: str,
        lot_number: str,
        tenant: Tenant | None = None,
    ) -> dict | None:
        """Build a full movement chain for a product + lot combination.

        Returns ``None`` when the product or lot cannot be found.
        Otherwise returns a dict matching the GS1 traceability schema
        with ``product``, ``lot``, and chronologically-ordered ``chain``.
        """
        tenant = self._resolve_tenant(tenant)
        try:
            product = Product.objects.filter(tenant=tenant).get(sku=sku)
        except Product.DoesNotExist:
            return None

        try:
            lot = StockLot.objects.filter(tenant=tenant).select_related("supplier").get(
                product=product,
                lot_number=lot_number,
            )
        except StockLot.DoesNotExist:
            return None

        allocations = (
            StockMovementLot.objects
            .filter(stock_lot=lot)
            .select_related(
                "stock_movement",
                "stock_movement__from_location",
                "stock_movement__to_location",
            )
            .order_by("stock_movement__created_at")
        )

        chain = []
        for alloc in allocations:
            mv = alloc.stock_movement
            entry = self._build_chain_entry(mv, alloc.quantity)
            chain.append(entry)

        return {
            "product": str(product),
            "lot": {
                "lot_number": lot.lot_number,
                "manufacturing_date": (
                    lot.manufacturing_date.isoformat()
                    if lot.manufacturing_date
                    else None
                ),
                "expiry_date": (
                    lot.expiry_date.isoformat() if lot.expiry_date else None
                ),
                "supplier": str(lot.supplier) if lot.supplier else None,
            },
            "chain": chain,
        }

    def _build_chain_entry(self, movement: StockMovement, quantity: int) -> dict:
        """Format a single movement into a traceability chain entry."""
        action = self._ACTION_MAP.get(movement.movement_type, movement.movement_type)
        entry: dict = {
            "action": action,
            "date": movement.created_at.isoformat(),
            "quantity": quantity,
        }

        if movement.movement_type == MovementType.TRANSFER:
            entry["from"] = str(movement.from_location) if movement.from_location else None
            entry["to"] = str(movement.to_location) if movement.to_location else None
        elif movement.movement_type == MovementType.ISSUE:
            entry["location"] = str(movement.from_location) if movement.from_location else None
            if movement.reference:
                entry["sales_order"] = movement.reference
        elif movement.movement_type == MovementType.RECEIVE:
            entry["location"] = str(movement.to_location) if movement.to_location else None
        elif movement.movement_type == MovementType.ADJUSTMENT:
            loc = movement.to_location or movement.from_location
            entry["location"] = str(loc) if loc else None

        return entry
