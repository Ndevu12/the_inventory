"""Recent tenants dashboard panel."""

from wagtail.admin.ui.components import Component

from tenants.models import Tenant


class RecentTenantsPanel(Component):
    """Last 10 tenants created on the platform."""

    name = "recent_tenants"
    template_name = "tenants/panels/recent_tenants.html"
    order = 120

    def get_context_data(self, parent_context=None):
        context = super().get_context_data(parent_context)
        context["recent_tenants"] = Tenant.objects.order_by("-created_at")[:10]
        return context
