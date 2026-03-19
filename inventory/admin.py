"""Django admin configuration for the inventory app.

Configures list displays, filters, and admin interface for
inventory models that aren't managed through Wagtail snippets.
Tenant-scoped models (StockRecord, StockMovement) are managed
via the tenant frontend dashboard, not platform admin.
"""
