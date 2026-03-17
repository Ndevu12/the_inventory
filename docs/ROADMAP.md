# Roadmap

This document outlines the planned development phases for **The Inventory**. Each phase builds on the previous one, progressively extending the system from a core inventory tracker into a full-featured inventory management platform.

> **Status key:** ✅ Done · 🚧 In Progress · 📋 Planned

---

## Phase 1 — Core Inventory (Building Now) 🚧

The foundation: manage products, track stock, and move items between locations. This is what we are actively building. See [Architecture](ARCHITECTURE.md) for the full schema design.

**App:** `inventory/`

**Models:** `TimeStampedModel` (abstract base), `Category`, `Product`, `ProductImage`, `ProductTag`, `StockLocation`, `StockRecord`, `StockMovement`

| Feature | Status |
|---|---|
| `TimeStampedModel` abstract base (audit: `created_at`, `updated_at`, `created_by`) | 📋 |
| `Category` model — hierarchical tree via `treebeard`, soft-delete | 📋 |
| `Product` model — SKU, name, description, unit of measure, unit cost, reorder point, soft-delete | 📋 |
| `ProductImage` — multiple orderable images per product | 📋 |
| `ProductTag` — free-form tagging via `django-taggit` | 📋 |
| `StockLocation` model — hierarchical tree (warehouse → shelf → bin), soft-delete | 📋 |
| `StockRecord` model — current quantity per product per location, low-stock property | 📋 |
| `StockMovement` model — receive, issue, transfer, adjustment with point-in-time unit cost | 📋 |
| Stock movement processing — atomic quantity updates on save, validation rules | 📋 |
| Low-stock alerts — filtered admin view, dashboard widget | 📋 |
| Full-text search & filtering via Wagtail search backend and `django-filter` | 📋 |
| Wagtail admin dashboard widgets (stock summary, low-stock, recent movements) | 📋 |
| Unit tests for all inventory models | 📋 |
| Integration tests for stock movement flow | 📋 |

**Goal:** A fully functional, well-tested inventory system usable through the Wagtail admin.

---

> **Everything below is planned for future phases.** These features are not yet in development and their designs may change based on Phase 1 learnings.

---

## Phase 2 — Procurement & Sales 🚧

Extend the system to track the full lifecycle of goods — from purchase orders to customer sales.

**Apps:** `procurement/`, `sales/`

**Models:** `Supplier`, `PurchaseOrder`, `PurchaseOrderLine`, `GoodsReceivedNote`, `Customer`, `SalesOrder`, `SalesOrderLine`, `Dispatch`

| Feature | Status |
|---|---|
| Supplier management (contacts, lead times, terms) | ✅ |
| Purchase orders with line items | ✅ |
| Goods received notes (GRN) — auto-create `receive` StockMovement | ✅ |
| Customer / client management | ✅ |
| Sales orders with line items | ✅ |
| Dispatch / shipment tracking — auto-create `issue` StockMovement | ✅ |
| Order status workflows (draft → confirmed → fulfilled) | ✅ |
| ProcurementService (confirm, cancel, receive goods) | ✅ |
| SalesService (confirm, cancel, process dispatch) | ✅ |
| Unit tests for all procurement models | ✅ |
| Unit tests for all sales models | ✅ |
| Integration tests for procurement workflows | ✅ |
| Integration tests for sales/dispatch workflows | ✅ |
| Wagtail admin menu items for procurement & sales | ✅ |
| Django admin for orders, GRNs, and dispatches | ✅ |

---

## Phase 3 — Reporting & Analytics 🚧

Provide insight into inventory health, movement trends, and financial summaries.

**App:** `reports/` (no persistent models — read-only views and exports)

| Feature | Status |
|---|---|
| Stock valuation reports (weighted average / latest cost via `StockMovement.unit_cost`) | ✅ |
| Movement history & audit trail (filterable by date, type, product, location) | ✅ |
| Low-stock report | ✅ |
| Overstock report (configurable threshold multiplier) | ✅ |
| Purchase summaries (daily / weekly / monthly with totals) | ✅ |
| Sales summaries (daily / weekly / monthly with totals) | ✅ |
| CSV export on all reports (`?export=csv`) | ✅ |
| InventoryReportService (valuation, stock levels, movements) | ✅ |
| OrderReportService (purchase & sales aggregations) | ✅ |
| Wagtail admin Reports submenu with all 6 report views | ✅ |
| Unit tests for both report services | ✅ |
| Integration tests for all report views | ✅ |
| PDF export on all reports (`?export=pdf`) via ReportLab | ✅ |
| Dashboard charts — stock by location, movement trends, order status (Chart.js) | ✅ |

---

## Phase 4 — API & Integrations ✅

Open up the system for external consumers and third-party integrations.

**App:** `api/`

| Feature | Status |
|---|---|
| RESTful API (Django REST Framework) for products, stock, orders | ✅ |
| Token authentication (`rest_framework.authtoken`) | ✅ |
| JWT authentication (`djangorestframework-simplejwt`) | ✅ |
| Session authentication (for browsable API) | ✅ |
| Staff-only permission enforcement | ✅ |
| Pagination (configurable page size, max 100) | ✅ |
| Filtering via `django-filter` on all list endpoints | ✅ |
| Search and ordering on products, suppliers, customers | ✅ |
| Custom actions: confirm/cancel orders, receive goods, process dispatch | ✅ |
| Stock movement creation via StockService (atomic) | ✅ |
| Read-only stock records with low-stock endpoint | ✅ |
| Immutable movements (no update/delete via API) | ✅ |
| Nested serializers (order lines, related names) | ✅ |
| Full test suite for all API endpoints | ✅ |
| Import via CSV & Excel (products, suppliers, customers) | ✅ |
| CORS support (`django-cors-headers`) for frontend dev | ✅ |
| Auth API: login, refresh, /me profile, change-password | ✅ |
| Reports API: 6 JSON endpoints with CSV/PDF export | ✅ |
| Dashboard API: summary, stock-by-location, movement-trends, order-status | ✅ |
| Tenant management API: current tenant, member list/update/delete | ✅ |
| Import API: file upload endpoint for CSV/Excel | ✅ |
| OpenAPI schema + Swagger UI + Redoc (`drf-spectacular`) | ✅ |
| Webhook support for stock events | 📋 |
| Barcode / QR code scanning support | 📋 |
| Optional Elasticsearch backend for advanced search | 📋 |

---

## Phase 5 — Multi-tenancy & SaaS (Stretch) 🚧

Enable multiple organizations to use a single deployment.

**App:** `tenants/`

**Models:** `Tenant`, `TenantMembership`

| Feature | Status |
|---|---|
| `Tenant` model — org name, slug, active flag, branding fields, subscription metadata | ✅ |
| `TenantMembership` model — user ↔ tenant link with role (owner/admin/manager/viewer) | ✅ |
| Tenant FK on `TimeStampedModel` — all 13 domain models scoped to a tenant | ✅ |
| Data migration — default tenant created, all existing records assigned | ✅ |
| `TenantMiddleware` — resolves tenant from user membership, header, or query param | ✅ |
| Thread-local tenant context (`set_current_tenant` / `get_current_tenant`) | ✅ |
| `TenantAwareManager` with auto-scoping and `unscoped()` escape hatch | ✅ |
| Per-tenant admin branding (site name, primary colour, logo via context processor) | ✅ |
| Role-based access control (RBAC) — utility functions and 5 DRF permission classes | ✅ |
| Subscription / billing hooks (plan, status, user/product limits on `Tenant`) | ✅ |
| Django admin for tenants and memberships | ✅ |
| Wagtail admin menu item for tenant management | ✅ |
| Full test suite (72 tests): models, middleware, context, managers, permissions, cross-app integration | ✅ |
| Per-tenant unique constraints (sku, code, order_number per tenant) | ✅ |
| Tenant-scoped Wagtail Snippet querysets (`TenantScopedSnippetViewSet`) | ✅ |
| Tenant provisioning API / self-service signup | 📋 |

---

## How to Contribute

Pick any **📋 Planned** item, open an issue to discuss your approach, and submit a PR. See the [Contributing Guide](../CONTRIBUTING.md) for workflow details.
