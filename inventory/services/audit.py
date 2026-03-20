"""Compliance audit logging service.

Provides a centralized API for recording entries in
:class:`~inventory.models.audit.ComplianceAuditLog`.  All domain
services that need audit trails should go through :class:`AuditService`
rather than creating log records directly.

The project adopts **OOP as the standard paradigm** for service layers.
See :mod:`inventory.services.stock` for the same pattern.
"""

from __future__ import annotations

import logging
from typing import Any

from inventory.models.audit import ComplianceAuditLog

logger = logging.getLogger(__name__)


class AuditService:
    """Centralized compliance audit logging.

    Usage::

        audit = AuditService()
        audit.log(
            tenant=tenant,
            action="stock_received",
            user=user,
            product=product,
            quantity=100,
            to_location="Warehouse A",
        )

    The class is **stateless** — instantiate per request or keep a
    module-level singleton.
    """

    def log(
        self,
        *,
        tenant,
        action: str,
        user=None,
        product=None,
        ip_address: str | None = None,
        **details: Any,
    ) -> ComplianceAuditLog:
        """Create a ComplianceAuditLog entry.

        Parameters
        ----------
        tenant : tenants.models.Tenant
            The tenant this action belongs to.
        action : str
            One of :class:`~inventory.models.audit.AuditAction` values.
        user : User | None
            The user who performed the action.
        product : inventory.models.Product | None
            Associated product, if applicable.
        ip_address : str | None
            Client IP address, if available.
        **details
            Arbitrary key-value pairs stored in the JSON ``details`` field.

        Returns
        -------
        ComplianceAuditLog
            The persisted audit log entry.
        """
        entry = ComplianceAuditLog.objects.create(
            tenant=tenant,
            action=action,
            user=user,
            product=product,
            ip_address=ip_address,
            details=details,
        )
        logger.debug(
            "Audit log created: action=%s tenant=%s user=%s",
            action,
            getattr(tenant, "pk", None),
            getattr(user, "pk", None),
        )
        return entry

    def log_from_request(
        self,
        request,
        *,
        action: str,
        product=None,
        **details: Any,
    ) -> ComplianceAuditLog:
        """Convenience: extract tenant, user, IP from the request.

        Parameters
        ----------
        request : HttpRequest
            The current Django request.  Expected to have ``tenant``
            set by ``TenantMiddleware`` and ``user`` from auth middleware.
        action : str
            One of :class:`~inventory.models.audit.AuditAction` values.
        product : inventory.models.Product | None
            Associated product, if applicable.
        **details
            Additional context stored in the ``details`` JSON field.

        Returns
        -------
        ComplianceAuditLog
            The persisted audit log entry.
        """
        from tenants.middleware import get_effective_tenant

        tenant = getattr(request, "tenant", None) or get_effective_tenant(request)
        user = getattr(request, "user", None)
        if user is not None and not getattr(user, "is_authenticated", False):
            user = None
        ip_address = self._get_client_ip(request)

        return self.log(
            tenant=tenant,
            action=action,
            user=user,
            product=product,
            ip_address=ip_address,
            **details,
        )

    @staticmethod
    def _get_client_ip(request) -> str | None:
        """Extract client IP, preferring X-Forwarded-For for proxied requests."""
        forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")
