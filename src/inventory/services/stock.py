"""Stock movement processing service.

This module owns the transactional business logic for creating stock
movements and updating stock records.  All callers (views, management
commands, tests) should use :class:`StockService` rather than calling
``StockMovement.save()`` directly.

The project adopts **OOP as the standard paradigm** for service layers.
Each service is a class whose public methods represent domain operations.
This makes services easy to subclass, mock in tests, and extend with
shared state (e.g. the requesting user) when needed.
"""

from __future__ import annotations

import logging
from datetime import date

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q, QuerySet

from inventory.exceptions import (
    InsufficientStockError,
    LocationCapacityExceededError,
    LotTrackingRequiredError,
    MovementWarehouseScopeError,
)
from inventory.models.audit import AuditAction
from inventory.models.lot import StockLot, StockMovementLot
from inventory.models.product import TrackingMode
from inventory.models.stock import MovementType, StockMovement, StockRecord
from inventory.services.audit import AuditService
from inventory.services.cache import invalidate_dashboard, invalidate_stock_record

logger = logging.getLogger(__name__)

_MOVEMENT_AUDIT_ACTIONS: dict[str, str] = {
    MovementType.RECEIVE: AuditAction.STOCK_RECEIVED,
    MovementType.ISSUE: AuditAction.STOCK_ISSUED,
    MovementType.TRANSFER: AuditAction.STOCK_TRANSFERRED,
    MovementType.ADJUSTMENT: AuditAction.STOCK_ADJUSTED,
}


def filter_stock_locations_by_warehouse_scope(
    queryset: QuerySet,
    *,
    tenant_id: int,
    warehouse_id: int | None,
) -> QuerySet:
    """Narrow a :class:`~inventory.models.stock.StockLocation` queryset to one tree partition.

    Partitions match :class:`~inventory.models.stock.StockLocation` tree scope:
    ``(tenant_id, warehouse_id)`` where ``warehouse_id`` of ``None`` is the
    retail-only forest (``warehouse`` unset).
    """
    return queryset.filter(tenant_id=tenant_id, warehouse_id=warehouse_id)


def filter_stock_records_by_warehouse_scope(
    queryset: QuerySet,
    *,
    tenant_id: int,
    warehouse_id: int | None,
) -> QuerySet:
    """Filter :class:`~inventory.models.stock.StockRecord` rows by location warehouse scope."""
    return queryset.filter(
        tenant_id=tenant_id,
        location__warehouse_id=warehouse_id,
    )


def filter_stock_movements_by_warehouse_scope(
    queryset: QuerySet,
    *,
    tenant_id: int,
    warehouse_id: int | None,
) -> QuerySet:
    """Stock movements whose source or destination lies in the given warehouse scope.

    Useful for dashboards and exports scoped to one facility or to retail-only
    locations (``warehouse_id=None``).
    """
    if warehouse_id is None:
        leg = Q(from_location__warehouse_id__isnull=True) | Q(
            to_location__warehouse_id__isnull=True,
        )
    else:
        leg = Q(from_location__warehouse_id=warehouse_id) | Q(
            to_location__warehouse_id=warehouse_id,
        )
    return queryset.filter(tenant_id=tenant_id).filter(leg)


def validate_movement_location_scope(
    *,
    product,
    movement_type: str,
    from_location=None,
    to_location=None,
) -> None:
    """Validate tenant alignment and warehouse scope rules before persisting a movement.

    * Every involved location must belong to the same tenant as ``product``.
    * **Transfer** and two-sided **adjustment**: facility-linked locations
      (``warehouse`` set) cannot be paired with retail-only locations
      (``warehouse`` null). Pure retail–retail and facility–facility (including
      **cross-warehouse** between two facilities) are allowed.

    Raises
    ------
    django.core.exceptions.ValidationError
        Tenant mismatch on a location field.
    MovementWarehouseScopeError
        Mixed retail vs facility-linked scope on transfer / two-sided adjustment.
    """
    tenant_id = product.tenant_id

    def _ensure_location_tenant(field: str, loc) -> None:
        if loc is None:
            return
        if loc.tenant_id != tenant_id:
            raise ValidationError(
                {field: "Location must belong to the same tenant as the product."}
            )

    mt = movement_type

    if mt == MovementType.RECEIVE:
        _ensure_location_tenant("to_location", to_location)
    elif mt == MovementType.ISSUE:
        _ensure_location_tenant("from_location", from_location)
    elif mt == MovementType.TRANSFER:
        _ensure_location_tenant("from_location", from_location)
        _ensure_location_tenant("to_location", to_location)
        _assert_no_mixed_warehouse_scope(from_location, to_location)
    elif mt == MovementType.ADJUSTMENT:
        _ensure_location_tenant("from_location", from_location)
        _ensure_location_tenant("to_location", to_location)
        if from_location is not None and to_location is not None:
            _assert_no_mixed_warehouse_scope(from_location, to_location)
    else:
        raise ValueError(f"Unknown movement type: {movement_type}")


def _assert_no_mixed_warehouse_scope(from_location, to_location) -> None:
    """Reject one facility-linked leg and one retail-only leg."""
    if from_location is None or to_location is None:
        return
    from_wh = from_location.warehouse_id
    to_wh = to_location.warehouse_id
    if (from_wh is None) != (to_wh is None):
        raise MovementWarehouseScopeError(
            "Cannot move stock between a warehouse-linked location and a "
            "retail-only location; use locations in the same warehouse scope."
        )


class StockService:
    """Encapsulates all stock-movement business logic.

    Usage::

        service = StockService()
        movement = service.process_movement(
            product=widget,
            movement_type="receive",
            quantity=100,
            to_location=warehouse,
            unit_cost=Decimal("9.99"),
            created_by=request.user,
        )

    The class is intentionally **stateless** — you can instantiate it per
    request or keep a module-level singleton.  An optional
    ``audit_service`` can be injected for testing; a default
    :class:`~inventory.services.audit.AuditService` is created otherwise.
    """

    def __init__(self, *, audit_service: AuditService | None = None):
        self._audit_service = audit_service or AuditService()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process_movement(
        self,
        *,
        product,
        movement_type: str,
        quantity: int,
        from_location=None,
        to_location=None,
        unit_cost=None,
        reference: str = "",
        notes: str = "",
        created_by=None,
    ) -> StockMovement:
        """Create a :class:`StockMovement` and update stock records atomically.

        This is the **single entry-point** for recording stock changes.
        It wraps validation, persistence, and stock-record updates inside
        a single ``transaction.atomic()`` block with
        ``select_for_update()`` row locking to prevent race conditions.

        Parameters
        ----------
        product : inventory.models.Product
            The product being moved.
        movement_type : str
            One of :class:`MovementType` values (``receive``, ``issue``,
            ``transfer``, ``adjustment``).
        quantity : int
            Positive integer — the amount to move.
        from_location : inventory.models.StockLocation | None
            Source location (required for ``issue`` and ``transfer``).
        to_location : inventory.models.StockLocation | None
            Destination location (required for ``receive`` and
            ``transfer``).
        unit_cost : Decimal | None
            Per-unit cost at the time of this movement.
        reference : str
            Optional external reference (PO/SO number, etc.).
        notes : str
            Optional free-text notes.
        created_by : User | None
            The user who triggered the movement.

        Returns
        -------
        StockMovement
            The persisted, fully-processed movement instance.

        Raises
        ------
        inventory.exceptions.InsufficientStockError
            If stock is insufficient or no stock record exists.
        django.core.exceptions.ValidationError
            If location rules are violated (from model-level clean).
        ValueError
            If the movement type is unknown.
        MovementWarehouseScopeError
            If a transfer mixes facility-linked and retail-only locations.
        """
        validate_movement_location_scope(
            product=product,
            movement_type=movement_type,
            from_location=from_location,
            to_location=to_location,
        )
        movement = StockMovement(
            product=product,
            movement_type=movement_type,
            quantity=quantity,
            from_location=from_location,
            to_location=to_location,
            unit_cost=unit_cost,
            reference=reference,
            notes=notes,
            created_by=created_by,
            tenant=product.tenant,
        )

        # full_clean() enforces field validation + the model's clean().
        movement.full_clean()

        with transaction.atomic():
            movement.save()
            self._dispatch(movement)
            self._log_movement_audit(movement)

        self._invalidate_caches(movement)
        return movement

    def process_movement_with_lots(
        self,
        *,
        product,
        movement_type: str,
        quantity: int,
        from_location=None,
        to_location=None,
        lot_number: str | None = None,
        serial_number: str = "",
        manufacturing_date: date | None = None,
        expiry_date: date | None = None,
        allocation_strategy: str = "FIFO",
        manual_lot_allocations: list[dict] | None = None,
        unit_cost=None,
        reference: str = "",
        notes: str = "",
        created_by=None,
    ) -> StockMovement:
        """Create a lot-aware :class:`StockMovement` with automatic allocation.

        Extends :meth:`process_movement` with batch/lot tracking:

        * **RECEIVE** — creates or updates a :class:`StockLot` and links
          it via :class:`StockMovementLot`.
        * **ISSUE** — allocates from existing lots using FIFO, LIFO, or
          MANUAL strategy; decrements ``quantity_remaining`` atomically.
        * **TRANSFER** — records lot lineage via :class:`StockMovementLot`
          without decrementing ``quantity_remaining`` (stock relocates,
          not consumed).
        * **ADJUSTMENT** — optionally targets a specific lot or falls
          back to FIFO/LIFO allocation.

        Parameters
        ----------
        lot_number : str | None
            Lot/batch identifier.  Required for RECEIVE when the product's
            ``tracking_mode`` is ``"required"``.  For ADJUSTMENT, targets
            a specific lot.
        allocation_strategy : str
            ``"FIFO"`` (default), ``"LIFO"``, or ``"MANUAL"``.
        manual_lot_allocations : list[dict] | None
            Required when ``allocation_strategy="MANUAL"``.  Each dict
            must have ``lot_id`` (int) and ``quantity`` (int) keys.

        Raises
        ------
        LotTrackingRequiredError
            Product ``tracking_mode`` is ``"required"`` but no lot info
            was provided for a RECEIVE movement.
        InsufficientStockError
            Stock-record or lot quantities are insufficient.
        """
        tracking_mode = getattr(product, "tracking_mode", TrackingMode.OPTIONAL)

        if tracking_mode == TrackingMode.NONE:
            return self.process_movement(
                product=product,
                movement_type=movement_type,
                quantity=quantity,
                from_location=from_location,
                to_location=to_location,
                unit_cost=unit_cost,
                reference=reference,
                notes=notes,
                created_by=created_by,
            )

        if (
            tracking_mode == TrackingMode.REQUIRED
            and movement_type == MovementType.RECEIVE
            and not lot_number
        ):
            raise LotTrackingRequiredError(
                f"Product {product.sku} requires lot tracking "
                f"but no lot information was provided."
            )

        validate_movement_location_scope(
            product=product,
            movement_type=movement_type,
            from_location=from_location,
            to_location=to_location,
        )
        movement = StockMovement(
            product=product,
            movement_type=movement_type,
            quantity=quantity,
            from_location=from_location,
            to_location=to_location,
            unit_cost=unit_cost,
            reference=reference,
            notes=notes,
            created_by=created_by,
            tenant=product.tenant,
        )
        movement.full_clean()

        with transaction.atomic():
            movement.save()
            self._dispatch(movement)
            self._process_lot_operations(
                movement=movement,
                lot_number=lot_number,
                serial_number=serial_number,
                manufacturing_date=manufacturing_date,
                expiry_date=expiry_date,
                allocation_strategy=allocation_strategy,
                manual_lot_allocations=manual_lot_allocations,
            )
            self._log_movement_audit(movement)

        self._invalidate_caches(movement)
        return movement

    # ------------------------------------------------------------------
    # Cache invalidation
    # ------------------------------------------------------------------

    @staticmethod
    def _invalidate_caches(movement: StockMovement) -> None:
        """Bust stock-record and dashboard caches for affected locations."""
        product_id = movement.product_id
        if movement.from_location_id:
            invalidate_stock_record(product_id, movement.from_location_id)
        if movement.to_location_id:
            invalidate_stock_record(product_id, movement.to_location_id)
        invalidate_dashboard()

    # ------------------------------------------------------------------
    # Internal helpers (private)
    # ------------------------------------------------------------------

    def _dispatch(self, movement: StockMovement) -> None:
        """Route to the correct handler based on ``movement_type``."""
        handler = {
            MovementType.RECEIVE: self._process_receive,
            MovementType.ISSUE: self._process_issue,
            MovementType.TRANSFER: self._process_transfer,
            MovementType.ADJUSTMENT: self._process_adjustment,
        }.get(movement.movement_type)

        if handler is None:
            raise ValueError(
                f"Unknown movement type: {movement.movement_type}"
            )
        handler(movement)

    def _get_or_create_record(
        self, product, location,
    ) -> StockRecord:
        """Return a locked :class:`StockRecord`, creating one if needed."""
        record, _created = (
            StockRecord.objects.select_for_update().get_or_create(
                product=product,
                location=location,
                defaults={"tenant": product.tenant},
            )
        )
        return record

    def _get_record_for_decrement(
        self, product, location, quantity,
    ) -> StockRecord:
        """Return a locked :class:`StockRecord` after validating stock."""
        try:
            record = StockRecord.objects.select_for_update().get(
                product=product,
                location=location,
            )
        except StockRecord.DoesNotExist:
            raise InsufficientStockError(
                f"No stock record for {product.sku} at {location.name}."
            )
        if record.quantity < quantity:
            raise InsufficientStockError(
                f"Insufficient stock for {product.sku} at "
                f"{location.name}: available {record.quantity}, "
                f"requested {quantity}."
            )
        return record

    def _check_capacity(self, location, quantity: int) -> None:
        """Raise if *location* cannot accept *quantity* more units."""
        if not location.can_accept(quantity):
            raise LocationCapacityExceededError(
                f"Location '{location.name}' cannot accept {quantity} units "
                f"(capacity: {location.max_capacity}, "
                f"current utilization: {location.current_utilization})."
            )

    def _process_receive(self, movement: StockMovement) -> None:
        """Receive: increment stock at ``to_location``."""
        self._check_capacity(movement.to_location, movement.quantity)
        record = self._get_or_create_record(
            movement.product, movement.to_location,
        )
        record.quantity += movement.quantity
        record.save(update_fields=["quantity", "updated_at"])

    def _process_issue(self, movement: StockMovement) -> None:
        """Issue: decrement stock at ``from_location``."""
        record = self._get_record_for_decrement(
            movement.product, movement.from_location, movement.quantity,
        )
        record.quantity -= movement.quantity
        record.save(update_fields=["quantity", "updated_at"])

    def _process_transfer(self, movement: StockMovement) -> None:
        """Transfer: decrement source, increment destination."""
        self._check_capacity(movement.to_location, movement.quantity)
        source = self._get_record_for_decrement(
            movement.product, movement.from_location, movement.quantity,
        )
        dest = self._get_or_create_record(
            movement.product, movement.to_location,
        )

        source.quantity -= movement.quantity
        source.save(update_fields=["quantity", "updated_at"])

        dest.quantity += movement.quantity
        dest.save(update_fields=["quantity", "updated_at"])

    def _process_adjustment(self, movement: StockMovement) -> None:
        """Adjustment: decrement ``from_location`` and/or increment ``to_location``."""
        if movement.from_location:
            record = self._get_record_for_decrement(
                movement.product, movement.from_location, movement.quantity,
            )
            record.quantity -= movement.quantity
            record.save(update_fields=["quantity", "updated_at"])

        if movement.to_location:
            self._check_capacity(movement.to_location, movement.quantity)
            record = self._get_or_create_record(
                movement.product, movement.to_location,
            )
            record.quantity += movement.quantity
            record.save(update_fields=["quantity", "updated_at"])

    # ------------------------------------------------------------------
    # Lot helpers (private)
    # ------------------------------------------------------------------

    def _process_lot_operations(
        self,
        *,
        movement: StockMovement,
        lot_number: str | None,
        serial_number: str,
        manufacturing_date,
        expiry_date,
        allocation_strategy: str,
        manual_lot_allocations: list[dict] | None,
    ) -> None:
        """Dispatch lot-specific logic based on movement type."""
        mt = movement.movement_type

        if mt == MovementType.RECEIVE:
            self._lot_receive(
                movement=movement,
                lot_number=lot_number,
                serial_number=serial_number,
                manufacturing_date=manufacturing_date,
                expiry_date=expiry_date,
            )
        elif mt == MovementType.ISSUE:
            self._lot_allocate_and_decrement(
                movement=movement,
                allocation_strategy=allocation_strategy,
                manual_lot_allocations=manual_lot_allocations,
            )
        elif mt == MovementType.TRANSFER:
            self._lot_transfer(
                movement=movement,
                allocation_strategy=allocation_strategy,
                manual_lot_allocations=manual_lot_allocations,
            )
        elif mt == MovementType.ADJUSTMENT:
            self._lot_adjustment(
                movement=movement,
                lot_number=lot_number,
                serial_number=serial_number,
                manufacturing_date=manufacturing_date,
                expiry_date=expiry_date,
                allocation_strategy=allocation_strategy,
                manual_lot_allocations=manual_lot_allocations,
            )

    def _lot_receive(
        self,
        *,
        movement: StockMovement,
        lot_number: str | None,
        serial_number: str,
        manufacturing_date,
        expiry_date,
    ) -> StockLot | None:
        """Create or update a StockLot for a receive-type operation."""
        if not lot_number:
            return None

        lot, created = StockLot.objects.select_for_update().get_or_create(
            product=movement.product,
            lot_number=lot_number,
            tenant=movement.product.tenant,
            defaults={
                "serial_number": serial_number or "",
                "manufacturing_date": manufacturing_date,
                "expiry_date": expiry_date,
                "quantity_received": movement.quantity,
                "quantity_remaining": movement.quantity,
                "received_date": date.today(),
                "created_by": movement.created_by,
            },
        )

        if not created:
            lot.quantity_received += movement.quantity
            lot.quantity_remaining += movement.quantity
            lot.save(update_fields=[
                "quantity_received", "quantity_remaining", "updated_at",
            ])

        # get_or_create handles the adjustment edge case where the same
        # lot appears on both the from- and to-location side.
        sml, sml_created = StockMovementLot.objects.get_or_create(
            stock_movement=movement,
            stock_lot=lot,
            defaults={"quantity": movement.quantity},
        )
        if not sml_created:
            sml.quantity += movement.quantity
            sml.save(update_fields=["quantity"])

        return lot

    def _allocate_from_lots(
        self,
        *,
        product,
        quantity: int,
        strategy: str,
        manual_allocations: list[dict] | None = None,
    ) -> list[tuple[StockLot, int]]:
        """Select lots and compute per-lot quantities for allocation.

        Returns ``(lot, allocated_qty)`` tuples.  Rows are locked with
        ``select_for_update`` to prevent concurrent modifications.
        """
        if strategy == "MANUAL":
            if not manual_allocations:
                raise ValueError(
                    "Manual allocation strategy requires "
                    "manual_lot_allocations."
                )
            return self._allocate_manual(product, quantity, manual_allocations)

        ordering = (
            "received_date" if strategy == "FIFO" else "-received_date"
        )
        lots = (
            StockLot.objects
            .select_for_update()
            .filter(
                product=product,
                is_active=True,
                quantity_remaining__gt=0,
            )
            .order_by(ordering)
        )

        allocations: list[tuple[StockLot, int]] = []
        remaining = quantity

        for lot in lots:
            if remaining <= 0:
                break
            allocated = min(lot.quantity_remaining, remaining)
            allocations.append((lot, allocated))
            remaining -= allocated

        if remaining > 0:
            available = quantity - remaining
            raise InsufficientStockError(
                f"Insufficient lot quantity for {product.sku}: "
                f"needed {quantity}, available across lots {available}."
            )

        return allocations

    def _allocate_manual(
        self, product, quantity: int, manual_allocations: list[dict],
    ) -> list[tuple[StockLot, int]]:
        """Validate and return manually specified lot allocations."""
        total = sum(a["quantity"] for a in manual_allocations)
        if total != quantity:
            raise ValueError(
                f"Manual lot allocations total ({total}) does not match "
                f"movement quantity ({quantity})."
            )

        result: list[tuple[StockLot, int]] = []
        for alloc in manual_allocations:
            lot = (
                StockLot.objects
                .select_for_update()
                .get(pk=alloc["lot_id"], product=product)
            )
            if lot.quantity_remaining < alloc["quantity"]:
                raise InsufficientStockError(
                    f"Lot {lot.lot_number} has {lot.quantity_remaining} "
                    f"remaining but {alloc['quantity']} was requested."
                )
            result.append((lot, alloc["quantity"]))

        return result

    def _lot_allocate_and_decrement(
        self,
        *,
        movement: StockMovement,
        allocation_strategy: str,
        manual_lot_allocations: list[dict] | None,
    ) -> None:
        """Allocate from lots and decrement ``quantity_remaining`` (ISSUE)."""
        allocations = self._allocate_from_lots(
            product=movement.product,
            quantity=movement.quantity,
            strategy=allocation_strategy,
            manual_allocations=manual_lot_allocations,
        )

        for lot, qty in allocations:
            lot.quantity_remaining -= qty
            lot.save(update_fields=["quantity_remaining", "updated_at"])
            StockMovementLot.objects.create(
                stock_movement=movement,
                stock_lot=lot,
                quantity=qty,
            )

    def _lot_transfer(
        self,
        *,
        movement: StockMovement,
        allocation_strategy: str,
        manual_lot_allocations: list[dict] | None,
    ) -> None:
        """Record lot lineage for transfers without decrementing.

        Transfers relocate stock; the lot's ``quantity_remaining`` is
        unchanged because the stock isn't consumed.  StockMovementLot
        entries provide traceability.
        """
        allocations = self._allocate_from_lots(
            product=movement.product,
            quantity=movement.quantity,
            strategy=allocation_strategy,
            manual_allocations=manual_lot_allocations,
        )

        for lot, qty in allocations:
            StockMovementLot.objects.create(
                stock_movement=movement,
                stock_lot=lot,
                quantity=qty,
            )

    def _lot_adjustment(
        self,
        *,
        movement: StockMovement,
        lot_number: str | None,
        serial_number: str,
        manufacturing_date,
        expiry_date,
        allocation_strategy: str,
        manual_lot_allocations: list[dict] | None,
    ) -> None:
        """Handle lot operations for adjustments.

        Negative adjustments (from_location) decrement lot quantities
        targeting a specific lot or using FIFO/LIFO/MANUAL.
        Positive adjustments (to_location) create or add to a lot.
        """
        if movement.from_location:
            if lot_number and not manual_lot_allocations:
                lot = StockLot.objects.select_for_update().get(
                    product=movement.product,
                    lot_number=lot_number,
                    tenant=movement.product.tenant,
                )
                if lot.quantity_remaining < movement.quantity:
                    raise InsufficientStockError(
                        f"Lot {lot.lot_number} has "
                        f"{lot.quantity_remaining} remaining but "
                        f"{movement.quantity} was requested."
                    )
                allocations = [(lot, movement.quantity)]
            else:
                allocations = self._allocate_from_lots(
                    product=movement.product,
                    quantity=movement.quantity,
                    strategy=allocation_strategy,
                    manual_allocations=manual_lot_allocations,
                )

            for lot, qty in allocations:
                lot.quantity_remaining -= qty
                lot.save(update_fields=["quantity_remaining", "updated_at"])
                StockMovementLot.objects.create(
                    stock_movement=movement,
                    stock_lot=lot,
                    quantity=qty,
                )

        if movement.to_location:
            self._lot_receive(
                movement=movement,
                lot_number=lot_number,
                serial_number=serial_number,
                manufacturing_date=manufacturing_date,
                expiry_date=expiry_date,
            )

    # ------------------------------------------------------------------
    # Audit logging
    # ------------------------------------------------------------------

    def _log_movement_audit(self, movement: StockMovement) -> None:
        """Record a compliance audit entry for a processed stock movement.

        Skipped silently when the product has no tenant (e.g. in legacy
        data or tests that don't set up multi-tenancy).
        """
        tenant = (
            getattr(movement.product, "tenant", None)
            or getattr(movement, "tenant", None)
        )
        if tenant is None:
            return

        action = _MOVEMENT_AUDIT_ACTIONS.get(movement.movement_type)
        if action is None:
            return

        details: dict = {
            "movement_id": movement.pk,
            "quantity": movement.quantity,
        }
        if movement.from_location:
            details["from_location"] = movement.from_location.name
        if movement.to_location:
            details["to_location"] = movement.to_location.name
        if movement.reference:
            details["reference"] = movement.reference
        if movement.unit_cost is not None:
            details["unit_cost"] = str(movement.unit_cost)

        self._audit_service.log(
            tenant=tenant,
            action=action,
            user=movement.created_by,
            product=movement.product,
            **details,
        )
