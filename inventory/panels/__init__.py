"""Wagtail admin dashboard panels for inventory health.

Each panel is a :class:`Component` subclass following the project's OOP
standard, rendered on the Wagtail admin homepage via the
``construct_homepage_panels`` hook.
"""

from .low_stock import LowStockPanel
from .recent_movements import RecentMovementsPanel
from .stock_summary import StockSummaryPanel

__all__ = [
    "LowStockPanel",
    "RecentMovementsPanel",
    "StockSummaryPanel",
]
