"""Sales service for sales order and dispatch workflows.

Follows the project's OOP service-layer convention.  All sales-order
state transitions and dispatch/issuing logic lives here rather than in
model ``save()`` methods or view code.
"""

from __future__ import annotations

import logging

from django.core.exceptions import ValidationError
from django.db import transaction

from inventory.exceptions import InsufficientStockError, InventoryError
from inventory.models.reservation import ReservationRule
from inventory.models.stock import MovementType, StockRecord
from inventory.services.reservation import ReservationService
from inventory.services.stock import StockService

from sales.models.order import SalesOrderStatus

logger = logging.getLogger(__name__)


class SalesService:
    """Encapsulates sales business logic.

    Usage::

        service = SalesService()
        service.confirm_order(sales_order=so)
        service.process_dispatch(dispatch=dispatch, dispatched_by=user)
    """

    def __init__(
        self,
        *,
        stock_service: StockService | None = None,
        reservation_service: ReservationService | None = None,
    ):
        self._stock_service = stock_service or StockService()
        self._reservation_service = reservation_service or ReservationService()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def confirm_order(self, *, sales_order, confirmed_by=None, default_location=None):
        """Transition a sales order from draft to confirmed.

        Validates that the order is in draft status and has at least
        one line item before confirming.

        When a :class:`ReservationRule` with ``auto_reserve_on_order=True``
        applies to a line's product, a :class:`StockReservation` is
        automatically created at ``default_location`` (required when
        auto-reservation is triggered).

        Returns the updated sales order.
        """
        if sales_order.status != SalesOrderStatus.DRAFT:
            raise ValidationError(
                f"Only draft orders can be confirmed. "
                f"Current status: {sales_order.get_status_display()}."
            )
        if not sales_order.lines.exists():
            raise ValidationError(
                "Cannot confirm a sales order with no line items."
            )

        with transaction.atomic():
            sales_order.status = SalesOrderStatus.CONFIRMED
            if confirmed_by:
                sales_order.created_by = sales_order.created_by or confirmed_by
            sales_order.save(update_fields=["status", "updated_at"])

            self._auto_reserve_lines(
                sales_order,
                confirmed_by=confirmed_by,
                default_location=default_location,
            )

        return sales_order

    def cancel_order(self, *, sales_order, cancelled_by=None):
        """Cancel a sales order.

        Only draft or confirmed orders can be cancelled.  Fulfilled
        orders cannot be cancelled — corrective adjustments should
        be used instead.
        """
        allowed = {SalesOrderStatus.DRAFT, SalesOrderStatus.CONFIRMED}
        if sales_order.status not in allowed:
            raise ValidationError(
                f"Only draft or confirmed orders can be cancelled. "
                f"Current status: {sales_order.get_status_display()}."
            )

        sales_order.status = SalesOrderStatus.CANCELLED
        sales_order.save(update_fields=["status", "updated_at"])
        return sales_order

    def process_dispatch(
        self,
        *,
        dispatch,
        dispatched_by=None,
        issue_available_only: bool = False,
    ):
        """Process a dispatch: issue stock for each sales order line.

        Creates an ``issue`` StockMovement for each line on the
        associated sales order, decrementing stock at the dispatch's
        source location.  Marks the dispatch as processed and
        transitions the SO to fulfilled status (or leaves it confirmed
        when ``issue_available_only`` ships a partial quantity).

        When ``issue_available_only`` is True, each line issues
        ``min(line quantity, available quantity at the dispatch source
        location)`` (available = on-hand minus reservations).  If every
        non-zero line can be fully covered, behaviour matches a normal
        full dispatch (line quantities on the SO are not reduced).
        Otherwise remaining quantities stay on the order for a later
        dispatch.

        The entire operation is wrapped in a transaction — if any
        movement fails (e.g. insufficient stock on full dispatch),
        nothing is persisted.
        """
        if dispatch.is_processed:
            raise ValidationError(
                "This dispatch has already been processed."
            )

        so = dispatch.sales_order
        if so.status != SalesOrderStatus.CONFIRMED:
            raise ValidationError(
                f"Sales order must be confirmed before dispatching. "
                f"Current status: {so.get_status_display()}."
            )

        lines = so.lines.select_related("product").all()
        if not lines.exists():
            raise ValidationError(
                "The sales order has no line items to dispatch."
            )

        lines_list = list(lines.order_by("pk"))

        if issue_available_only:
            return self._process_dispatch_available_only(
                dispatch=dispatch,
                sales_order=so,
                lines=lines_list,
                dispatched_by=dispatched_by,
            )

        with transaction.atomic():
            try:
                self._issue_full_quantities(
                    dispatch=dispatch,
                    lines=lines_list,
                    dispatched_by=dispatched_by,
                )
            except InsufficientStockError as exc:
                loc = dispatch.from_location
                loc_label = getattr(loc, "name", None) or "the source location"
                raise ValidationError(
                    f"{exc} "
                    f'Receive or transfer stock into "{loc_label}" first, '
                    f"then process this dispatch again, or use "
                    f'"issue available quantities only" if supported.',
                ) from exc
            except InventoryError as exc:
                raise ValidationError(str(exc)) from exc

            dispatch.is_processed = True
            dispatch.save(update_fields=["is_processed", "updated_at"])

            so.status = SalesOrderStatus.FULFILLED
            so.save(update_fields=["status", "updated_at"])

        return dispatch

    def fulfillment_preview(self, *, dispatch):
        """Per-line ordered vs available (unreserved) stock at dispatch source."""
        if dispatch.is_processed:
            raise ValidationError("This dispatch has already been processed.")

        so = dispatch.sales_order
        if so.status != SalesOrderStatus.CONFIRMED:
            raise ValidationError(
                f"Sales order must be confirmed. "
                f"Current status: {so.get_status_display()}."
            )

        loc = dispatch.from_location
        rows = []
        for line in so.lines.select_related("product").order_by("pk"):
            ordered = line.quantity
            available = self._available_at_location(
                product=line.product,
                location=loc,
            )
            issue_now = min(ordered, available) if ordered > 0 else 0
            rows.append({
                "line_id": line.id,
                "product_id": line.product_id,
                "product_sku": line.product.sku,
                "ordered_quantity": ordered,
                "available_quantity": available,
                "issue_now_quantity": issue_now,
            })

        can_full = all(
            r["ordered_quantity"] <= r["available_quantity"]
            for r in rows
        )
        total_issue = sum(r["issue_now_quantity"] for r in rows)
        return {
            "from_location": {"id": loc.pk, "name": loc.name},
            "sales_order_id": so.pk,
            "lines": rows,
            "can_full_dispatch": can_full,
            "total_issue_if_available_only": total_issue,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _available_at_location(*, product, location) -> int:
        rec = (
            StockRecord.objects.filter(product=product, location=location)
            .first()
        )
        if rec is None:
            return 0
        return max(0, rec.available_quantity)

    def _issue_full_quantities(self, *, dispatch, lines, dispatched_by):
        for line in lines:
            qty = line.quantity
            if qty <= 0:
                continue
            self._stock_service.process_movement(
                product=line.product,
                movement_type=MovementType.ISSUE,
                quantity=qty,
                from_location=dispatch.from_location,
                unit_cost=line.product.unit_cost,
                reference=dispatch.dispatch_number,
                created_by=dispatched_by,
            )

    def _process_dispatch_available_only(
        self,
        *,
        dispatch,
        sales_order,
        lines,
        dispatched_by,
    ):
        loc = dispatch.from_location
        loc_label = getattr(loc, "name", None) or "the source location"

        planned = []
        for line in lines:
            if line.quantity <= 0:
                planned.append((line, 0))
                continue
            av = self._available_at_location(
                product=line.product,
                location=loc,
            )
            planned.append((line, min(line.quantity, av)))

        total_issue = sum(q for _, q in planned)
        if total_issue <= 0:
            raise ValidationError(
                f'No unreserved stock available at "{loc_label}" for any line '
                f"on this order. Receive or transfer stock there first, "
                f"reduce quantities on the sales order, or cancel this dispatch."
            )

        full_ship = all(
            line.quantity == 0 or to_issue == line.quantity
            for line, to_issue in planned
        )

        with transaction.atomic():
            try:
                if full_ship:
                    self._issue_full_quantities(
                        dispatch=dispatch,
                        lines=lines,
                        dispatched_by=dispatched_by,
                    )
                else:
                    for line, to_issue in planned:
                        if to_issue <= 0:
                            continue
                        self._stock_service.process_movement(
                            product=line.product,
                            movement_type=MovementType.ISSUE,
                            quantity=to_issue,
                            from_location=dispatch.from_location,
                            unit_cost=line.product.unit_cost,
                            reference=dispatch.dispatch_number,
                            created_by=dispatched_by,
                        )
                        line.quantity -= to_issue
                        line.save(
                            update_fields=["quantity", "updated_at"],
                        )
            except InsufficientStockError as exc:
                raise ValidationError(
                    f"{exc} "
                    f'Stock changed while processing; retry or check "{loc_label}".',
                ) from exc
            except InventoryError as exc:
                raise ValidationError(str(exc)) from exc

            dispatch.is_processed = True
            dispatch.save(update_fields=["is_processed", "updated_at"])

            if full_ship or not sales_order.lines.filter(
                quantity__gt=0,
            ).exists():
                sales_order.status = SalesOrderStatus.FULFILLED
            else:
                sales_order.status = SalesOrderStatus.CONFIRMED
            sales_order.save(update_fields=["status", "updated_at"])

        return dispatch

    def _auto_reserve_lines(self, sales_order, *, confirmed_by, default_location):
        """Create reservations for lines whose products have auto-reserve rules."""
        lines = sales_order.lines.select_related("product").all()
        tenant = getattr(sales_order, "tenant", None)

        for line in lines:
            rule = ReservationRule.get_rule_for_product(
                line.product, tenant=tenant,
            )
            if rule is None or not rule.auto_reserve_on_order:
                continue

            location = default_location
            if location is None:
                logger.warning(
                    "Auto-reservation skipped for %s on SO %s: "
                    "no default_location provided.",
                    line.product.sku,
                    sales_order.order_number,
                )
                continue

            self._reservation_service.create_reservation(
                product=line.product,
                location=location,
                quantity=line.quantity,
                sales_order=sales_order,
                reserved_by=confirmed_by,
                notes=f"Auto-reserved on order confirmation ({sales_order.order_number})",
                auto_assign_lot=True,
            )
