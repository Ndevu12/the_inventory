# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project aims to follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html) once it reaches a stable release.

## [Unreleased]

### Changed

- **Tenant RBAC vocabulary:** second-tier governance role renamed from `admin` / `TenantRole.ADMIN` to **`coordinator` / `TenantRole.COORDINATOR`** (data migration `0009_tenant_role_coordinator`). `can_admin` → `can_manage_organization`, `IsTenantAdmin` → `IsTenantGovernanceMember`, tenant audit permission `IsAdminOrOwner` → `IsTenantMemberAuthorizedForAuditLog`; API constant `_ADMIN_ROLES` → `_TENANT_GOVERNANCE_ROLES`. Next.js settings types and i18n keys updated accordingly.

### Added

- **Headless API Server Preparation:**
  - **JWT authentication** via `djangorestframework-simplejwt` — login, token refresh, and user profile endpoints at `/api/v1/auth/`
  - **CORS support** via `django-cors-headers` — configured for local frontend dev servers (localhost:3000, localhost:5173)
  - **OpenAPI documentation** via `drf-spectacular` — schema at `/api/v1/schema/`, Swagger UI at `/api/v1/docs/`, Redoc at `/api/v1/redoc/`
  - **Auth endpoints:** `/auth/login/` (JWT obtain with user/tenant info), `/auth/refresh/`, `/auth/me/` (GET/PATCH), `/auth/change-password/`
  - **Reports API:** 6 JSON endpoints at `/api/v1/reports/` (stock valuation, movement history, low-stock, overstock, purchase summary, sales summary) with `?export=csv` and `?export=pdf` support
  - **Dashboard API:** 4 endpoints at `/api/v1/dashboard/` (summary, stock-by-location, movement-trends, order-status) returning chart-ready data
  - **Tenant management API:** `/api/v1/tenants/current/` (GET/PATCH), `/api/v1/tenants/members/` (list/detail/update/delete) with RBAC enforcement
  - **Import API:** `/api/v1/import/` — multipart file upload for CSV/Excel bulk imports
  - **JWT auth middleware** — pre-authenticates JWT requests before TenantMiddleware for automatic tenant resolution
  - **Dependencies added:** `djangorestframework-simplejwt>=5.4`, `django-cors-headers>=4.6`, `drf-spectacular>=0.28`
  - Full test suite for all new endpoints (38 new tests, 462 total passing)

- **Phase 6 — Extended Features & Polish:**
  - **PDF export** on all 6 report views via `?export=pdf`, powered by ReportLab with styled table layouts, alternating row colours, and auto-generated timestamps
  - **Dashboard charts** using Chart.js on the Wagtail admin homepage:
    - Stock by Location (horizontal bar chart)
    - Movement Trends (30-day line chart)
    - Order Status (purchase + sales doughnut charts)
  - **CSV/Excel import** for Products, Suppliers, and Customers via a new Wagtail admin import view (`/admin/inventory/import/`), with file validation, row-level error reporting, and all-or-nothing transactions
  - **Per-tenant unique constraints** on SKU, slug, supplier code, customer code, order numbers, GRN numbers, and dispatch numbers — each field is now unique within a tenant, allowing the same identifiers across different organisations
  - **Tenant-scoped Wagtail Snippet querysets** via `TenantScopedSnippetViewSet` base class
  - **Dependencies added:** `reportlab>=4.0` (PDF generation), `openpyxl>=3.1` (Excel parsing)
  - Full test suite for all new features (51 new tests, 424 total passing)

- **Tenants app** (`tenants/`):
  - `Tenant` model with name, slug, active flag, branding fields (site name, primary colour, logo), and subscription metadata (plan, status, user/product limits)
  - `TenantMembership` model linking users to tenants with role-based access (owner, admin, manager, viewer)
  - `TenantMiddleware` that resolves the active tenant per request via user membership, `X-Tenant` header, or `?tenant=` query parameter
  - Thread-local tenant context (`set_current_tenant` / `get_current_tenant` / `clear_current_tenant`)
  - `TenantAwareManager` with auto-scoping `get_queryset()` and `unscoped()` escape hatch for cross-tenant operations
  - `TenantAwareQuerySet` with `.for_tenant()` helper
  - RBAC utility functions: `get_membership()`, `has_role()`, `can_manage()`, `can_admin()`, `is_owner()`
  - 5 DRF permission classes: `IsTenantMember`, `IsTenantManager`, `IsTenantAdmin`, `IsTenantOwner`, `TenantReadOnlyOrManager`
  - Per-tenant branding via `tenant_branding` template context processor
  - `tenant` FK added to `TimeStampedModel` — all 13 domain models across inventory, procurement, and sales are now tenant-scoped
  - Data migration: creates default tenant and assigns all existing records
  - Django admin for `Tenant` (with inline memberships) and `TenantMembership`
  - Wagtail admin menu item for tenant management
  - Full test suite (72 tests): models, middleware, context, managers, permissions, and cross-app integration

- **API app** (`api/`):
  - RESTful API at `/api/v1/` built with Django REST Framework
  - 11 endpoints: products, categories, stock-locations, stock-records, stock-movements, suppliers, purchase-orders, goods-received-notes, customers, sales-orders, dispatches
  - Token authentication and session authentication with staff-only permissions
  - Paginated responses (25 per page, configurable up to 100)
  - Search, filtering, and ordering on all list endpoints
  - Custom workflow actions: confirm/cancel orders, receive goods, process dispatch
  - Stock movement creation routed through `StockService` for atomic updates
  - Read-only stock records with `/low_stock/` endpoint
  - Immutable movements enforced (no update/delete)
  - Nested line item serializers on order endpoints
  - Full API test suite covering CRUD, auth, permissions, and workflow actions

- **Reports app** (`reports/`):
  - `InventoryReportService` — stock valuation (weighted average & latest cost), low-stock/overstock analysis, movement history with filtering
  - `OrderReportService` — purchase and sales order summaries grouped by day/week/month, with totals and status breakdowns
  - CSV export on all 6 report views via `?export=csv` query parameter
  - Stock Valuation view with selectable valuation method
  - Movement History view with filters (date range, movement type, location, category)
  - Low Stock and Overstock report views
  - Purchase Summary and Sales Summary views with period grouping and date range filtering
  - Wagtail admin Reports submenu with all report views
  - Full test suite: service tests and view integration tests

- **Procurement app** (`procurement/`):
  - `Supplier` model (Wagtail Snippet) with contacts, lead times, and payment terms
  - `PurchaseOrder` model with status workflow (draft → confirmed → received → cancelled)
  - `PurchaseOrderLine` model for order line items (product, quantity, unit cost)
  - `GoodsReceivedNote` model — auto-creates `receive` StockMovements on processing
  - `ProcurementService` with `confirm_order`, `cancel_order`, and `receive_goods` operations
  - Django admin for purchase orders (with inline lines) and goods received notes
  - Wagtail admin menu items for Suppliers, Purchase Orders, and Goods Received
  - Full test suite: model tests, service integration tests, and factories

- **Sales app** (`sales/`):
  - `Customer` model (Wagtail Snippet) with contact details
  - `SalesOrder` model with status workflow (draft → confirmed → fulfilled → cancelled)
  - `SalesOrderLine` model for order line items (product, quantity, unit price)
  - `Dispatch` model — auto-creates `issue` StockMovements on processing
  - `SalesService` with `confirm_order`, `cancel_order`, and `process_dispatch` operations
  - Django admin for sales orders (with inline lines) and dispatches
  - Wagtail admin menu items for Customers, Sales Orders, and Dispatches
  - Full test suite: model tests, service integration tests, and factories

## [0.1.0] - 2026-03-10

### Added

- Initial project scaffold with Wagtail 7.3 on Django 6.

[Unreleased]: https://github.com/Ndevu12/the_inventory/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Ndevu12/the_inventory/releases/tag/v0.1.0

