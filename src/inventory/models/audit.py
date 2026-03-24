from django.conf import settings
from django.db import models


class AuditAction(models.TextChoices):
    STOCK_RECEIVED = "stock_received", "Stock Received"
    STOCK_ISSUED = "stock_issued", "Stock Issued"
    STOCK_TRANSFERRED = "stock_transferred", "Stock Transferred"
    STOCK_ADJUSTED = "stock_adjusted", "Stock Adjusted"
    RESERVATION_CREATED = "reservation_created", "Reservation Created"
    RESERVATION_FULFILLED = "reservation_fulfilled", "Reservation Fulfilled"
    RESERVATION_CANCELLED = "reservation_cancelled", "Reservation Cancelled"
    CYCLE_COUNT_STARTED = "cycle_count_started", "Cycle Count Started"
    CYCLE_COUNT_RECONCILED = "cycle_count_reconciled", "Cycle Count Reconciled"
    BULK_OPERATION = "bulk_operation", "Bulk Operation"
    TENANT_ACCESSED = "tenant_accessed", "Tenant Accessed"
    TENANT_DEACTIVATED = "tenant_deactivated", "Tenant Deactivated"
    TENANT_REACTIVATED = "tenant_reactivated", "Tenant Reactivated"
    TENANT_LIMIT_OVERRIDDEN = "tenant_limit_overridden", "Tenant Limit Overridden"
    IMPERSONATION_STARTED = "impersonation_started", "Impersonation Started"
    IMPERSONATION_ENDED = "impersonation_ended", "Impersonation Ended"
    TENANT_EXPORT = "tenant_export", "Tenant Data Exported"


class ComplianceAuditLog(models.Model):
    """Immutable compliance audit trail for regulatory and operational tracking.

    Records user actions across the system — stock operations, reservations,
    cycle counts, bulk operations, and tenant access events.  Unlike
    ``StockMovement`` (which tracks inventory deltas), this model captures
    *who* did *what* and *when*, with optional context in ``details``.
    """

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="audit_logs",
    )
    action = models.CharField(
        max_length=30,
        choices=AuditAction.choices,
    )
    product = models.ForeignKey(
        "inventory.Product",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
        help_text="Associated product, if applicable to this action.",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="audit_logs",
    )
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    details = models.JSONField(
        default=dict,
        blank=True,
        help_text="Context-specific data: lot numbers, quantities, location names, etc.",
    )

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["tenant", "action", "timestamp"]),
            models.Index(fields=["tenant", "timestamp"]),
        ]

    def __str__(self):
        return f"[{self.get_action_display()}] tenant={self.tenant_id} user={self.user_id} @ {self.timestamp}"
