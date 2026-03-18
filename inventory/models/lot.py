from datetime import date

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import UniqueConstraint

from .base import TimeStampedModel


class StockLot(TimeStampedModel):
    """Batch/lot tracking for products.

    Tracks lot numbers, serial numbers, expiry dates, and remaining
    quantities to enable FIFO/LIFO allocation and traceability.
    """

    product = models.ForeignKey(
        "inventory.Product",
        on_delete=models.CASCADE,
        related_name="lots",
    )
    lot_number = models.CharField(max_length=100, db_index=True)
    serial_number = models.CharField(max_length=100, blank=True)
    manufacturing_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    quantity_received = models.PositiveIntegerField()
    quantity_remaining = models.PositiveIntegerField()
    supplier = models.ForeignKey(
        "procurement.Supplier",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="stock_lots",
    )
    purchase_order = models.ForeignKey(
        "procurement.PurchaseOrder",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="stock_lots",
    )
    received_date = models.DateField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["received_date", "pk"]
        constraints = [
            UniqueConstraint(
                fields=["tenant", "product", "lot_number"],
                name="unique_lot_per_product_per_tenant",
            ),
        ]

    def clean(self):
        super().clean()
        errors = {}
        if self.quantity_remaining is not None and self.quantity_received is not None:
            if self.quantity_remaining > self.quantity_received:
                errors["quantity_remaining"] = (
                    "Remaining quantity cannot exceed received quantity."
                )
        if self.manufacturing_date and self.expiry_date:
            if self.expiry_date <= self.manufacturing_date:
                errors["expiry_date"] = (
                    "Expiry date must be after manufacturing date."
                )
        if errors:
            raise ValidationError(errors)

    def is_expired(self):
        """Return True if the lot has passed its expiry date."""
        if self.expiry_date is None:
            return False
        return date.today() > self.expiry_date

    def days_to_expiry(self):
        """Return days until expiry, or None if no expiry date is set.

        Returns a negative number for lots that have already expired.
        """
        if self.expiry_date is None:
            return None
        return (self.expiry_date - date.today()).days

    def __str__(self):
        return f"{self.product.sku} — Lot {self.lot_number}"


class StockMovementLot(models.Model):
    """Junction table linking a StockMovement to the lots it consumed.

    A single movement may draw quantities from multiple lots (e.g.,
    issuing 150 units when Lot A has 100 and Lot B has 50).
    """

    stock_movement = models.ForeignKey(
        "inventory.StockMovement",
        on_delete=models.CASCADE,
        related_name="lot_allocations",
    )
    stock_lot = models.ForeignKey(
        "inventory.StockLot",
        on_delete=models.PROTECT,
        related_name="movement_allocations",
    )
    quantity = models.PositiveIntegerField()

    class Meta:
        unique_together = ("stock_movement", "stock_lot")

    def __str__(self):
        return (
            f"Movement #{self.stock_movement_id} "
            f"← Lot {self.stock_lot.lot_number} x{self.quantity}"
        )
