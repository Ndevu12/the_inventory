"""Tenant resolution and impersonation middleware.

TenantMiddleware resolves the active tenant and stores it in both
``request.tenant`` and thread-local context.

ImpersonationMiddleware (session-based) swaps request.user to the
impersonated user when a superuser has started impersonation via
Wagtail admin. API impersonation uses token swap (no middleware).
"""

import logging

from django.conf import settings as django_settings

from tenants.context import (
    clear_current_tenant,
    clear_impersonation_context,
    set_current_tenant,
    set_impersonation_context,
)

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


class ImpersonationMiddleware:
    """Session-based impersonation for Wagtail admin.

    When a superuser has started impersonation (session contains
    _impersonating_user_id), swap request.user to the impersonated user.
    Only applies to session-authenticated requests (not JWT API requests).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        self._apply_impersonation(request)
        try:
            return self.get_response(request)
        finally:
            clear_impersonation_context()

    @staticmethod
    def _apply_impersonation(request):
        """Swap to impersonated user when session indicates impersonation."""
        # Skip for JWT-authenticated requests (API uses token swap, not session)
        if getattr(request, "auth", None) is not None:
            return
        if not hasattr(request, "user") or not request.user.is_authenticated:
            return
        if not request.user.is_superuser:
            return

        session = getattr(request, "session", None)
        if session is None:
            return

        imp_user_id = session.get("_impersonating_user_id")
        if not imp_user_id:
            return

        from django.contrib.auth import get_user_model

        User = get_user_model()
        try:
            imp_user = User.objects.get(pk=imp_user_id, is_active=True)
        except User.DoesNotExist:
            session.pop("_impersonating_user_id", None)
            return

        if imp_user.pk == request.user.pk:
            session.pop("_impersonating_user_id", None)
            return

        request._real_user = request.user
        request.user = imp_user
        request._impersonating = True

        set_impersonation_context(
            real_user=request._real_user,
            impersonated_user=imp_user,
        )
