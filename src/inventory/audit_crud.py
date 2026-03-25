"""Tenant-scoped API audit logging helpers (CRUD / workflow)."""

from __future__ import annotations

from typing import Any

from inventory.services.audit import AuditService


def log_tenant_audit(
    request,
    tenant,
    action: str,
    *,
    product=None,
    **details: Any,
) -> None:
    """Append a :class:`~inventory.models.audit.ComplianceAuditLog` for an API mutation."""
    user = request.user if getattr(request.user, "is_authenticated", False) else None
    AuditService().log(
        tenant=tenant,
        action=action,
        user=user,
        product=product,
        ip_address=AuditService._get_client_ip(request),
        **details,
    )
