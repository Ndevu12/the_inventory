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
    ComplianceAuditLogViewSet,
    CustomerViewSet,
    DispatchViewSet,
    GoodsReceivedNoteViewSet,
    ProductViewSet,
    PurchaseOrderViewSet,
    SalesOrderViewSet,
    StockLocationViewSet,
    StockLotViewSet,
    StockMovementViewSet,
    StockRecordViewSet,
    StockReservationViewSet,
    SupplierViewSet,
)
from api.views.auth import ChangePasswordView, LoginView, MeView, RefreshView
from api.views.dashboard import (
    DashboardSummaryView,
    ExpiringLotsView,
    MovementTrendsView,
    OrderStatusView,
    PendingReservationsView,
    StockByLocationView,
)
from api.views.imports import ImportDataView
from api.views.reports import (
    AvailabilityReportView,
    CycleHistoryView,
    LotHistoryView,
    LowStockReportView,
    MovementHistoryView,
    OverstockReportView,
    ProductExpiryView,
    ProductTraceabilityView,
    PurchaseSummaryView,
    ReservationSummaryView,
    SalesSummaryView,
    StockValuationView,
    VarianceReportView,
)
from api.views.bulk import BulkAdjustmentView, BulkRevalueView, BulkTransferView
from api.views.jobs import JobListView, JobStatusView
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
router.register("stock-lots", StockLotViewSet, basename="stocklot")
router.register("reservations", StockReservationViewSet, basename="reservation")
router.register("audit-log", ComplianceAuditLogViewSet, basename="auditlog")
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
    path("reports/reservation-summary/", ReservationSummaryView.as_view(), name="api-reservation-summary"),
    path("reports/availability/", AvailabilityReportView.as_view(), name="api-availability"),
    path("reports/product-traceability/", ProductTraceabilityView.as_view(), name="api-product-traceability"),
    path("reports/product-expiry/", ProductExpiryView.as_view(), name="api-product-expiry"),
    path("reports/lot-history/", LotHistoryView.as_view(), name="api-lot-history"),
    path("reports/variances/", VarianceReportView.as_view(), name="api-variance-report"),
    path("reports/cycle-history/", CycleHistoryView.as_view(), name="api-cycle-history"),

    # Dashboard
    path("dashboard/summary/", DashboardSummaryView.as_view(), name="api-dashboard-summary"),
    path("dashboard/stock-by-location/", StockByLocationView.as_view(), name="api-stock-by-location"),
    path("dashboard/movement-trends/", MovementTrendsView.as_view(), name="api-movement-trends"),
    path("dashboard/order-status/", OrderStatusView.as_view(), name="api-order-status"),
    path("dashboard/reservations/", PendingReservationsView.as_view(), name="api-dashboard-reservations"),
    path("dashboard/expiring-lots/", ExpiringLotsView.as_view(), name="api-dashboard-expiring-lots"),

    # Tenants
    path("tenants/current/", CurrentTenantView.as_view(), name="api-current-tenant"),
    path("tenants/members/", TenantMemberListView.as_view(), name="api-tenant-members"),
    path("tenants/members/<int:pk>/", TenantMemberDetailView.as_view(), name="api-tenant-member-detail"),

    # Bulk operations
    path("bulk-operations/transfer/", BulkTransferView.as_view(), name="api-bulk-transfer"),
    path("bulk-operations/adjust/", BulkAdjustmentView.as_view(), name="api-bulk-adjust"),
    path("bulk-operations/revalue/", BulkRevalueView.as_view(), name="api-bulk-revalue"),

    # Import
    path("import/", ImportDataView.as_view(), name="api-import"),

    # Async jobs
    path("jobs/", JobListView.as_view(), name="api-job-list"),
    path("jobs/<uuid:job_id>/status/", JobStatusView.as_view(), name="api-job-status"),

    # API documentation
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
] + router.urls
