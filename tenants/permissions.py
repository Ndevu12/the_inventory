"""RBAC permission helpers for tenant-scoped access control.

Provides both DRF permission classes and utility functions for checking
a user's role within the current tenant.
"""

from rest_framework.permissions import BasePermission

from tenants.context import get_current_tenant
from tenants.middleware import get_effective_tenant
from tenants.models import TenantMembership, TenantRole


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------


def get_membership(user, tenant=None, request=None):
    """Return the active TenantMembership for a user in a tenant.

    When *tenant* is omitted, uses thread-local tenant or, if *request* is
    given, :func:`~tenants.middleware.get_effective_tenant` (JWT-safe).
    """
    if tenant is None:
        tenant = get_current_tenant()
        if tenant is None and request is not None:
            tenant = get_effective_tenant(request)
    if not tenant or not user or not user.is_authenticated:
        return None
    return TenantMembership.objects.filter(
        user=user,
        tenant=tenant,
        is_active=True,
    ).first()


def has_role(user, *roles, tenant=None, request=None):
    """Check if user holds one of the given roles in the tenant."""
    membership = get_membership(user, tenant=tenant, request=request)
    if not membership:
        return False
    return membership.role in {r.value if isinstance(r, TenantRole) else r for r in roles}


def can_manage(user, tenant=None, request=None):
    """Owner / admin / manager — can create, update, and delete data."""
    return has_role(
        user, TenantRole.OWNER, TenantRole.ADMIN, TenantRole.MANAGER,
        tenant=tenant, request=request,
    )


def can_admin(user, tenant=None, request=None):
    """Owner / admin — can manage tenant settings and members."""
    return has_role(
        user, TenantRole.OWNER, TenantRole.ADMIN, tenant=tenant, request=request,
    )


def is_owner(user, tenant=None, request=None):
    return has_role(user, TenantRole.OWNER, tenant=tenant, request=request)


# ---------------------------------------------------------------------------
# DRF permission classes
# ---------------------------------------------------------------------------


class IsTenantMember(BasePermission):
    """Allows access if the user has any active membership in the current tenant."""

    message = "You do not have access to this tenant."

    def has_permission(self, request, view):
        return get_membership(request.user, request=request) is not None


class IsTenantManager(BasePermission):
    """Allows access if the user is owner, admin, or manager."""

    message = "Manager-level access is required."

    def has_permission(self, request, view):
        return can_manage(request.user, request=request)


class IsTenantAdmin(BasePermission):
    """Allows access if the user is owner or admin."""

    message = "Admin-level access is required."

    def has_permission(self, request, view):
        return can_admin(request.user, request=request)


class IsTenantOwner(BasePermission):
    """Allows access only to the tenant owner."""

    message = "Owner-level access is required."

    def has_permission(self, request, view):
        return is_owner(request.user, request=request)


class TenantReadOnlyOrManager(BasePermission):
    """Viewers get read-only; managers and above get full access."""

    def has_permission(self, request, view):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            membership = get_membership(request.user, request=request)
            if membership is not None:
                return True
            tenant = get_current_tenant()
            if tenant is None:
                tenant = get_effective_tenant(request)
            if (
                tenant is None
                and request.user
                and request.user.is_authenticated
            ):
                self.message = "No tenant context available."
            return False
        return can_manage(request.user, request=request)
