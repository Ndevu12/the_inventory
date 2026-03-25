"""Mixin: emit compliance audit rows after tenant-scoped ModelViewSet writes."""

from __future__ import annotations

from typing import Any

from inventory.services.audit import AuditService


class AuditedTenantCRUDMixin:
    """Log audits after create/update/destroy.

    Place **before** :class:`TenantScopedInventoryMixin` in the MRO so
    ``super().perform_create`` etc. run the tenant-aware saves.

    Subclasses may set any action to ``None`` to skip that verb. Override
    :meth:`_audit_log_payload` to set ``product`` FK and ``details`` fields.
    """

    audit_action_create: str | None = None
    audit_action_update: str | None = None
    audit_action_delete: str | None = None

    def perform_create(self, serializer):
        super().perform_create(serializer)
        if self.audit_action_create:
            self._emit_audit_log(self.audit_action_create, serializer.instance)

    def perform_update(self, serializer):
        super().perform_update(serializer)
        if self.audit_action_update:
            self._emit_audit_log(self.audit_action_update, serializer.instance)

    def perform_destroy(self, instance):
        if self.audit_action_delete:
            self._emit_audit_log(self.audit_action_delete, instance)
        super().perform_destroy(instance)

    def _emit_audit_log(self, action: str, instance):
        tenant = self._get_current_tenant()
        user = self.request.user if self.request.user.is_authenticated else None
        product, details = self._audit_log_payload(instance)
        AuditService().log(
            tenant=tenant,
            action=action,
            user=user,
            product=product,
            ip_address=AuditService._get_client_ip(self.request),
            **details,
        )

    def _audit_log_payload(self, instance) -> tuple[Any, dict[str, Any]]:
        """Return ``(product_fk_or_none, keyword args merged into ``details``)."""
        return None, {
            "object_type": instance._meta.model_name,
            "object_id": instance.pk,
        }
