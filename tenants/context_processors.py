"""Template context processor that exposes tenant branding to templates.

Add ``'tenants.context_processors.tenant_branding'`` to the
``context_processors`` list in ``TEMPLATES`` settings to use this.
"""

from tenants.context import get_current_tenant


def tenant_branding(request):
    tenant = getattr(request, "tenant", None) or get_current_tenant()
    if not tenant:
        return {}
    return {
        "tenant": tenant,
        "tenant_site_name": tenant.display_name,
        "tenant_primary_color": tenant.branding_primary_color,
        "tenant_logo": tenant.branding_logo,
    }
