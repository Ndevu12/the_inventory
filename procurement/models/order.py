from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import UniqueConstraint
from wagtail.search import index

from inventory.models.base import TimeStampedModel


class PurchaseOrderStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    CONFIRMED = "confirmed", "Confirmed"
    RECEIVED = "received", "Received"
    CANCELLED = "cancelled", "Cancelled"


class PurchaseOrder(TimeStampedModel):
    """An order placed with a supplier to procure goods.

    Follows a status workflow: draft -> confirmed -> received.
    Orders can be cancelled from draft or confirmed state.
    """

    order_number = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Unique purchase order number per tenant (e.g., PO-2026-001).",
    )
    supplier = models.ForeignKey(
        "procurement.Supplier",
        on_delete=models.PROTECT,
        related_name="purchase_orders",
        help_text="The supplier this order is placed with.",
    )
    status = models.CharField(
        max_length=20,
        choices=PurchaseOrderStatus.choices,
        default=PurchaseOrderStatus.DRAFT,
    )
    order_date = models.DateField(
        help_text="The date this order was placed.",
    )
    expected_delivery_date = models.DateField(
        null=True,
        blank=True,
        help_text="Expected date of goods arrival.",
    )
    notes = models.TextField(
        blank=True,
        help_text="Internal notes about this purchase order.",
    )

    search_fields = [
        index.SearchField("order_number"),
        index.FilterField("status"),
        index.FilterField("supplier"),
    ]

    class Meta:
        ordering = ["-order_date", "-created_at"]
        constraints = [
            UniqueConstraint(
                fields=["tenant", "order_number"],
                name="unique_po_number_per_tenant",
            ),
        ]

    def clean(self):
        super().clean()
        if (
            self.expected_delivery_date
            and self.order_date
            and self.expected_delivery_date < self.order_date
        ):
            raise ValidationError({
                "expected_delivery_date": "Expected delivery date cannot be before order date.",
            })

    @property
    def total_cost(self):
        """Sum of (quantity * unit_cost) across all lines."""
        return sum(line.line_total for line in self.lines.all())

    def __str__(self):
        return f"{self.order_number} — {self.supplier.name}"


class PurchaseOrderLine(TimeStampedModel):
    """A single line item on a purchase order.

    Tenant is inherited from ``TimeStampedModel`` (``tenant`` FK to ``tenants.Tenant``,
    ``on_delete=CASCADE``). It must match the parent ``PurchaseOrder``'s tenant; if
    omitted at creation, it is set from the purchase order on ``save()`` when the PO has a tenant.
    """

    purchase_order = models.ForeignKey(
        "procurement.PurchaseOrder",
        on_delete=models.CASCADE,
        related_name="lines",
    )
    product = models.ForeignKey(
        "inventory.Product",
        on_delete=models.PROTECT,
        related_name="purchase_order_lines",
    )
    quantity = models.PositiveIntegerField(
        help_text="Number of units to order.",
    )
    unit_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Cost per unit for this line.",
    )

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["tenant", "purchase_order", "product"],
                name="unique_purchaseorderline_tenant_po_product",
            ),
        ]

    def clean(self):
        super().clean()
        if self.purchase_order_id and self.tenant_id and self.purchase_order.tenant_id:
            if self.tenant_id != self.purchase_order.tenant_id:
                raise ValidationError({
                    "tenant": "Line tenant must match the purchase order's tenant.",
                })

    def save(self, *args, **kwargs):
        if self.purchase_order_id:
            po_tid = self.purchase_order.tenant_id
            if self.tenant_id is None and po_tid:
                self.tenant_id = po_tid
            elif (
                self.tenant_id
                and po_tid
                and self.tenant_id != po_tid
            ):
                raise ValidationError({
                    "tenant": "Line tenant must match the purchase order's tenant.",
                })
        super().save(*args, **kwargs)

    @property
    def line_total(self):
        """Total cost for this line (quantity * unit_cost)."""
        return self.quantity * self.unit_cost

    def __str__(self):
        return f"{self.product.sku} x{self.quantity} @ {self.unit_cost}"


class GoodsReceivedNote(TimeStampedModel):
    """Confirmation that goods from a purchase order have been received.

    Processing a GRN auto-creates 'receive' StockMovements for each line
    on the associated purchase order, updating stock at the specified location.
    """

    grn_number = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Unique GRN number per tenant (e.g., GRN-2026-001).",
    )
    purchase_order = models.ForeignKey(
        "procurement.PurchaseOrder",
        on_delete=models.PROTECT,
        related_name="goods_received_notes",
    )
    received_date = models.DateField(
        help_text="The date goods were received.",
    )
    location = models.ForeignKey(
        "inventory.StockLocation",
        on_delete=models.PROTECT,
        related_name="goods_received_notes",
        help_text="The location where goods were received into.",
    )
    notes = models.TextField(
        blank=True,
        help_text="Notes about the goods received (e.g., condition, discrepancies).",
    )
    is_processed = models.BooleanField(
        default=False,
        help_text="Whether stock movements have been created for this GRN.",
    )

    search_fields = [
        index.SearchField("grn_number"),
        index.FilterField("is_processed"),
    ]

    class Meta:
        ordering = ["-received_date", "-created_at"]
        constraints = [
            UniqueConstraint(
                fields=["tenant", "grn_number"],
                name="unique_grn_number_per_tenant",
            ),
        ]

    def __str__(self):
        return f"{self.grn_number} — {self.purchase_order.order_number}"
