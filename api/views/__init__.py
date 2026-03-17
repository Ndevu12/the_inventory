from .inventory import (
    CategoryViewSet,
    ProductViewSet,
    StockLocationViewSet,
    StockMovementViewSet,
    StockRecordViewSet,
)
from .procurement import (
    GoodsReceivedNoteViewSet,
    PurchaseOrderViewSet,
    SupplierViewSet,
)
from .sales import (
    CustomerViewSet,
    DispatchViewSet,
    SalesOrderViewSet,
)

__all__ = [
    "CategoryViewSet",
    "CustomerViewSet",
    "DispatchViewSet",
    "GoodsReceivedNoteViewSet",
    "ProductViewSet",
    "PurchaseOrderViewSet",
    "SalesOrderViewSet",
    "StockLocationViewSet",
    "StockMovementViewSet",
    "StockRecordViewSet",
    "SupplierViewSet",
]
