"""Cycle counting service.

Owns the transactional business logic for managing physical inventory
count cycles — from scheduling through counting, completion, and
reconciliation with corrective stock adjustments.

The project adopts **OOP as the standard paradigm** for service layers.
See :mod:`inventory.services.stock` for the same pattern.
"""

from __future__ import annotations

import logging
from typing import Any

from django.db import transaction
from django.utils import timezone

from inventory.models.audit import AuditAction
from inventory.models.cycle import (
    CycleCountLine,
    CycleStatus,
    InventoryCycle,
    InventoryVariance,
    VarianceResolution,
    VarianceType,
)
from inventory.models.stock import MovementType, StockRecord
from inventory.services.audit import AuditService
from inventory.services.stock import StockService

logger = logging.getLogger(__name__)

_VALID_TRANSITIONS: dict[str, str] = {
    CycleStatus.SCHEDULED: CycleStatus.IN_PROGRESS,
    CycleStatus.IN_PROGRESS: CycleStatus.COMPLETED,
    CycleStatus.COMPLETED: CycleStatus.RECONCILED,
}


class CycleCountService:
    """Manages the full lifecycle of physical inventory count cycles.

    Usage::

        service = CycleCountService()
        cycle = service.start_cycle(
            name="Q1 2026 Full Count",
            scheduled_date=date.today(),
            started_by=user,
        )
        service.record_count(
            cycle, product=widget, location=warehouse,
            counted_quantity=98, counted_by=user,
        )
        service.complete_cycle(cycle)
        variances = service.reconcile_cycle(
            cycle, resolved_by=user,
            resolutions={line_id: {"resolution": "accepted"}},
        )

    The class is **stateless** — instantiate per request or keep a
    module-level singleton.
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

    def start_cycle(
        self,
        *,
        name: str,
        location=None,
        scheduled_date,
        started_by,
    ) -> InventoryCycle:
        """Create a cycle and pre-populate CycleCountLines with system quantities.

        Snapshots the current ``StockRecord.quantity`` for every
        product at the target location (or all locations when
        ``location`` is ``None``).

        Parameters
        ----------
        name : str
            Descriptive name for the cycle (e.g. "Q1 2026 Full Count").
        location : StockLocation | None
            Scope to a specific location.  ``None`` counts all locations.
        scheduled_date : date
            The planned date for the count.
        started_by : User
            The user initiating the cycle.

        Returns
        -------
        InventoryCycle
            The persisted cycle in ``IN_PROGRESS`` status.
        """
        with transaction.atomic():
            cycle = InventoryCycle.objects.create(
                name=name,
                location=location,
                scheduled_date=scheduled_date,
                status=CycleStatus.IN_PROGRESS,
                started_by=started_by,
                started_at=timezone.now(),
            )

            stock_qs = StockRecord.objects.select_related("product", "location")
            if location is not None:
                stock_qs = stock_qs.filter(location=location)
            stock_qs = stock_qs.filter(quantity__gt=0)

            lines = [
                CycleCountLine(
                    cycle=cycle,
                    product=record.product,
                    location=record.location,
                    system_quantity=record.quantity,
                )
                for record in stock_qs
            ]
            CycleCountLine.objects.bulk_create(lines)

            self._log_audit(
                cycle,
                AuditAction.CYCLE_COUNT_STARTED,
                user=started_by,
                line_count=len(lines),
            )

        return cycle

    def record_count(
        self,
        cycle: InventoryCycle,
        *,
        product,
        location,
        counted_quantity: int,
        counted_by,
        notes: str = "",
    ) -> CycleCountLine:
        """Record a physical count for one product at one location.

        Parameters
        ----------
        cycle : InventoryCycle
            Must be in ``IN_PROGRESS`` status.
        product : Product
            The product being counted.
        location : StockLocation
            Where the count took place.
        counted_quantity : int
            The physical count observed.
        counted_by : User
            The user performing the count.
        notes : str
            Optional free-text notes.

        Returns
        -------
        CycleCountLine
            The updated count line.

        Raises
        ------
        ValueError
            If the cycle is not in ``IN_PROGRESS`` status or the line
            does not exist.
        """
        if cycle.status != CycleStatus.IN_PROGRESS:
            raise ValueError(
                f"Cannot record counts on a cycle with status "
                f"'{cycle.get_status_display()}'. "
                f"Cycle must be IN_PROGRESS."
            )

        try:
            line = CycleCountLine.objects.get(
                cycle=cycle,
                product=product,
                location=location,
            )
        except CycleCountLine.DoesNotExist:
            raise ValueError(
                f"No count line for {product} at {location} in cycle "
                f"'{cycle.name}'."
            )

        line.counted_quantity = counted_quantity
        line.counted_by = counted_by
        line.counted_at = timezone.now()
        line.notes = notes
        line.save(update_fields=[
            "counted_quantity", "counted_by", "counted_at", "notes", "updated_at",
        ])

        return line

    def complete_cycle(self, cycle: InventoryCycle) -> None:
        """Mark cycle as COMPLETED. No more counts accepted afterward.

        Parameters
        ----------
        cycle : InventoryCycle
            Must be in ``IN_PROGRESS`` status.

        Raises
        ------
        ValueError
            If the cycle is not in ``IN_PROGRESS`` status.
        """
        if cycle.status != CycleStatus.IN_PROGRESS:
            raise ValueError(
                f"Cannot complete a cycle with status "
                f"'{cycle.get_status_display()}'. "
                f"Cycle must be IN_PROGRESS."
            )

        cycle.status = CycleStatus.COMPLETED
        cycle.completed_at = timezone.now()
        cycle.save(update_fields=["status", "completed_at", "updated_at"])

    def reconcile_cycle(
        self,
        cycle: InventoryCycle,
        *,
        resolved_by,
        resolutions: dict[int, dict[str, Any]],
    ) -> list[InventoryVariance]:
        """Process all variances and create adjustment movements where accepted.

        Parameters
        ----------
        cycle : InventoryCycle
            Must be in ``COMPLETED`` status.
        resolved_by : User
            The user approving/investigating the variances.
        resolutions : dict[int, dict[str, Any]]
            Keyed by ``CycleCountLine.pk``.  Each value is a dict with:

            - ``"resolution"`` — one of ``VarianceResolution`` values
              (``"accepted"``, ``"investigating"``, ``"rejected"``).
            - ``"root_cause"`` — optional free-text explanation.

            Lines with zero variance (matches) are auto-resolved as
            ``ACCEPTED`` if not explicitly included.

        Returns
        -------
        list[InventoryVariance]
            All variance records created during reconciliation.

        Raises
        ------
        ValueError
            If the cycle is not COMPLETED, or a non-zero-variance
            counted line has no resolution entry.
        """
        if cycle.status != CycleStatus.COMPLETED:
            raise ValueError(
                f"Cannot reconcile a cycle with status "
                f"'{cycle.get_status_display()}'. "
                f"Cycle must be COMPLETED."
            )

        counted_lines = cycle.lines.filter(
            counted_quantity__isnull=False,
        ).select_related("product", "location")

        now = timezone.now()
        variances: list[InventoryVariance] = []

        with transaction.atomic():
            for line in counted_lines:
                var_qty = line.variance
                var_type = self._classify_variance(var_qty)
                resolution_data = resolutions.get(line.pk, {})

                if var_type == VarianceType.MATCH:
                    resolution = resolution_data.get(
                        "resolution", VarianceResolution.ACCEPTED,
                    )
                    root_cause = resolution_data.get("root_cause", "")
                else:
                    if line.pk not in resolutions:
                        raise ValueError(
                            f"No resolution provided for variance on "
                            f"count line {line.pk} ({line.product} @ "
                            f"{line.location}, variance={var_qty:+d})."
                        )
                    resolution = resolution_data["resolution"]
                    root_cause = resolution_data.get("root_cause", "")

                adjustment_movement = None
                if resolution == VarianceResolution.ACCEPTED and var_qty != 0:
                    adjustment_movement = self._create_adjustment(
                        line=line,
                        variance_quantity=var_qty,
                        created_by=resolved_by,
                        cycle=cycle,
                    )

                variance = InventoryVariance.objects.create(
                    cycle=cycle,
                    count_line=line,
                    product=line.product,
                    location=line.location,
                    variance_type=var_type,
                    system_quantity=line.system_quantity,
                    physical_quantity=line.counted_quantity,
                    variance_quantity=var_qty,
                    resolution=resolution,
                    adjustment_movement=adjustment_movement,
                    resolved_by=resolved_by,
                    resolved_at=now,
                    root_cause=root_cause,
                )
                variances.append(variance)

            cycle.status = CycleStatus.RECONCILED
            cycle.save(update_fields=["status", "updated_at"])

            self._log_audit(
                cycle,
                AuditAction.CYCLE_COUNT_RECONCILED,
                user=resolved_by,
                variance_count=len(variances),
                accepted=sum(
                    1 for v in variances
                    if v.resolution == VarianceResolution.ACCEPTED
                ),
                investigating=sum(
                    1 for v in variances
                    if v.resolution == VarianceResolution.INVESTIGATING
                ),
            )

        return variances

    def get_variance_summary(self, cycle: InventoryCycle) -> dict:
        """Return counts of shortages, surpluses, and matches.

        Works on both COMPLETED cycles (from count line data) and
        RECONCILED cycles (from persisted variance records).

        Returns
        -------
        dict
            Keys: ``"shortages"``, ``"surpluses"``, ``"matches"``,
            ``"uncounted"``, ``"total_lines"``.
        """
        lines = cycle.lines.all()
        total = lines.count()

        shortages = 0
        surpluses = 0
        matches = 0
        uncounted = 0

        for line in lines:
            if line.counted_quantity is None:
                uncounted += 1
            elif line.variance < 0:
                shortages += 1
            elif line.variance > 0:
                surpluses += 1
            else:
                matches += 1

        return {
            "shortages": shortages,
            "surpluses": surpluses,
            "matches": matches,
            "uncounted": uncounted,
            "total_lines": total,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _classify_variance(variance_quantity: int) -> str:
        if variance_quantity < 0:
            return VarianceType.SHORTAGE
        elif variance_quantity > 0:
            return VarianceType.SURPLUS
        return VarianceType.MATCH

    def _create_adjustment(
        self,
        *,
        line: CycleCountLine,
        variance_quantity: int,
        created_by,
        cycle: InventoryCycle,
    ):
        """Create a corrective StockMovement for an accepted variance.

        Positive variance (surplus) → receive-style adjustment (to_location).
        Negative variance (shortage) → issue-style adjustment (from_location).
        """
        if variance_quantity > 0:
            return self._stock_service.process_movement(
                product=line.product,
                movement_type=MovementType.ADJUSTMENT,
                quantity=abs(variance_quantity),
                to_location=line.location,
                reference=f"Cycle count: {cycle.name}",
                notes=f"Surplus adjustment from cycle count line #{line.pk}",
                created_by=created_by,
            )
        else:
            return self._stock_service.process_movement(
                product=line.product,
                movement_type=MovementType.ADJUSTMENT,
                quantity=abs(variance_quantity),
                from_location=line.location,
                reference=f"Cycle count: {cycle.name}",
                notes=f"Shortage adjustment from cycle count line #{line.pk}",
                created_by=created_by,
            )

    def _log_audit(
        self,
        cycle: InventoryCycle,
        action: str,
        *,
        user=None,
        **details: Any,
    ) -> None:
        """Record a compliance audit entry for a cycle event.

        Skipped when the cycle has no tenant (e.g. in tests without
        multi-tenancy setup).
        """
        tenant = getattr(cycle, "tenant", None)
        if tenant is None:
            return

        details["cycle_id"] = cycle.pk
        details["cycle_name"] = cycle.name
        if cycle.location:
            details["location"] = cycle.location.name

        self._audit_service.log(
            tenant=tenant,
            action=action,
            user=user,
            **details,
        )
