"""Procurement service for purchase order and goods receiving workflows.

Follows the project's OOP service-layer convention.  All purchase-order
state transitions and stock-receiving logic lives here rather than in
model ``save()`` methods or view code.
"""

from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import transaction

from inventory.models.stock import MovementType
from inventory.services.stock import StockService

from procurement.models.order import PurchaseOrderStatus


class ProcurementService:
    """Encapsulates procurement business logic.

    Usage::

        service = ProcurementService()
        service.confirm_order(purchase_order=po)
        service.receive_goods(goods_received_note=grn, received_by=user)
    """

    def __init__(self):
        self._stock_service = StockService()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def confirm_order(self, *, purchase_order, confirmed_by=None):
        """Transition a purchase order from draft to confirmed.

        Validates that the order is in draft status and has at least
        one line item before confirming.

        Returns the updated purchase order.
        """
        if purchase_order.status != PurchaseOrderStatus.DRAFT:
            raise ValidationError(
                f"Only draft orders can be confirmed. "
                f"Current status: {purchase_order.get_status_display()}."
            )
        if not purchase_order.lines.exists():
            raise ValidationError(
                "Cannot confirm a purchase order with no line items."
            )

        purchase_order.status = PurchaseOrderStatus.CONFIRMED
        if confirmed_by:
            purchase_order.created_by = purchase_order.created_by or confirmed_by
        purchase_order.save(update_fields=["status", "updated_at"])
        return purchase_order

    def cancel_order(self, *, purchase_order, cancelled_by=None):
        """Cancel a purchase order.

        Only draft or confirmed orders can be cancelled.  Received
        orders cannot be cancelled — corrective adjustments should
        be used instead.
        """
        allowed = {PurchaseOrderStatus.DRAFT, PurchaseOrderStatus.CONFIRMED}
        if purchase_order.status not in allowed:
            raise ValidationError(
                f"Only draft or confirmed orders can be cancelled. "
                f"Current status: {purchase_order.get_status_display()}."
            )

        purchase_order.status = PurchaseOrderStatus.CANCELLED
        purchase_order.save(update_fields=["status", "updated_at"])
        return purchase_order

    def receive_goods(self, *, goods_received_note, received_by=None):
        """Process a goods received note.

        Creates a ``receive`` StockMovement for each line on the
        associated purchase order, updating stock at the GRN's
        location.  Marks the GRN as processed and transitions the
        PO to received status.

        The entire operation is wrapped in a transaction — if any
        movement fails, nothing is persisted.
        """
        if goods_received_note.is_processed:
            raise ValidationError(
                "This goods received note has already been processed."
            )

        po = goods_received_note.purchase_order
        if po.status != PurchaseOrderStatus.CONFIRMED:
            raise ValidationError(
                f"Purchase order must be confirmed before receiving goods. "
                f"Current status: {po.get_status_display()}."
            )

        lines = po.lines.select_related("product").all()
        if not lines.exists():
            raise ValidationError(
                "The purchase order has no line items to receive."
            )

        with transaction.atomic():
            for line in lines:
                self._stock_service.process_movement(
                    product=line.product,
                    movement_type=MovementType.RECEIVE,
                    quantity=line.quantity,
                    to_location=goods_received_note.location,
                    unit_cost=line.unit_cost,
                    reference=goods_received_note.grn_number,
                    created_by=received_by,
                )

            goods_received_note.is_processed = True
            goods_received_note.save(update_fields=["is_processed", "updated_at"])

            po.status = PurchaseOrderStatus.RECEIVED
            po.save(update_fields=["status", "updated_at"])

        return goods_received_note
