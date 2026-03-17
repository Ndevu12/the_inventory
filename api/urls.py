"""API URL configuration.

All endpoints are registered under ``/api/v1/``.  The router handles
CRUD ViewSets while additional paths cover auth, reports, dashboard,
tenants, import, and API documentation.
"""

from django.urls import path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework.routers import DefaultRouter

from api.views import (
    CategoryViewSet,
    CustomerViewSet,
    DispatchViewSet,
    GoodsReceivedNoteViewSet,
    ProductViewSet,
    PurchaseOrderViewSet,
    SalesOrderViewSet,
    StockLocationViewSet,
    StockMovementViewSet,
    StockRecordViewSet,
    SupplierViewSet,
)
from api.views.auth import ChangePasswordView, LoginView, MeView, RefreshView
from api.views.dashboard import (
    DashboardSummaryView,
    MovementTrendsView,
    OrderStatusView,
    StockByLocationView,
)
from api.views.imports import ImportDataView
from api.views.reports import (
    LowStockReportView,
    MovementHistoryView,
    OverstockReportView,
    PurchaseSummaryView,
    SalesSummaryView,
    StockValuationView,
)
from api.views.tenants import (
    CurrentTenantView,
    TenantMemberDetailView,
    TenantMemberListView,
)

router = DefaultRouter()

# Inventory
router.register("categories", CategoryViewSet, basename="category")
router.register("products", ProductViewSet, basename="product")
router.register("stock-locations", StockLocationViewSet, basename="stocklocation")
router.register("stock-records", StockRecordViewSet, basename="stockrecord")
router.register("stock-movements", StockMovementViewSet, basename="stockmovement")

# Procurement
router.register("suppliers", SupplierViewSet, basename="supplier")
router.register("purchase-orders", PurchaseOrderViewSet, basename="purchaseorder")
router.register("goods-received-notes", GoodsReceivedNoteViewSet, basename="goodsreceivednote")

# Sales
router.register("customers", CustomerViewSet, basename="customer")
router.register("sales-orders", SalesOrderViewSet, basename="salesorder")
router.register("dispatches", DispatchViewSet, basename="dispatch")

urlpatterns = [
    # Auth
    path("auth/login/", LoginView.as_view(), name="api-login"),
    path("auth/refresh/", RefreshView.as_view(), name="api-token-refresh"),
    path("auth/me/", MeView.as_view(), name="api-me"),
    path("auth/change-password/", ChangePasswordView.as_view(), name="api-change-password"),

    # Reports
    path("reports/stock-valuation/", StockValuationView.as_view(), name="api-stock-valuation"),
    path("reports/movement-history/", MovementHistoryView.as_view(), name="api-movement-history"),
    path("reports/low-stock/", LowStockReportView.as_view(), name="api-low-stock"),
    path("reports/overstock/", OverstockReportView.as_view(), name="api-overstock"),
    path("reports/purchase-summary/", PurchaseSummaryView.as_view(), name="api-purchase-summary"),
    path("reports/sales-summary/", SalesSummaryView.as_view(), name="api-sales-summary"),

    # Dashboard
    path("dashboard/summary/", DashboardSummaryView.as_view(), name="api-dashboard-summary"),
    path("dashboard/stock-by-location/", StockByLocationView.as_view(), name="api-stock-by-location"),
    path("dashboard/movement-trends/", MovementTrendsView.as_view(), name="api-movement-trends"),
    path("dashboard/order-status/", OrderStatusView.as_view(), name="api-order-status"),

    # Tenants
    path("tenants/current/", CurrentTenantView.as_view(), name="api-current-tenant"),
    path("tenants/members/", TenantMemberListView.as_view(), name="api-tenant-members"),
    path("tenants/members/<int:pk>/", TenantMemberDetailView.as_view(), name="api-tenant-member-detail"),

    # Import
    path("import/", ImportDataView.as_view(), name="api-import"),

    # API documentation
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
] + router.urls
