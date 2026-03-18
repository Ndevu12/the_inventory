"""Bulk stock operations service.

Provides atomic bulk transfer, adjustment, and revalue operations that
process multiple items in a single transaction.  Each method returns a
:class:`BulkOperationResult` summarising successes, failures, and
per-item error details.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from decimal import Decimal

from django.db import transaction

from inventory.exceptions import InventoryError
from inventory.models.product import Product
from inventory.models.stock import MovementType, StockRecord
from inventory.services.stock import StockService

logger = logging.getLogger(__name__)


@dataclass
class BulkOperationResult:
    """Outcome of a bulk stock operation."""

    success_count: int = 0
    failure_count: int = 0
    errors: list[dict] = field(default_factory=list)
    results: list[dict] = field(default_factory=list)

    @property
    def total_count(self) -> int:
        return self.success_count + self.failure_count


class BulkStockService:
    """Bulk stock operations: transfer, adjustment, revalue.

    Each method wraps processing in ``transaction.atomic()``.  When
    ``fail_fast=True`` the entire batch is rolled back on the first
    error.  When ``fail_fast=False`` each item is processed in its own
    savepoint so that valid items succeed even if others fail.
    """

    def __init__(self, *, stock_service: StockService | None = None):
        self._stock_service = stock_service or StockService()

    def bulk_transfer(
        self,
        *,
        items: list[dict],
        from_location,
        to_location,
        created_by=None,
        reference: str = "",
        notes: str = "",
        fail_fast: bool = False,
    ) -> BulkOperationResult:
        """Transfer multiple products between locations.

        Each item dict requires ``product_id`` (int) and ``quantity`` (int).
        """
        result = BulkOperationResult()

        with transaction.atomic():
            for idx, item in enumerate(items):
                product_id = item.get("product_id")
                try:
                    if product_id is None:
                        raise ValueError("Missing product_id.")

                    product = Product.objects.get(pk=product_id)
                    if fail_fast:
                        movement = self._stock_service.process_movement(
                            product=product,
                            movement_type=MovementType.TRANSFER,
                            quantity=item["quantity"],
                            from_location=from_location,
                            to_location=to_location,
                            reference=reference,
                            notes=notes,
                            created_by=created_by,
                        )
                    else:
                        sid = transaction.savepoint()
                        try:
                            movement = self._stock_service.process_movement(
                                product=product,
                                movement_type=MovementType.TRANSFER,
                                quantity=item["quantity"],
                                from_location=from_location,
                                to_location=to_location,
                                reference=reference,
                                notes=notes,
                                created_by=created_by,
                            )
                            transaction.savepoint_commit(sid)
                        except Exception as e:
                            transaction.savepoint_rollback(sid)
                            raise e

                    result.success_count += 1
                    result.results.append({
                        "index": idx,
                        "product_id": product_id,
                        "status": "success",
                        "movement_id": movement.pk,
                    })

                except Product.DoesNotExist:
                    result.failure_count += 1
                    error = {
                        "index": idx,
                        "product_id": product_id,
                        "error": f"Product {product_id} not found.",
                    }
                    result.errors.append(error)
                    if fail_fast:
                        raise InventoryError(error["error"])

                except (InventoryError, Exception) as e:
                    result.failure_count += 1
                    error = {
                        "index": idx,
                        "product_id": product_id,
                        "error": str(e),
                    }
                    result.errors.append(error)
                    if fail_fast:
                        raise

        return result

    def bulk_adjustment(
        self,
        *,
        items: list[dict],
        location,
        created_by=None,
        notes: str = "",
        fail_fast: bool = False,
    ) -> BulkOperationResult:
        """Adjust stock for multiple products at a location.

        Each item dict requires ``product_id`` (int) and ``new_quantity`` (int).
        The service computes the delta between current and desired quantity,
        creating a positive (to_location) or negative (from_location) adjustment.
        """
        result = BulkOperationResult()

        with transaction.atomic():
            for idx, item in enumerate(items):
                product_id = item.get("product_id")
                try:
                    if product_id is None:
                        raise ValueError("Missing product_id.")

                    product = Product.objects.get(pk=product_id)
                    new_qty = item["new_quantity"]

                    record = StockRecord.objects.filter(
                        product=product, location=location,
                    ).first()
                    current_qty = record.quantity if record else 0
                    delta = new_qty - current_qty

                    if delta == 0:
                        result.success_count += 1
                        result.results.append({
                            "index": idx,
                            "product_id": product_id,
                            "status": "no_change",
                            "previous_quantity": current_qty,
                            "new_quantity": new_qty,
                        })
                        continue

                    if fail_fast:
                        movement = self._create_adjustment_movement(
                            product=product,
                            location=location,
                            delta=delta,
                            notes=notes,
                            created_by=created_by,
                        )
                    else:
                        sid = transaction.savepoint()
                        try:
                            movement = self._create_adjustment_movement(
                                product=product,
                                location=location,
                                delta=delta,
                                notes=notes,
                                created_by=created_by,
                            )
                            transaction.savepoint_commit(sid)
                        except Exception as e:
                            transaction.savepoint_rollback(sid)
                            raise e

                    result.success_count += 1
                    result.results.append({
                        "index": idx,
                        "product_id": product_id,
                        "status": "success",
                        "previous_quantity": current_qty,
                        "new_quantity": new_qty,
                        "movement_id": movement.pk,
                    })

                except Product.DoesNotExist:
                    result.failure_count += 1
                    error = {
                        "index": idx,
                        "product_id": product_id,
                        "error": f"Product {product_id} not found.",
                    }
                    result.errors.append(error)
                    if fail_fast:
                        raise InventoryError(error["error"])

                except (InventoryError, Exception) as e:
                    result.failure_count += 1
                    error = {
                        "index": idx,
                        "product_id": product_id,
                        "error": str(e),
                    }
                    result.errors.append(error)
                    if fail_fast:
                        raise

        return result

    def bulk_revalue(
        self,
        *,
        items: list[dict],
        fail_fast: bool = False,
    ) -> BulkOperationResult:
        """Update unit costs for multiple products.

        Each item dict requires ``product_id`` (int) and ``new_unit_cost`` (Decimal/str).
        """
        result = BulkOperationResult()

        with transaction.atomic():
            for idx, item in enumerate(items):
                product_id = item.get("product_id")
                try:
                    if product_id is None:
                        raise ValueError("Missing product_id.")

                    product = Product.objects.select_for_update().get(
                        pk=product_id,
                    )
                    old_cost = product.unit_cost
                    new_cost = Decimal(str(item["new_unit_cost"]))

                    if new_cost < 0:
                        raise ValueError(
                            f"Unit cost cannot be negative: {new_cost}"
                        )

                    if fail_fast:
                        product.unit_cost = new_cost
                        product.save(update_fields=["unit_cost", "updated_at"])
                    else:
                        sid = transaction.savepoint()
                        try:
                            product.unit_cost = new_cost
                            product.save(update_fields=["unit_cost", "updated_at"])
                            transaction.savepoint_commit(sid)
                        except Exception as e:
                            transaction.savepoint_rollback(sid)
                            raise e

                    result.success_count += 1
                    result.results.append({
                        "index": idx,
                        "product_id": product_id,
                        "status": "success",
                        "old_unit_cost": str(old_cost),
                        "new_unit_cost": str(new_cost),
                    })

                except Product.DoesNotExist:
                    result.failure_count += 1
                    error = {
                        "index": idx,
                        "product_id": product_id,
                        "error": f"Product {product_id} not found.",
                    }
                    result.errors.append(error)
                    if fail_fast:
                        raise InventoryError(error["error"])

                except (InventoryError, Exception) as e:
                    result.failure_count += 1
                    error = {
                        "index": idx,
                        "product_id": product_id,
                        "error": str(e),
                    }
                    result.errors.append(error)
                    if fail_fast:
                        raise

        return result

    def _create_adjustment_movement(
        self, *, product, location, delta, notes, created_by,
    ):
        """Create an adjustment movement for the given delta."""
        if delta > 0:
            return self._stock_service.process_movement(
                product=product,
                movement_type=MovementType.ADJUSTMENT,
                quantity=delta,
                to_location=location,
                notes=notes,
                created_by=created_by,
            )
        else:
            return self._stock_service.process_movement(
                product=product,
                movement_type=MovementType.ADJUSTMENT,
                quantity=abs(delta),
                from_location=location,
                notes=notes,
                created_by=created_by,
            )
