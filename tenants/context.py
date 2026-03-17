"""Thread-local storage for the current tenant.

The ``TenantMiddleware`` writes to this context on every request so that
model managers, service layers, and serializers can read the active
tenant without needing an explicit ``request`` parameter.

Usage::

    from tenants.context import get_current_tenant, set_current_tenant

    # In middleware / views
    set_current_tenant(tenant_instance)

    # Anywhere else
    tenant = get_current_tenant()  # may be None
"""

import threading

_thread_locals = threading.local()


def set_current_tenant(tenant):
    _thread_locals.tenant = tenant


def get_current_tenant():
    return getattr(_thread_locals, "tenant", None)


def clear_current_tenant():
    _thread_locals.tenant = None
