"""Reservation business logic service.

Owns the transactional lifecycle for :class:`StockReservation`:
create, fulfill, cancel, and expire.  All callers (views, management
commands, tests) should use :class:`ReservationService` rather than
manipulating reservation records directly.

The project adopts **OOP as the standard paradigm** for service layers.
See :mod:`inventory.services.stock` for the same pattern.
"""

from __future__ import annotations

import logging
from datetime import timedelta

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from inventory.exceptions import InsufficientStockError, ReservationConflictError
from inventory.models.audit import AuditAction
from inventory.models.lot import StockLot
from inventory.models.reservation import ReservationRule, ReservationStatus, StockReservation
from inventory.models.stock import MovementType, StockRecord
from inventory.services.audit import AuditService
from inventory.services.cache import invalidate_dashboard, invalidate_stock_record
from inventory.services.stock import StockService

logger = logging.getLogger(__name__)

_CANCELLABLE_STATUSES = frozenset({
    ReservationStatus.PENDING,
    ReservationStatus.CONFIRMED,
})

_FULFILLABLE_STATUSES = frozenset({
    ReservationStatus.PENDING,
    ReservationStatus.CONFIRMED,
})

DEFAULT_RESERVATION_TTL = timedelta(hours=24)


class ReservationService:
    """Encapsulates reservation lifecycle business logic.

    Usage::

        service = ReservationService()
        reservation = service.create_reservation(
            product=widget,
            location=warehouse,
            quantity=10,
            reserved_by=request.user,
        )
        movement = service.fulfill_reservation(reservation, created_by=request.user)

    The class is **stateless** — instantiate per request or keep a
    module-level singleton.  ``stock_service`` and ``audit_service``
    can be injected for testing.
    """

    def __init__(
        self,
        *,
        stock_service: StockService | None = None,
        audit_service: AuditService | None = None,
    ):
        self._stock_service = stock_service or StockService()
        self._audit_service = audit_service or AuditService()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create_reservation(
        self,
        *,
        product,
        location,
        quantity: int,
        sales_order=None,
        reserved_by=None,
        expires_at=None,
        notes: str = "",
        stock_lot=None,
        auto_assign_lot: bool = False,
    ) -> StockReservation:
        """Reserve stock at a product+location, optionally targeting a lot.

        Locks the :class:`StockRecord` row and verifies that
        ``available_quantity >= quantity`` before creating the
        reservation.  A default ``expires_at`` is set when none is
        provided.

        Parameters
        ----------
        product : inventory.models.Product
        location : inventory.models.StockLocation
        quantity : int
            Must be positive.
        sales_order : sales.models.SalesOrder | None
        reserved_by : User | None
        expires_at : datetime | None
            Falls back to ``now + DEFAULT_RESERVATION_TTL``.
        notes : str
        stock_lot : inventory.models.StockLot | None
            Explicitly reserve against this lot.
        auto_assign_lot : bool
            When ``True`` and ``stock_lot`` is not provided, attempt to
            pick a lot using the product's :class:`ReservationRule`
            allocation strategy (FIFO/LIFO).

        Returns
        -------
        StockReservation

        Raises
        ------
        InsufficientStockError
            Available quantity is less than the requested amount.
        """
        if quantity <= 0:
            raise ValueError("Reservation quantity must be positive.")

        if expires_at is None:
            expires_at = timezone.now() + DEFAULT_RESERVATION_TTL

        with transaction.atomic():
            available = self._get_available_quantity_locked(product, location)

            if available < quantity:
                raise InsufficientStockError(
                    f"Cannot reserve {quantity} of {product.sku} at "
                    f"{location.name}: only {available} available."
                )

            if stock_lot is None and auto_assign_lot:
                stock_lot = self._auto_select_lot(product, quantity)

            reservation = StockReservation.objects.create(
                product=product,
                location=location,
                quantity=quantity,
                sales_order=sales_order,
                reserved_by=reserved_by,
                expires_at=expires_at,
                status=ReservationStatus.PENDING,
                notes=notes,
                stock_lot=stock_lot,
            )

        self._log_audit(
            reservation,
            action=AuditAction.RESERVATION_CREATED,
            user=reserved_by,
            quantity=quantity,
            lot=stock_lot.lot_number if stock_lot else None,
        )

        self._invalidate_caches(product.pk, location.pk)

        logger.info(
            "Reservation %s created: %s x%d at %s (lot=%s)",
            reservation.pk, product.sku, quantity, location.name,
            stock_lot.lot_number if stock_lot else "none",
        )
        return reservation

    def fulfill_reservation(
        self, reservation: StockReservation, *, created_by=None,
    ):
        """Fulfill a reservation by issuing stock.

        When the reservation is linked to a :class:`StockLot`, uses
        :meth:`StockService.process_movement_with_lots` with a MANUAL
        allocation targeting that specific lot.  Otherwise falls back to
        the standard :meth:`StockService.process_movement`.

        Parameters
        ----------
        reservation : StockReservation
            Must be in PENDING or CONFIRMED status.
        created_by : User | None

        Returns
        -------
        StockMovement

        Raises
        ------
        ReservationConflictError
            Reservation is not in a fulfillable state.
        """
        if reservation.status not in _FULFILLABLE_STATUSES:
            raise ReservationConflictError(
                f"Cannot fulfill reservation {reservation.pk}: "
                f"current status is '{reservation.get_status_display()}'."
            )

        with transaction.atomic():
            locked = (
                StockReservation.objects
                .select_for_update()
                .select_related("stock_lot")
                .get(pk=reservation.pk)
            )
            if locked.status not in _FULFILLABLE_STATUSES:
                raise ReservationConflictError(
                    f"Cannot fulfill reservation {locked.pk}: "
                    f"status changed to '{locked.get_status_display()}'."
                )

            movement = self._create_fulfillment_movement(locked, created_by)

            locked.status = ReservationStatus.FULFILLED
            locked.fulfilled_movement = movement
            locked.save(update_fields=["status", "fulfilled_movement", "updated_at"])

        reservation.refresh_from_db()

        self._log_audit(
            reservation,
            action=AuditAction.RESERVATION_FULFILLED,
            user=created_by,
            movement_id=movement.pk,
            lot=reservation.stock_lot.lot_number if reservation.stock_lot else None,
        )

        logger.info("Reservation %s fulfilled (movement %s).", reservation.pk, movement.pk)
        return movement

    def cancel_reservation(self, reservation: StockReservation) -> None:
        """Cancel a PENDING or CONFIRMED reservation, releasing reserved qty.

        Parameters
        ----------
        reservation : StockReservation

        Raises
        ------
        ReservationConflictError
            Reservation is not in a cancellable state.
        """
        if reservation.status not in _CANCELLABLE_STATUSES:
            raise ReservationConflictError(
                f"Cannot cancel reservation {reservation.pk}: "
                f"current status is '{reservation.get_status_display()}'."
            )

        with transaction.atomic():
            locked = (
                StockReservation.objects
                .select_for_update()
                .get(pk=reservation.pk)
            )
            if locked.status not in _CANCELLABLE_STATUSES:
                raise ReservationConflictError(
                    f"Cannot cancel reservation {locked.pk}: "
                    f"status changed to '{locked.get_status_display()}'."
                )

            locked.status = ReservationStatus.CANCELLED
            locked.save(update_fields=["status", "updated_at"])

        reservation.refresh_from_db()

        self._log_audit(
            reservation,
            action=AuditAction.RESERVATION_CANCELLED,
            user=reservation.reserved_by,
        )

        self._invalidate_caches(reservation.product_id, reservation.location_id)

        logger.info("Reservation %s cancelled.", reservation.pk)

    def expire_stale_reservations(self) -> int:
        """Bulk-expire reservations past their ``expires_at``.

        Designed to be called by a management command or periodic task.

        Returns
        -------
        int
            Number of reservations expired.
        """
        now = timezone.now()
        with transaction.atomic():
            stale_qs = (
                StockReservation.objects
                .select_for_update()
                .filter(
                    status__in=list(_CANCELLABLE_STATUSES),
                    expires_at__lte=now,
                )
            )
            count = stale_qs.update(status=ReservationStatus.EXPIRED)

        if count:
            invalidate_dashboard()
            logger.info("Expired %d stale reservation(s).", count)
        return count

    def get_available_quantity(self, product, location) -> int:
        """Return stock quantity minus active reservation totals.

        Does **not** acquire row locks — suitable for read-only display.
        """
        try:
            record = StockRecord.objects.get(
                product=product, location=location,
            )
        except StockRecord.DoesNotExist:
            return 0

        reserved = self._sum_active_reservations(product, location)
        return max(record.quantity - reserved, 0)

    # ------------------------------------------------------------------
    # Cache invalidation
    # ------------------------------------------------------------------

    @staticmethod
    def _invalidate_caches(product_id: int, location_id: int) -> None:
        invalidate_stock_record(product_id, location_id)
        invalidate_dashboard()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_available_quantity_locked(self, product, location) -> int:
        """Like :meth:`get_available_quantity` but with ``select_for_update``."""
        try:
            record = StockRecord.objects.select_for_update().get(
                product=product, location=location,
            )
        except StockRecord.DoesNotExist:
            return 0

        reserved = self._sum_active_reservations(product, location)
        return max(record.quantity - reserved, 0)

    @staticmethod
    def _sum_active_reservations(product, location) -> int:
        result = (
            StockReservation.objects
            .filter(
                product=product,
                location=location,
                status__in=list(_CANCELLABLE_STATUSES),
            )
            .aggregate(total=Sum("quantity"))
        )
        return result["total"] or 0

    def _create_fulfillment_movement(self, reservation, created_by):
        """Issue stock via the appropriate StockService method.

        Uses lot-aware processing when the reservation targets a specific lot.
        """
        ref = f"Reservation #{reservation.pk}"

        if reservation.stock_lot_id:
            return self._stock_service.process_movement_with_lots(
                product=reservation.product,
                movement_type=MovementType.ISSUE,
                quantity=reservation.quantity,
                from_location=reservation.location,
                allocation_strategy="MANUAL",
                manual_lot_allocations=[{
                    "lot_id": reservation.stock_lot_id,
                    "quantity": reservation.quantity,
                }],
                reference=ref,
                created_by=created_by,
            )

        return self._stock_service.process_movement(
            product=reservation.product,
            movement_type=MovementType.ISSUE,
            quantity=reservation.quantity,
            from_location=reservation.location,
            reference=ref,
            created_by=created_by,
        )

    @staticmethod
    def _auto_select_lot(product, quantity):
        """Pick the best available lot using the product's reservation rule strategy.

        Returns a :class:`StockLot` or ``None`` if no lots are available
        or the product has no active lots.
        """
        rule = ReservationRule.get_rule_for_product(product)
        strategy = rule.allocation_strategy if rule else "FIFO"
        ordering = "received_date" if strategy == "FIFO" else "-received_date"

        lot = (
            StockLot.objects
            .filter(
                product=product,
                is_active=True,
                quantity_remaining__gte=quantity,
            )
            .order_by(ordering)
            .first()
        )
        return lot

    def _log_audit(self, reservation: StockReservation, *, action: str, user=None, **extra) -> None:
        tenant = getattr(reservation.product, "tenant", None)
        if tenant is None:
            return

        details: dict = {
            "reservation_id": reservation.pk,
            "quantity": reservation.quantity,
            "location": reservation.location.name,
        }
        details.update(extra)

        self._audit_service.log(
            tenant=tenant,
            action=action,
            user=user,
            product=reservation.product,
            **details,
        )
