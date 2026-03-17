"""Subscription statistics dashboard panel."""

from django.db.models import Count
from wagtail.admin.ui.components import Component

from tenants.models import SubscriptionPlan, SubscriptionStatus, Tenant


class SubscriptionStatsPanel(Component):
    """Breakdown of tenants by subscription plan and status."""

    name = "subscription_stats"
    template_name = "tenants/panels/subscription_stats.html"
    order = 110

    def get_context_data(self, parent_context=None):
        context = super().get_context_data(parent_context)

        plan_counts = dict(
            Tenant.objects.values_list("subscription_plan")
            .annotate(count=Count("id"))
            .values_list("subscription_plan", "count")
        )
        context["plan_stats"] = [
            {"label": label, "value": value, "count": plan_counts.get(value, 0)}
            for value, label in SubscriptionPlan.choices
        ]

        status_counts = dict(
            Tenant.objects.values_list("subscription_status")
            .annotate(count=Count("id"))
            .values_list("subscription_status", "count")
        )
        context["status_stats"] = [
            {"label": label, "value": value, "count": status_counts.get(value, 0)}
            for value, label in SubscriptionStatus.choices
        ]

        return context
