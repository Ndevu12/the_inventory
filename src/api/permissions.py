from rest_framework.permissions import BasePermission

from tenants.context import get_current_tenant
from tenants.middleware import get_effective_tenant
from tenants.models import TenantMembership, TenantRole

_TENANT_GOVERNANCE_ROLES = {TenantRole.OWNER, TenantRole.COORDINATOR}


class IsStaffUser(BasePermission):
    """Allow access only to authenticated staff users."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_staff
        )


class IsPlatformSuperuser(BasePermission):
    """Allow access only to Django superusers (platform-level admin).

    Used for platform user management and other cross-tenant admin features.
    No tenant context is required.
    """

    message = "Platform superuser access is required."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_superuser
        )


# Permission codename for Wagtail admin menu (mirrors ``require_admin_access``).
_WAGTAIL_ACCESS_ADMIN = "wagtailadmin.access_admin"


class IsPlatformAuditAPIAccess(BasePermission):
    """Full compliance audit via REST — same audience as the Wagtail platform audit snippet.

    Allows **active** Django superusers or any user with **``wagtailadmin.access_admin``**
    (typical Wagtail staff). Matches :class:`PlatformAuditLogPermissionPolicy` in
    ``inventory.wagtail_audit_snippet``.
    """

    message = "Platform audit access requires superuser or Wagtail admin permission."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated or not user.is_active:
            return False
        if user.is_superuser:
            return True
        return user.has_perm(_WAGTAIL_ACCESS_ADMIN)


class IsTenantMemberAuthorizedForAuditLog(BasePermission):
    """Allow access to users with organization governance roles (JWT membership).

    Django superusers have no special access here; platform-wide audit uses
    :class:`IsPlatformSuperuser` on separate routes.

    Works regardless of whether the tenant context was resolved by
    middleware (JWT auth) or not (Token / Session auth). When no
    current tenant is available, falls back to checking the user's
    memberships directly.
    """

    message = "Organization governance access is required for the audit log."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        tenant = get_current_tenant()
        if tenant is None:
            tenant = get_effective_tenant(request)
        qs = TenantMembership.objects.filter(
            user=user, is_active=True, role__in=_TENANT_GOVERNANCE_ROLES,
        )
        if tenant is not None:
            qs = qs.filter(tenant=tenant)
        return qs.exists()
