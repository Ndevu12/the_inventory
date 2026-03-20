from rest_framework.permissions import BasePermission

from tenants.context import get_current_tenant
from tenants.middleware import get_effective_tenant
from tenants.models import TenantMembership, TenantRole

_ADMIN_ROLES = {TenantRole.OWNER, TenantRole.ADMIN}


class IsStaffUser(BasePermission):
    """Allow access only to authenticated staff users."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_staff
        )


class ReadOnlyOrStaff(BasePermission):
    """Allow read access to authenticated users, write access to staff only."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        return request.user.is_staff


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


class IsAdminOrOwner(BasePermission):
    """Allow access to tenant admins, tenant owners, and Django superusers.

    Works regardless of whether the tenant context was resolved by
    middleware (JWT auth) or not (Token / Session auth).  When no
    current tenant is available, falls back to checking the user's
    memberships directly.
    """

    message = "Admin or owner access is required."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True

        tenant = get_current_tenant()
        if tenant is None:
            tenant = get_effective_tenant(request)
        qs = TenantMembership.objects.filter(
            user=user, is_active=True, role__in=_ADMIN_ROLES,
        )
        if tenant is not None:
            qs = qs.filter(tenant=tenant)
        return qs.exists()
