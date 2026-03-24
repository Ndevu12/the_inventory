from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from .base import TimeStampedModel


class AllocationStrategy(models.TextChoices):
    FIFO = "FIFO", _("FIFO")
    LIFO = "LIFO", _("LIFO")


class ReservationStatus(models.TextChoices):
    PENDING = "pending", _("Pending")
    CONFIRMED = "confirmed", _("Confirmed")
    FULFILLED = "fulfilled", _("Fulfilled")
    CANCELLED = "cancelled", _("Cancelled")
    EXPIRED = "expired", _("Expired")


class ReservationRule(TimeStampedModel):
    """Tenant-level reservation policy.

    Rules define how reservations behave for a given scope.  The resolution
    order is: product-specific > category-specific > tenant-wide (both
    ``product`` and ``category`` are NULL).
    """

    name = models.CharField(max_length=255)
    category = models.ForeignKey(
        "inventory.Category",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reservation_rules",
    )
    product = models.ForeignKey(
        "inventory.Product",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reservation_rules",
    )
    auto_reserve_on_order = models.BooleanField(default=False)
    reservation_expiry_hours = models.PositiveIntegerField(default=72)
    allocation_strategy = models.CharField(
        max_length=10,
        choices=AllocationStrategy.choices,
        default=AllocationStrategy.FIFO,
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        scope = "tenant-wide"
        if self.product_id:
            scope = f"product={self.product}"
        elif self.category_id:
            scope = f"category={self.category}"
        return f"ReservationRule '{self.name}' ({scope})"

    @classmethod
    def get_rule_for_product(cls, product, tenant=None):
        """Return the most specific active rule for *product*.

        Precedence: product-level > category-level > tenant-wide.
        Returns ``None`` when no matching rule exists.
        """
        qs = cls.objects.filter(is_active=True)
        if tenant is not None:
            qs = qs.filter(tenant=tenant)

        product_rule = qs.filter(product=product).first()
        if product_rule:
            return product_rule

        if product.category_id:
            category_rule = qs.filter(
                product__isnull=True, category=product.category,
            ).first()
            if category_rule:
                return category_rule

        tenant_wide = qs.filter(
            product__isnull=True, category__isnull=True,
        ).first()
        return tenant_wide


class StockReservation(TimeStampedModel):
    """Stock reserved against a product+location for a sales order or manual hold.

    Prevents over-selling by earmarking inventory that is no longer
    available for other orders.  The reservation lifecycle is:

        PENDING  →  CONFIRMED  →  FULFILLED
                                →  CANCELLED
                                →  EXPIRED

    ``expires_at`` enables automatic expiry via a background task (T-12).
    """

    product = models.ForeignKey(
        "inventory.Product",
        on_delete=models.CASCADE,
        related_name="reservations",
    )
    location = models.ForeignKey(
        "inventory.StockLocation",
        on_delete=models.CASCADE,
        related_name="reservations",
    )
    stock_lot = models.ForeignKey(
        "inventory.StockLot",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reservations",
        help_text="Optional: reserve against a specific lot for lot-aware fulfillment.",
    )
    quantity = models.PositiveIntegerField()
    sales_order = models.ForeignKey(
        "sales.SalesOrder",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reservations",
    )
    reserved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="stock_reservations",
    )
    status = models.CharField(
        max_length=20,
        choices=ReservationStatus.choices,
        default=ReservationStatus.PENDING,
    )
    expires_at = models.DateTimeField(null=True, blank=True)
    fulfilled_movement = models.ForeignKey(
        "inventory.StockMovement",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="fulfilled_reservations",
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"Reservation {self.pk} — "
            f"{self.product.sku} x{self.quantity} "
            f"[{self.get_status_display()}]"
        )
