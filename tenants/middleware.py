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

from tenants.context import clear_current_tenant, set_current_tenant


class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tenant = self._resolve_tenant(request)
        request.tenant = tenant
        set_current_tenant(tenant)

        try:
            response = self.get_response(request)
        finally:
            clear_current_tenant()
        return response

    # -----------------------------------------------------------------

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
