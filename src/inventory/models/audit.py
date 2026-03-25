from django.conf import settings
from django.db import models

from .audit_action import AuditAction

__all__ = ["AuditAction", "ComplianceAuditLog"]


class ComplianceAuditLog(models.Model):
    """Immutable compliance audit trail for regulatory and operational tracking.

    Records user actions across the system — stock operations, master data CRUD
    (products, locations, trading partners), sales/procurement workflow,
    reservations, cycle counts, bulk operations, and tenant access events.  Unlike
    ``StockMovement`` (which tracks inventory deltas), this model captures
    *who* did *what* and *when*, with optional context in ``details``.
    """

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="audit_logs",
    )
    action = models.CharField(
        max_length=40,
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

    @property
    def event_scope(self) -> str:
        """operational vs platform — matches API ``event_scope`` (see ``audit_display``)."""
        from inventory.audit_display import event_scope_for_action

        return event_scope_for_action(self.action)

    def __str__(self):
        return f"[{self.get_action_display()}] tenant={self.tenant_id} user={self.user_id} @ {self.timestamp}"
