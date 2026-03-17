"""API URL configuration.

All endpoints are registered under ``/api/v1/`` using DRF's
DefaultRouter for automatic URL discovery and a browsable root.
"""

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

urlpatterns = router.urls
