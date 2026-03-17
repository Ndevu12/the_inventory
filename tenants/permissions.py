"""RBAC permission helpers for tenant-scoped access control.

Provides both DRF permission classes and utility functions for checking
a user's role within the current tenant.
"""

from rest_framework.permissions import BasePermission

from tenants.context import get_current_tenant
from tenants.models import TenantMembership, TenantRole


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------


def get_membership(user, tenant=None):
    """Return the active TenantMembership for a user in a tenant."""
    tenant = tenant or get_current_tenant()
    if not tenant or not user or not user.is_authenticated:
        return None
    return TenantMembership.objects.filter(
        user=user,
        tenant=tenant,
        is_active=True,
    ).first()


def has_role(user, *roles, tenant=None):
    """Check if user holds one of the given roles in the tenant."""
    membership = get_membership(user, tenant)
    if not membership:
        return False
    return membership.role in {r.value if isinstance(r, TenantRole) else r for r in roles}


def can_manage(user, tenant=None):
    """Owner / admin / manager — can create, update, and delete data."""
    return has_role(user, TenantRole.OWNER, TenantRole.ADMIN, TenantRole.MANAGER, tenant=tenant)


def can_admin(user, tenant=None):
    """Owner / admin — can manage tenant settings and members."""
    return has_role(user, TenantRole.OWNER, TenantRole.ADMIN, tenant=tenant)


def is_owner(user, tenant=None):
    return has_role(user, TenantRole.OWNER, tenant=tenant)


# ---------------------------------------------------------------------------
# DRF permission classes
# ---------------------------------------------------------------------------


class IsTenantMember(BasePermission):
    """Allows access if the user has any active membership in the current tenant."""

    message = "You do not have access to this tenant."

    def has_permission(self, request, view):
        return get_membership(request.user) is not None


class IsTenantManager(BasePermission):
    """Allows access if the user is owner, admin, or manager."""

    message = "Manager-level access is required."

    def has_permission(self, request, view):
        return can_manage(request.user)


class IsTenantAdmin(BasePermission):
    """Allows access if the user is owner or admin."""

    message = "Admin-level access is required."

    def has_permission(self, request, view):
        return can_admin(request.user)


class IsTenantOwner(BasePermission):
    """Allows access only to the tenant owner."""

    message = "Owner-level access is required."

    def has_permission(self, request, view):
        return is_owner(request.user)


class TenantReadOnlyOrManager(BasePermission):
    """Viewers get read-only; managers and above get full access."""

    def has_permission(self, request, view):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return get_membership(request.user) is not None
        return can_manage(request.user)
