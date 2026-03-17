"""Platform overview dashboard panel."""

from django.contrib.auth import get_user_model
from wagtail.admin.ui.components import Component

from tenants.models import Tenant, TenantMembership

User = get_user_model()


class PlatformOverviewPanel(Component):
    """At-a-glance platform metrics.

    Displays total tenants, active tenants, total users,
    and active memberships.
    """

    name = "platform_overview"
    template_name = "tenants/panels/platform_overview.html"
    order = 100

    def get_context_data(self, parent_context=None):
        context = super().get_context_data(parent_context)
        context["total_tenants"] = Tenant.objects.count()
        context["active_tenants"] = Tenant.objects.filter(is_active=True).count()
        context["total_users"] = User.objects.filter(is_active=True).count()
        context["active_memberships"] = TenantMembership.objects.filter(
            is_active=True
        ).count()
        return context
