"""Wagtail hooks for the reports app.

Registers admin URLs and menu items for all report views.
"""

from django.urls import path, reverse
from wagtail import hooks
from wagtail.admin.menu import MenuItem, SubmenuMenuItem, Menu

from reports.views import (
    LowStockReportView,
    MovementHistoryView,
    OverstockReportView,
    PurchaseSummaryView,
    SalesSummaryView,
    StockValuationView,
)


@hooks.register("register_admin_urls")
def register_report_admin_urls():
    return [
        path(
            "reports/stock-valuation/",
            StockValuationView.as_view(),
            name="report_stock_valuation",
        ),
        path(
            "reports/movement-history/",
            MovementHistoryView.as_view(),
            name="report_movement_history",
        ),
        path(
            "reports/low-stock/",
            LowStockReportView.as_view(),
            name="report_low_stock",
        ),
        path(
            "reports/overstock/",
            OverstockReportView.as_view(),
            name="report_overstock",
        ),
        path(
            "reports/purchase-summary/",
            PurchaseSummaryView.as_view(),
            name="report_purchase_summary",
        ),
        path(
            "reports/sales-summary/",
            SalesSummaryView.as_view(),
            name="report_sales_summary",
        ),
    ]


reports_menu = Menu(
    register_hook_name="register_reports_menu_item",
    construct_hook_name="construct_reports_menu",
)


@hooks.register("register_admin_menu_item")
def register_reports_submenu():
    return SubmenuMenuItem(
        "Reports",
        reports_menu,
        icon_name="clipboard-list",
        order=400,
    )


@hooks.register("register_reports_menu_item")
def register_stock_valuation_menu():
    return MenuItem(
        "Stock Valuation",
        reverse("report_stock_valuation"),
        icon_name="doc-full",
        order=100,
    )


@hooks.register("register_reports_menu_item")
def register_movement_history_menu():
    return MenuItem(
        "Movement History",
        reverse("report_movement_history"),
        icon_name="history",
        order=200,
    )


@hooks.register("register_reports_menu_item")
def register_low_stock_report_menu():
    return MenuItem(
        "Low Stock",
        reverse("report_low_stock"),
        icon_name="warning",
        order=300,
    )


@hooks.register("register_reports_menu_item")
def register_overstock_report_menu():
    return MenuItem(
        "Overstock",
        reverse("report_overstock"),
        icon_name="plus-inverse",
        order=400,
    )


@hooks.register("register_reports_menu_item")
def register_purchase_summary_menu():
    return MenuItem(
        "Purchase Summary",
        reverse("report_purchase_summary"),
        icon_name="doc-full-inverse",
        order=500,
    )


@hooks.register("register_reports_menu_item")
def register_sales_summary_menu():
    return MenuItem(
        "Sales Summary",
        reverse("report_sales_summary"),
        icon_name="doc-full-inverse",
        order=600,
    )
