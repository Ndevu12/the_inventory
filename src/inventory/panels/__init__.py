"""Wagtail admin dashboard panels for inventory health.

Each panel is a :class:`Component` subclass following the project's OOP
standard, rendered on the Wagtail admin homepage via the
``construct_homepage_panels`` hook.
"""

from .expiring_lots import ExpiringLotsPanel
from .low_stock import LowStockPanel
from .movement_trend_chart import MovementTrendChart
from .order_status_chart import OrderStatusChart
from .pending_reservations import PendingReservationsPanel
from .recent_movements import RecentMovementsPanel
from .stock_by_location_chart import StockByLocationChart
from .stock_summary import StockSummaryPanel

__all__ = [
    "ExpiringLotsPanel",
    "LowStockPanel",
    "MovementTrendChart",
    "OrderStatusChart",
    "PendingReservationsPanel",
    "RecentMovementsPanel",
    "StockByLocationChart",
    "StockSummaryPanel",
]
