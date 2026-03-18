"""Tenant resolution middleware.

On every request the middleware resolves the active tenant and stores it
in both ``request.tenant`` and thread-local context so that model
managers can scope queries automatically.

Resolution order:
1. ``X-Tenant`` HTTP header (API consumers switching tenant context)
2. ``tenant`` query parameter
3. The user's default ``TenantMembership``
4. The user's first active membership (fallback)

Anonymous requests get ``tenant = None``, which means all tenant-aware
managers return an empty queryset — safe by default.
"""

import logging

from django.conf import settings as django_settings

from tenants.context import clear_current_tenant, set_current_tenant

logger = logging.getLogger(__name__)


class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tenant = self._resolve_tenant(request)
        request.tenant = tenant
        set_current_tenant(tenant)
        self._audit_tenant_access(request, tenant)

        try:
            response = self.get_response(request)
        finally:
            clear_current_tenant()
        return response

    # -----------------------------------------------------------------

    @staticmethod
    def _audit_tenant_access(request, tenant):
        """Log an audit entry when the resolved tenant changes within a session.

        Controlled by ``settings.AUDIT_TENANT_ACCESS`` (default ``False``).
        Uses the Django session to track the previously-accessed tenant slug;
        a log entry is created only when the slug differs (including the
        very first tenant access in a new session).
        """
        if not getattr(django_settings, "AUDIT_TENANT_ACCESS", False):
            return
        if tenant is None:
            return
        if not hasattr(request, "user") or not request.user.is_authenticated:
            return

        session = getattr(request, "session", None)
        if session is None:
            return

        current_slug = tenant.slug
        previous_slug = session.get("_audit_last_tenant_slug")
        if previous_slug == current_slug:
            return

        session["_audit_last_tenant_slug"] = current_slug

        from inventory.services.audit import AuditService

        AuditService().log_from_request(
            request,
            action="tenant_accessed",
            tenant_slug=current_slug,
            previous_tenant_slug=previous_slug,
        )
        logger.debug(
            "Tenant access audited: user=%s switched %s → %s",
            getattr(request.user, "pk", None),
            previous_slug,
            current_slug,
        )

    @staticmethod
    def _resolve_tenant(request):
        if not hasattr(request, "user") or not request.user.is_authenticated:
            return None

        from tenants.models import TenantMembership

        memberships = TenantMembership.objects.filter(
            user=request.user,
            is_active=True,
            tenant__is_active=True,
        ).select_related("tenant")

        if not memberships.exists():
            return None

        # 1) Header override (for API switching)
        header_slug = request.META.get("HTTP_X_TENANT")
        if header_slug:
            m = memberships.filter(tenant__slug=header_slug).first()
            if m:
                return m.tenant

        # 2) Query-parameter override
        param_slug = request.GET.get("tenant")
        if param_slug:
            m = memberships.filter(tenant__slug=param_slug).first()
            if m:
                return m.tenant

        # 3) Default membership
        default = memberships.filter(is_default=True).first()
        if default:
            return default.tenant

        # 4) First active membership
        return memberships.first().tenant
