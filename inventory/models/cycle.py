from django.conf import settings
from django.db import models

from .base import TimeStampedModel


class CycleStatus(models.TextChoices):
    SCHEDULED = "scheduled", "Scheduled"
    IN_PROGRESS = "in_progress", "In Progress"
    COMPLETED = "completed", "Completed"
    RECONCILED = "reconciled", "Reconciled"


class VarianceType(models.TextChoices):
    SHORTAGE = "shortage", "Shortage"
    SURPLUS = "surplus", "Surplus"
    MATCH = "match", "Match"


class VarianceResolution(models.TextChoices):
    ACCEPTED = "accepted", "Accepted (Adjustment Created)"
    INVESTIGATING = "investigating", "Under Investigation"
    REJECTED = "rejected", "Rejected (No Change)"


class InventoryCycle(TimeStampedModel):
    """Physical inventory count cycle for verification against system records.

    Supports full-warehouse or location-scoped counts.  Status workflow:

        SCHEDULED → IN_PROGRESS → COMPLETED → RECONCILED
    """

    name = models.CharField(
        max_length=255,
        help_text="Descriptive name for this cycle count (e.g., 'Q1 2026 Full Count').",
    )
    location = models.ForeignKey(
        "inventory.StockLocation",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="inventory_cycles",
        help_text="Scope to a specific location. Leave blank for a full warehouse count.",
    )
    status = models.CharField(
        max_length=20,
        choices=CycleStatus.choices,
        default=CycleStatus.SCHEDULED,
    )
    scheduled_date = models.DateField(
        help_text="Date when the cycle count is planned to take place.",
    )
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when counting actually began.",
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when counting was finished.",
    )
    started_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="cycles_started",
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-scheduled_date"]

    def __str__(self):
        return f"{self.name} [{self.get_status_display()}]"


# ---------------------------------------------------------------------------
# CycleCountLine
# ---------------------------------------------------------------------------


class CycleCountLine(TimeStampedModel):
    """Individual line recording a physical count for one product at one location.

    The ``system_quantity`` is a snapshot captured when the line is created,
    allowing variance analysis even if stock changes after counting.
    """

    cycle = models.ForeignKey(
        "inventory.InventoryCycle",
        on_delete=models.CASCADE,
        related_name="lines",
    )
    product = models.ForeignKey(
        "inventory.Product",
        on_delete=models.PROTECT,
        related_name="cycle_count_lines",
    )
    location = models.ForeignKey(
        "inventory.StockLocation",
        on_delete=models.PROTECT,
    )
    system_quantity = models.IntegerField(
        help_text="System stock at time of count.",
    )
    counted_quantity = models.IntegerField(
        null=True,
        blank=True,
        help_text="Physical count entered by warehouse staff.",
    )
    counted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="counts_performed",
    )
    counted_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ("cycle", "product", "location")

    @property
    def variance(self):
        """Difference between physical count and system record.

        Returns ``None`` if the line has not been counted yet.
        """
        if self.counted_quantity is None:
            return None
        return self.counted_quantity - self.system_quantity

    def __str__(self):
        status = f"counted={self.counted_quantity}" if self.counted_quantity is not None else "pending"
        return f"{self.product} @ {self.location} ({status})"


# ---------------------------------------------------------------------------
# InventoryVariance
# ---------------------------------------------------------------------------


class InventoryVariance(TimeStampedModel):
    """Records the outcome of comparing a physical count against the system record.

    Created during cycle reconciliation.  Each variance links back to
    its :class:`CycleCountLine` (one-to-one) and optionally to the
    corrective :class:`~inventory.models.stock.StockMovement` created
    when the variance is accepted.
    """

    cycle = models.ForeignKey(
        "inventory.InventoryCycle",
        on_delete=models.CASCADE,
        related_name="variances",
    )
    count_line = models.OneToOneField(
        "inventory.CycleCountLine",
        on_delete=models.CASCADE,
        related_name="variance_record",
    )
    product = models.ForeignKey(
        "inventory.Product",
        on_delete=models.PROTECT,
    )
    location = models.ForeignKey(
        "inventory.StockLocation",
        on_delete=models.PROTECT,
    )
    variance_type = models.CharField(
        max_length=20,
        choices=VarianceType.choices,
    )
    system_quantity = models.IntegerField()
    physical_quantity = models.IntegerField()
    variance_quantity = models.IntegerField(
        help_text="physical_quantity − system_quantity (negative = shortage).",
    )
    resolution = models.CharField(
        max_length=20,
        choices=VarianceResolution.choices,
        null=True,
        blank=True,
    )
    adjustment_movement = models.ForeignKey(
        "inventory.StockMovement",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="cycle_variances",
        help_text="Corrective stock movement created when resolution is 'accepted'.",
    )
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="variances_resolved",
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    root_cause = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    @staticmethod
    def detect_variance_type(system_qty: int, physical_qty: int) -> str:
        """Return the appropriate ``VarianceType`` value."""
        if physical_qty < system_qty:
            return VarianceType.SHORTAGE
        if physical_qty > system_qty:
            return VarianceType.SURPLUS
        return VarianceType.MATCH

    def __str__(self):
        return (
            f"{self.product} @ {self.location}: "
            f"{self.get_variance_type_display()} ({self.variance_quantity:+d})"
        )
