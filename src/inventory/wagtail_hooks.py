"""Wagtail hooks for the inventory app.

Tenant-facing day-to-day ops use the REST API and Next.js app. Staff still get
tenant-scoped **Warehouses & locations** snippets (see :mod:`inventory.snippets`)
plus hooks used elsewhere (e.g. dashboard panels if re-enabled).
"""

import inventory.snippets  # noqa: F401 — registers Warehouse + StockLocation snippet group
