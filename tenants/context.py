"""Thread-local storage for the current tenant and impersonation context.

The ``TenantMiddleware`` writes to this context on every request so that
model managers, service layers, and serializers can read the active
tenant without needing an explicit ``request`` parameter.

Impersonation context (real user, impersonated user) is set by
``ImpersonationMiddleware`` for session-based impersonation, or resolved
from JWT custom claims for API impersonation.

Usage::

    from tenants.context import get_current_tenant, set_current_tenant

    # In middleware / views
    set_current_tenant(tenant_instance)

    # Anywhere else
    tenant = get_current_tenant()  # may be None
    real_user = get_real_user()  # original user when impersonating
"""

import threading

_thread_locals = threading.local()


def set_current_tenant(tenant):
    _thread_locals.tenant = tenant


def get_current_tenant():
    return getattr(_thread_locals, "tenant", None)


def clear_current_tenant():
    _thread_locals.tenant = None


# ---------------------------------------------------------------------------
# Impersonation context
# ---------------------------------------------------------------------------


def set_impersonation_context(*, real_user, impersonated_user):
    """Set impersonation context for the current thread.

    real_user: the actual logged-in user (superuser who started impersonation)
    impersonated_user: the user being viewed as
    """
    _thread_locals.impersonation_real_user = real_user
    _thread_locals.impersonation_impersonated_user = impersonated_user


def get_real_user():
    """Return the real (actual) user when impersonating, else None."""
    return getattr(_thread_locals, "impersonation_real_user", None)


def get_impersonated_user():
    """Return the user being impersonated when active, else None."""
    return getattr(_thread_locals, "impersonation_impersonated_user", None)


def clear_impersonation_context():
    """Clear impersonation context for the current thread."""
    _thread_locals.impersonation_real_user = None
    _thread_locals.impersonation_impersonated_user = None


def is_impersonating():
    """Return True if the current request is in impersonation mode."""
    return get_real_user() is not None and get_impersonated_user() is not None
