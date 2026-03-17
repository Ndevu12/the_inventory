from django.db import models
from django.db.models import UniqueConstraint
from wagtail.search import index

from inventory.models.base import TimeStampedModel


class SalesOrderStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    CONFIRMED = "confirmed", "Confirmed"
    FULFILLED = "fulfilled", "Fulfilled"
    CANCELLED = "cancelled", "Cancelled"


class SalesOrder(TimeStampedModel):
    """An order from a customer to purchase goods.

    Follows a status workflow: draft -> confirmed -> fulfilled.
    Orders can be cancelled from draft or confirmed state.
    """

    order_number = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Unique sales order number per tenant (e.g., SO-2026-001).",
    )
    customer = models.ForeignKey(
        "sales.Customer",
        on_delete=models.PROTECT,
        related_name="sales_orders",
        help_text="The customer this order belongs to.",
    )
    status = models.CharField(
        max_length=20,
        choices=SalesOrderStatus.choices,
        default=SalesOrderStatus.DRAFT,
    )
    order_date = models.DateField(
        help_text="The date this order was placed.",
    )
    notes = models.TextField(
        blank=True,
        help_text="Internal notes about this sales order.",
    )

    search_fields = [
        index.SearchField("order_number"),
        index.FilterField("status"),
        index.FilterField("customer"),
    ]

    class Meta:
        ordering = ["-order_date", "-created_at"]
        constraints = [
            UniqueConstraint(
                fields=["tenant", "order_number"],
                name="unique_so_number_per_tenant",
            ),
        ]

    @property
    def total_price(self):
        """Sum of (quantity * unit_price) across all lines."""
        return sum(line.line_total for line in self.lines.all())

    def __str__(self):
        return f"{self.order_number} — {self.customer.name}"


class SalesOrderLine(TimeStampedModel):
    """A single line item on a sales order."""

    sales_order = models.ForeignKey(
        "sales.SalesOrder",
        on_delete=models.CASCADE,
        related_name="lines",
    )
    product = models.ForeignKey(
        "inventory.Product",
        on_delete=models.PROTECT,
        related_name="sales_order_lines",
    )
    quantity = models.PositiveIntegerField(
        help_text="Number of units ordered.",
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Selling price per unit.",
    )

    class Meta:
        unique_together = ("sales_order", "product")

    @property
    def line_total(self):
        """Total price for this line (quantity * unit_price)."""
        return self.quantity * self.unit_price

    def __str__(self):
        return f"{self.product.sku} x{self.quantity} @ {self.unit_price}"


class Dispatch(TimeStampedModel):
    """A shipment of goods to fulfil a sales order.

    Processing a dispatch auto-creates 'issue' StockMovements for each
    line on the associated sales order, decrementing stock at the
    specified source location.
    """

    dispatch_number = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Unique dispatch number per tenant (e.g., DSP-2026-001).",
    )
    sales_order = models.ForeignKey(
        "sales.SalesOrder",
        on_delete=models.PROTECT,
        related_name="dispatches",
    )
    dispatch_date = models.DateField(
        help_text="The date goods were dispatched.",
    )
    from_location = models.ForeignKey(
        "inventory.StockLocation",
        on_delete=models.PROTECT,
        related_name="dispatches",
        help_text="The location goods are shipped from.",
    )
    notes = models.TextField(
        blank=True,
        help_text="Notes about this dispatch (e.g., tracking number, carrier).",
    )
    is_processed = models.BooleanField(
        default=False,
        help_text="Whether stock movements have been created for this dispatch.",
    )

    search_fields = [
        index.SearchField("dispatch_number"),
        index.FilterField("is_processed"),
    ]

    class Meta:
        ordering = ["-dispatch_date", "-created_at"]
        verbose_name_plural = "dispatches"
        constraints = [
            UniqueConstraint(
                fields=["tenant", "dispatch_number"],
                name="unique_dispatch_number_per_tenant",
            ),
        ]

    def __str__(self):
        return f"{self.dispatch_number} — {self.sales_order.order_number}"
