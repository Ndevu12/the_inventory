"""Platform dashboard panels for the Wagtail admin homepage."""

from .platform_overview import PlatformOverviewPanel
from .recent_tenants import RecentTenantsPanel
from .subscription_stats import SubscriptionStatsPanel

__all__ = [
    "PlatformOverviewPanel",
    "SubscriptionStatsPanel",
    "RecentTenantsPanel",
]
