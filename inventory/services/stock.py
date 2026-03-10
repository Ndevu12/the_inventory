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

from django.core.exceptions import ValidationError
from django.db import transaction

from inventory.models.stock import MovementType, StockMovement, StockRecord


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
    request or keep a module-level singleton.  If you later need
    request-scoped context (e.g. the current user for audit logging),
    accept it in ``__init__`` and store it as an instance attribute.
    """

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
        django.core.exceptions.ValidationError
            If location rules are violated, stock is insufficient, or
            the movement type is unknown.
        """
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
        )

        # full_clean() enforces field validation + the model's clean().
        movement.full_clean()

        with transaction.atomic():
            movement.save()
            self._dispatch(movement)

        return movement

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
            raise ValidationError(
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
            raise ValidationError(
                f"No stock record for {product.sku} at {location.name}."
            )
        if record.quantity < quantity:
            raise ValidationError(
                f"Insufficient stock for {product.sku} at "
                f"{location.name}: available {record.quantity}, "
                f"requested {quantity}."
            )
        return record

    def _process_receive(self, movement: StockMovement) -> None:
        """Receive: increment stock at ``to_location``."""
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
            record = self._get_or_create_record(
                movement.product, movement.to_location,
            )
            record.quantity += movement.quantity
            record.save(update_fields=["quantity", "updated_at"])
