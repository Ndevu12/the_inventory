"""Sales service for sales order and dispatch workflows.

Follows the project's OOP service-layer convention.  All sales-order
state transitions and dispatch/issuing logic lives here rather than in
model ``save()`` methods or view code.
"""

from __future__ import annotations

import logging

from django.core.exceptions import ValidationError
from django.db import transaction

from inventory.exceptions import InventoryError
from inventory.models.reservation import ReservationRule
from inventory.models.stock import MovementType
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

    def process_dispatch(self, *, dispatch, dispatched_by=None):
        """Process a dispatch: issue stock for each sales order line.

        Creates an ``issue`` StockMovement for each line on the
        associated sales order, decrementing stock at the dispatch's
        source location.  Marks the dispatch as processed and
        transitions the SO to fulfilled status.

        The entire operation is wrapped in a transaction — if any
        movement fails (e.g. insufficient stock), nothing is persisted.
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

        with transaction.atomic():
            try:
                for line in lines:
                    self._stock_service.process_movement(
                        product=line.product,
                        movement_type=MovementType.ISSUE,
                        quantity=line.quantity,
                        from_location=dispatch.from_location,
                        unit_cost=line.product.unit_cost,
                        reference=dispatch.dispatch_number,
                        created_by=dispatched_by,
                    )
            except InventoryError as exc:
                raise ValidationError(str(exc)) from exc

            dispatch.is_processed = True
            dispatch.save(update_fields=["is_processed", "updated_at"])

            so.status = SalesOrderStatus.FULFILLED
            so.save(update_fields=["status", "updated_at"])

        return dispatch

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

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
