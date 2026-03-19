"""Django admin configuration for the procurement app.

Supplier is managed via Wagtail snippets. Tenant-scoped models
(PurchaseOrder, GoodsReceivedNote) are managed via the tenant frontend
dashboard, not platform admin.
"""
