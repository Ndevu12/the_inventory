from django.core.exceptions import ValidationError
from django.db import models
from treebeard.mp_tree import MP_Node
from wagtail.admin.panels import FieldPanel
from wagtail.search import index
from wagtail.snippets.models import register_snippet

from .base import TimeStampedModel


@register_snippet
class StockLocation(TimeStampedModel, MP_Node):
    """Hierarchical physical location using treebeard materialised path.

    Examples: Main Warehouse → Aisle A → Shelf 3 → Bin 12.
    """

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    # treebeard: alphabetical ordering within each tree level
    node_order_by = ["name"]

    panels = [
        FieldPanel("name"),
        FieldPanel("description"),
        FieldPanel("is_active"),
    ]

    search_fields = [
        index.SearchField("name"),
        index.FilterField("is_active"),
    ]

    def __str__(self):
        return self.name


# ---------------------------------------------------------------------------
# StockRecord
# ---------------------------------------------------------------------------


class StockRecord(TimeStampedModel):
    """Live stock quantity for a product at a specific location.

    Updated automatically by stock movement processing logic.
    """

    product = models.ForeignKey(
        "inventory.Product",
        on_delete=models.CASCADE,
        related_name="stock_records",
    )
    location = models.ForeignKey(
        "inventory.StockLocation",
        on_delete=models.CASCADE,
        related_name="stock_records",
    )
    quantity = models.IntegerField(default=0)

    class Meta:
        unique_together = ("product", "location")

    @property
    def is_low_stock(self):
        """Return True when quantity is at or below the product's reorder point."""
        return self.quantity <= self.product.reorder_point

    def __str__(self):
        return f"{self.product.sku} @ {self.location.name}: {self.quantity}"


# ---------------------------------------------------------------------------
# StockMovement
# ---------------------------------------------------------------------------


class MovementType(models.TextChoices):
    RECEIVE = "receive", "Receive"
    ISSUE = "issue", "Issue"
    TRANSFER = "transfer", "Transfer"
    ADJUSTMENT = "adjustment", "Adjustment"


class StockMovement(TimeStampedModel):
    """Immutable audit log of every stock change.

    Once created, movements should not be edited or deleted — only new
    corrective movements (adjustments) should be added.
    """

    product = models.ForeignKey(
        "inventory.Product",
        on_delete=models.PROTECT,
        related_name="stock_movements",
    )
    from_location = models.ForeignKey(
        "inventory.StockLocation",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="movements_out",
    )
    to_location = models.ForeignKey(
        "inventory.StockLocation",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="movements_in",
    )
    quantity = models.PositiveIntegerField()
    unit_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Cost per unit at the time of this movement.",
    )
    movement_type = models.CharField(
        max_length=20,
        choices=MovementType.choices,
    )
    reference = models.CharField(
        max_length=255,
        blank=True,
        help_text="Optional reference (e.g. PO number, SO number).",
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def clean(self):
        """Validate location requirements per movement type."""
        super().clean()
        mt = self.movement_type
        errors = {}

        if mt == MovementType.RECEIVE:
            if not self.to_location:
                errors["to_location"] = "Receive movements require a destination location."
            if self.from_location:
                errors["from_location"] = "Receive movements must not have a source location."

        elif mt == MovementType.ISSUE:
            if not self.from_location:
                errors["from_location"] = "Issue movements require a source location."
            if self.to_location:
                errors["to_location"] = "Issue movements must not have a destination location."

        elif mt == MovementType.TRANSFER:
            if not self.from_location:
                errors["from_location"] = "Transfer movements require a source location."
            if not self.to_location:
                errors["to_location"] = "Transfer movements require a destination location."
            if (
                self.from_location
                and self.to_location
                and self.from_location == self.to_location
            ):
                errors["to_location"] = "Source and destination must be different for transfers."

        elif mt == MovementType.ADJUSTMENT:
            if not self.from_location and not self.to_location:
                errors["from_location"] = "Adjustment movements require at least one location."

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.movement_type} — {self.product.sku} x{self.quantity}"
