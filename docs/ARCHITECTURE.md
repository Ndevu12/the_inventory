# Architecture

This document describes the technical design of **The Inventory** — an open-source inventory management system built on [Wagtail CMS](https://wagtail.org/) and [Django](https://djangoproject.com/).

---

## High-Level Overview

```
┌─────────────────────────────────────────────────┐
│                   Browser / Client               │
└────────────────────────┬────────────────────────┘
                         │
          ┌──────────────┴──────────────┐
          │       Django / Wagtail       │
          │        (WSGI server)         │
          └──────────────┬──────────────┘
                         │
     ┌───────────┬───────┴───────┬───────────┐
     │           │               │           │
  Wagtail     Django          Search      Static /
   Admin      Admin          Backend      Media
     │           │               │        Storage
     └───────────┴───────┬───────┘
                         │
                    ┌────┴────┐
                    │   DB    │
                    │ SQLite  │
                    │  / PG   │
                    └─────────┘
```

Users interact with The Inventory primarily through the **Wagtail admin** interface. The standard Django admin is available at `/django-admin/` for low-level access when needed.

---

## Tech Stack

| Layer | Technology | Notes |
|---|---|---|
| Language | Python 3.12+ | |
| Web framework | Django 6.0 | |
| CMS / Admin UI | Wagtail 7.3 | Primary interface for all CRUD |
| Database | SQLite (dev) / PostgreSQL (prod) | Split settings pattern |
| Search | Wagtail search (database backend) | Elasticsearch planned for Phase 4 |
| Tagging | `django-taggit` | Bundled with Wagtail |
| Clustering | `django-modelcluster` | Bundled with Wagtail |
| Filtering | `django-filter` | List filtering in admin views |
| JWT Auth | `djangorestframework-simplejwt` | Stateless token auth for SPA/mobile |
| CORS | `django-cors-headers` | Cross-origin frontend support |
| API Docs | `drf-spectacular` | OpenAPI 3.0 schema, Swagger UI, Redoc |
| PDF Generation | `reportlab` | Styled PDF report export |
| Excel Parsing | `openpyxl` | CSV/Excel data import |
| Charts | Chart.js (CDN) | Dashboard visualizations |
| Containerization | Docker | Single-container for now |

### Frontend / UI Stack

The backend operates as a **headless API server** serving JSON data to a separate modern frontend, while retaining the Wagtail admin UI for staff.  Wagtail admin templates remain for internal CMS use.

| Layer | Technology | Role |
|---|---|---|
| Interactivity | [HTMX](https://htmx.org/) | Server-driven partial page updates, live search, inline editing |
| Client-side state | [Alpine.js](https://alpinejs.dev/) | Dropdowns, modals, toggles, small reactive state |
| Styling | [Tailwind CSS](https://tailwindcss.com/) | Utility-first CSS for custom views |
| Admin CRUD | Wagtail Snippets | Built-in model editing UI with permissions |

**Why this stack?**

- Inventory management is **CRUD-heavy and staff-facing** — naturally fits Django's request-response model.
- HTMX gives SPA-like responsiveness (partial updates, debounced search, form submissions) without a JavaScript framework.
- Alpine.js handles the small bits of client-side state (expand/collapse, confirm dialogs) that HTMX doesn't cover.
- Tailwind CSS provides a modern look for custom views without fighting Django's template system.
- No npm, no webpack, no Vite — HTMX and Alpine.js are loaded via `<script>` tags (CDN or vendored static files).

**How the two UIs coexist:**

| Surface | Stack | Examples |
|---|---|---|
| Wagtail admin (Snippets) | Wagtail's built-in UI (React internals, no customization needed) | Category CRUD, Product editing, Location tree |
| Custom inventory views | Django templates + HTMX + Alpine.js + Tailwind | Dashboard, stock movement forms, low-stock alerts, search |

**Dependencies added:**

```
django-htmx       # HTMX middleware & template helpers
```

> Alpine.js, HTMX, and Tailwind CSS are loaded as static assets — no Python packages needed for them.

---

## Design Conventions

The project uses **object-oriented programming (OOP) as its standard paradigm**. This applies across all layers:

| Layer | Convention | Example |
|---|---|---|
| **Models** | Django `Model` / `MP_Node` classes with declarative fields and validation | `Product`, `StockMovement` |
| **Services** | One `<Domain>Service` class per domain, public methods = operations | `StockService.process_movement()` |
| **Views** | Class-based views (Django CBVs / Wagtail view classes) preferred | `ListView`, `CreateView` |
| **Tests** | `TestCase` subclasses grouped by domain | `StockServiceTests` |

**Why OOP?**
- **Consistency** — contributors can predict how any module is structured.
- **Encapsulation** — related logic and helpers live together inside a class.
- **Extensibility** — classes can be subclassed, composed, or injected.
- **Testability** — classes are easy to mock, stub, and isolate.

> **Rule of thumb:** If you're adding a new module that contains business logic, wrap it in a class. Standalone utility functions are fine for truly stateless helpers (e.g. formatting, pure transformations), but domain operations should live on a service class.

---

## Project Structure

```
the_inventory/              ← Project root
│
├── manage.py               ← Django entry point (uses dev settings by default)
├── requirements.txt        ← Python dependencies
├── Dockerfile              ← Container build
├── db.sqlite3              ← Dev database (gitignored in production)
│
├── the_inventory/          ← Project configuration package
│   ├── settings/
│   │   ├── base.py         ← Shared / common settings
│   │   ├── dev.py          ← Development overrides (DEBUG=True, SQLite)
│   │   └── production.py   ← Production overrides (PostgreSQL, ManifestStaticFiles)
│   ├── urls.py             ← Root URL configuration
│   ├── wsgi.py             ← WSGI application
│   ├── templates/          ← Project-level templates (base.html, 404, 500)
│   └── static/             ← Project-level static assets (CSS, JS)
│
├── home/                   ← Home page app (landing page)
│   ├── models.py           ← HomePage (Wagtail Page model)
│   ├── templates/home/     ← Home page templates
│   └── migrations/
│
├── search/                 ← Site-wide search app
│   ├── views.py            ← Search view
│   └── templates/search/   ← Search results template
│
├── docs/                   ← Project documentation
│   ├── ARCHITECTURE.md     ← This file
│   └── ROADMAP.md          ← Development roadmap & phases
│
│   ── Apps ──
│
├── inventory/              ← [Phase 1] Core inventory models & logic
│   ├── models/             ← Models package (split by domain)
│   │   ├── __init__.py     ← Re-exports all models
│   │   ├── base.py         ← TimeStampedModel (abstract)
│   │   ├── category.py     ← Category (treebeard)
│   │   ├── product.py      ← Product, ProductImage, ProductTag
│   │   └── stock.py        ← StockLocation, StockRecord, StockMovement
│   ├── services/           ← Business-logic service layer
│   │   ├── __init__.py
│   │   └── stock.py        ← StockService class
│   ├── panels/             ← Wagtail admin dashboard panels
│   │   ├── __init__.py     ← Re-exports all panel components
│   │   ├── stock_summary.py ← StockSummaryPanel (metrics overview)
│   │   ├── low_stock.py    ← LowStockPanel (critical stock items)
│   │   └── recent_movements.py ← RecentMovementsPanel (latest activity)
│   ├── apps.py             ← InventoryConfig
│   ├── admin.py
│   ├── filters.py          ← ProductFilterSet, StockStatusFilter
│   ├── views.py
│   ├── tests/              ← Test suite (mirrors source layout)
│   │   ├── __init__.py
│   │   ├── factories.py    ← Shared test data factories
│   │   ├── test_filters.py ← FilterSet and custom filter tests
│   │   ├── test_views.py   ← Admin view tests (low-stock, search)
│   │   ├── test_models/    ← Unit tests for all models
│   │   │   ├── __init__.py
│   │   │   ├── test_category.py
│   │   │   ├── test_product.py
│   │   │   └── test_stock.py
│   │   ├── test_services/  ← Integration tests for service layer
│   │   │   ├── __init__.py
│   │   │   └── test_stock_service.py
│   │   └── test_panels/    ← Dashboard panel component tests
│   │       ├── __init__.py
│   │       ├── test_stock_summary.py
│   │       ├── test_low_stock.py
│   │       └── test_recent_movements.py
│   ├── wagtail_hooks.py    ← Wagtail admin customizations
│   ├── migrations/
│   └── templates/inventory/
│
├── tenants/               ← [Phase 5] Multi-tenancy & SaaS (built)
│   ├── models.py          ← Tenant, TenantMembership
│   ├── middleware.py       ← TenantMiddleware (resolves tenant per request)
│   ├── context.py          ← Thread-local tenant context
│   ├── managers.py         ← TenantAwareManager, TenantAwareQuerySet
│   ├── permissions.py      ← RBAC utilities + DRF permission classes
│   ├── context_processors.py ← Per-tenant branding for templates
│   ├── admin.py            ← Django admin for tenants & memberships
│   ├── wagtail_hooks.py    ← Wagtail admin menu item
│   ├── migrations/
│   └── tests/
│       ├── factories.py
│       ├── test_models.py
│       ├── test_middleware.py
│       ├── test_managers.py
│       ├── test_permissions.py
│       ├── test_context.py
│       └── test_tenant_aware_models.py
│
├── procurement/            ← [Phase 2] Suppliers & purchase orders (built)
├── sales/                  ← [Phase 2] Customers & sales orders (built)
├── reports/                ← [Phase 3] Reporting & analytics (built)
└── api/                    ← [Phase 4] REST API (built)
```

---

## Settings Pattern

The project uses a **split settings** layout under `the_inventory/settings/`:

- **`base.py`** — All shared configuration (installed apps, middleware, templates, Wagtail settings).
- **`dev.py`** — Inherits from `base`, sets `DEBUG = True`, uses SQLite, adds dev-only tools.
- **`production.py`** — Inherits from `base`, reads `SECRET_KEY` and database credentials from environment variables, enables `ManifestStaticFilesStorage`.

`manage.py` defaults to `the_inventory.settings.dev`. Production deployments set `DJANGO_SETTINGS_MODULE=the_inventory.settings.production`.

---

## App Designs

### `inventory/` — Phase 1 (Building Now)

The core app. All other apps will depend on models defined here.

Models use a **package layout** (`models/` directory with one file per domain) rather than a single `models.py`. This keeps each file focused and navigable as the model count grows. The `models/__init__.py` re-exports all models so Django migrations, admin, and imports work identically to a flat file.

#### Schema Design Decisions

These decisions were made upfront to avoid costly migrations later:

| Decision | Choice | Rationale |
|---|---|---|
| Audit + tenant fields | `TimeStampedModel` abstract base | `tenant`, `created_at`, `updated_at`, `created_by` on all models |
| Soft-delete | `is_active` boolean | Preserves FK integrity; deactivated items remain in history |
| Unit of measure | Choices on `Product` | Required for mixed inventory (countable + bulk goods) |
| Pricing | `unit_cost` on Product + StockMovement | Product holds latest cost; movement captures point-in-time cost for valuation |
| Category hierarchy | `treebeard.MP_Node` | Bundled with Wagtail — no extra dependency |
| Location hierarchy | `treebeard.MP_Node` | Warehouse → shelf → bin nesting without a separate type field |
| Multi-image | `ProductImage` orderable inline | Multiple images with ordering and captions per product |
| Movement types | receive / issue / transfer / adjustment | Adjustment added for stock corrections and write-offs |

#### Abstract Base Model

```python
class TimeStampedModel(models.Model):
    """Audit + tenant fields inherited by all domain models."""
    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name="%(app_label)s_%(class)s_set",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="%(class)s_created",
    )

    class Meta:
        abstract = True
```

> **Phase 5 note:** The `tenant` FK was added to `TimeStampedModel` so that every domain model in the system (`Category`, `Product`, `StockLocation`, `StockRecord`, `StockMovement`, `Supplier`, `PurchaseOrder`, `PurchaseOrderLine`, `GoodsReceivedNote`, `Customer`, `SalesOrder`, `SalesOrderLine`, `Dispatch`) is automatically scoped to a `Tenant`.  The field is nullable during migration; the `TenantMiddleware` and `TenantAwareManager` enforce scoping at runtime.

#### Models

| Model | Type | Key Fields | Purpose |
|---|---|---|---|
| `TimeStampedModel` | Abstract base | `tenant` (FK), `created_at`, `updated_at`, `created_by` | Tenant scoping + audit trail on all models |
| `Category` | Wagtail Snippet (`treebeard.MP_Node`) | `name`, `slug`, `description`, `is_active` | Hierarchical product categories |
| `Product` | Wagtail Snippet (`ClusterableModel`) | `sku` (unique), `name`, `description`, `category` (FK), `unit_of_measure`, `unit_cost`, `reorder_point`, `is_active` | Items in the catalog |
| `ProductImage` | `Orderable` inline on Product | `image` (FK → wagtailimages), `caption` | Multiple images per product |
| `ProductTag` | `TaggedItemBase` | `content_object` (ParentalKey → Product) | Free-form tags via `django-taggit` |
| `StockLocation` | Wagtail Snippet (`treebeard.MP_Node`) | `name`, `description`, `is_active` | Hierarchical physical locations |
| `StockRecord` | Django Model | `product` (FK), `location` (FK), `quantity` | Current stock per product per location |
| `StockMovement` | Django Model | `product` (FK), `from_location` (FK, nullable), `to_location` (FK, nullable), `quantity`, `unit_cost`, `movement_type`, `reference`, `notes` | Audit log of every stock change |

#### Field Details

**Product.unit_of_measure** — choices:

| Value | Label |
|---|---|
| `pcs` | Pieces |
| `kg` | Kilograms |
| `lt` | Liters |
| `m` | Meters |
| `box` | Boxes |
| `pack` | Packs |

**StockMovement.movement_type** — choices:

| Value | Label |
|---|---|
| `receive` | Receive |
| `issue` | Issue |
| `transfer` | Transfer |
| `adjustment` | Adjustment |

**StockMovement.reference** — An optional freeform `CharField` (e.g. `"PO-2026-001"`). Phase 2 apps (`procurement/`, `sales/`) will use this to link movements back to purchase orders or sales orders. This avoids adding a `GenericForeignKey` now while keeping the door open.

**StockRecord** constraints:
- `unique_together = ("product", "location")`
- Property: `is_low_stock` → `self.quantity <= self.product.reorder_point`

#### Key Relationships

```
TimeStampedModel (abstract)
    ├── Category
    ├── Product
    ├── StockLocation
    ├── StockRecord
    └── StockMovement

Category (treebeard tree)
    └── Product (FK → Category, SET_NULL, nullable)
            ├── ProductImage (ParentalKey → Product, orderable)
            ├── ProductTag (ParentalKey → Product, M2M via taggit)
            ├── StockRecord (FK → Product, CASCADE)
            └── StockMovement (FK → Product, PROTECT)

StockLocation (treebeard tree)
    ├── StockRecord (FK → StockLocation, CASCADE)
    └── StockMovement (FK from_location / to_location → StockLocation, PROTECT)
```

#### Stock Movement Types

| Type | From Location | To Location | Effect |
|---|---|---|---|
| **Receive** | — (null) | Target location | Increases stock at destination |
| **Issue** | Source location | — (null) | Decreases stock at source |
| **Transfer** | Location A | Location B | Decreases at A, increases at B |
| **Adjustment** | Location (optional) | Location (optional) | Corrects stock count (write-off, found stock, audit fix) |

Movement processing is transactional: quantity changes to `StockRecord` happen atomically inside `StockService.process_movement()`. The model's `save()` method only enforces immutability (no updates) and runs `full_clean()` — all business logic lives in the **service layer**.

##### Service Layer

Business logic is separated from model definitions into `inventory/services/`. The project adopts **object-oriented programming (OOP) as the standard paradigm** for service layers: each service is a class whose public methods represent domain operations.

```
inventory/services/
├── __init__.py
└── stock.py          ← StockService class
```

**Why OOP services?**
- **Consistency** — every service follows the same class-based pattern, making the codebase predictable for contributors.
- **Encapsulation** — related operations and their private helpers are grouped inside a single class.
- **Extensibility** — services can be subclassed or composed; shared state (e.g. the requesting user) can be passed via `__init__`.
- **Testability** — classes are straightforward to mock, stub, or inject in tests.
- **Separation of concerns** — models stay purely declarative (fields, validation, `__str__`); views, management commands, and API endpoints all call the same service class.

> **Convention:** When adding a new service, create a class named `<Domain>Service` (e.g. `ProcurementService`, `ReportService`) in its own file under `services/`. Keep the class stateless by default — accept request-scoped context via `__init__` only when needed.

**Usage:**
```python
from inventory.services.stock import StockService

service = StockService()
movement = service.process_movement(
    product=widget,
    movement_type="receive",
    quantity=100,
    to_location=warehouse,
    unit_cost=Decimal("9.99"),
    created_by=request.user,
)
```

Validation rules:

- **Receive** must have `to_location`; `from_location` must be null
- **Issue** must have `from_location`; `to_location` must be null; cannot issue more than available
- **Transfer** must have both locations; cannot transfer more than available at source
- **Adjustment** must have at least one location

#### Low-Stock Alerts

Each `Product` defines a `reorder_point` (default: 0). A stock record is **low** when `StockRecord.quantity <= Product.reorder_point`. Low-stock items surface via:

- A filtered view in the Wagtail admin (using `django-filter`)
- A Wagtail admin dashboard widget
- Future: webhook/email notifications (Phase 4)

#### Future-Proofing Notes

These notes explain how the Phase 1 schema accommodates future phases without requiring breaking migrations:

- **Supplier link (Phase 2):** `procurement/` will add a `Supplier` model and either a FK on `Product` or a `SupplierProduct` junction table. The Phase 1 `Product` model does not need a supplier field yet.
- **Order references (Phase 2):** `StockMovement.reference` stores PO/SO numbers as free text. Phase 2 apps may add a dedicated FK alongside this field for structured lookups.
- **Stock valuation (Phase 3):** `StockMovement.unit_cost` captures point-in-time cost. Combined with movement history, this supports FIFO, LIFO, or weighted-average valuation without schema changes.
- **API (Phase 4):** All models have clean `__str__` methods and simple FKs — straightforward to serialize with Django REST Framework.

---

> **Note:** All apps below (procurement, sales, reports, API, tenants) are now built.

---

### `procurement/` — Phase 2 (Built)

| Model | Type | Purpose |
|---|---|---|
| `Supplier` | Wagtail Snippet | Vendor / supplier details (code, contacts, lead times, payment terms, soft-delete) |
| `PurchaseOrder` | Django Model | Order placed with a supplier (status workflow: draft → confirmed → received / cancelled) |
| `PurchaseOrderLine` | Django Model | Line items (FK → Product, quantity, unit cost; unique per PO + product) |
| `GoodsReceivedNote` | Django Model | Confirmation of goods arrival — triggers `receive` StockMovements via `ProcurementService` |

**Service:** `ProcurementService` — `confirm_order()`, `cancel_order()`, `receive_goods()`.  GRN processing creates atomic receive movements for each PO line and transitions the PO to received status.

---

### `sales/` — Phase 2 (Built)

| Model | Type | Purpose |
|---|---|---|
| `Customer` | Wagtail Snippet | Customer / client details (code, contacts, soft-delete) |
| `SalesOrder` | Django Model | Order from a customer (status workflow: draft → confirmed → fulfilled / cancelled) |
| `SalesOrderLine` | Django Model | Line items (FK → Product, quantity, unit price; unique per SO + product) |
| `Dispatch` | Django Model | Shipment record — triggers `issue` StockMovements via `SalesService` |

**Service:** `SalesService` — `confirm_order()`, `cancel_order()`, `process_dispatch()`.  Dispatch processing creates atomic issue movements for each SO line and transitions the SO to fulfilled status.

---

### `reports/` — Phase 3 (Built)

No persistent models — read-only views and exports querying data from `inventory`, `procurement`, and `sales`.

**Services:**

| Service | Methods |
|---|---|
| `InventoryReportService` | `get_stock_valuation()`, `get_valuation_summary()`, `get_low_stock_products()`, `get_overstock_products()`, `get_movement_history()`, `get_movement_summary()` |
| `OrderReportService` | `get_purchase_summary()`, `get_purchase_totals()`, `get_sales_summary()`, `get_sales_totals()` |

**Views (all at `/admin/reports/…`):**

| View | Features |
|---|---|
| Stock Valuation | Weighted average or latest cost method, CSV + PDF export |
| Movement History | Filterable by date, type, product, location; paginated; CSV + PDF export |
| Low Stock Report | Products at/below reorder point; CSV + PDF export |
| Overstock Report | Configurable threshold multiplier; CSV + PDF export |
| Purchase Summary | Period grouping (daily/weekly/monthly), date range, totals; CSV + PDF export |
| Sales Summary | Period grouping (daily/weekly/monthly), date range, totals; CSV + PDF export |

**Export:** All views support `?export=csv` and `?export=pdf` via the `ExportMixin` (which combines CSV and PDF export). PDF generation uses ReportLab with styled table layouts.

**Dashboard Charts (Wagtail admin homepage):**

| Panel | Chart Type | Data |
|---|---|---|
| Stock by Location | Horizontal bar (Chart.js) | Total quantity per active location |
| Movement Trends | Line chart (Chart.js) | Movement count per day, last 30 days |
| Order Status | Doughnut charts (Chart.js) | Purchase and sales order counts by status |

**Data Import:**

The `inventory/imports/` module provides CSV and Excel (.xlsx) import for Products, Suppliers, and Customers via a Wagtail admin view at `/admin/inventory/import/`.  Imports are validated row-by-row with all-or-nothing transactions — if any row fails, no records are created.

---

### `api/` — Phase 4 (Built) — Headless API Server

Built with **Django REST Framework** at `/api/v1/`.  Serves as the headless backend for modern frontend applications.

**Authentication:**

| Method | Header | Purpose |
|---|---|---|
| JWT (primary) | `Authorization: Bearer <access_token>` | Stateless auth for SPA/mobile frontends |
| Token | `Authorization: Token <key>` | Backwards-compatible service-to-service auth |
| Session | Cookie | Browsable API and Wagtail admin |

JWT tokens are obtained via `/api/v1/auth/login/` and refreshed via `/api/v1/auth/refresh/`.  A `JWTAuthMiddleware` pre-authenticates requests before `TenantMiddleware` for automatic tenant resolution.

**CORS:** `django-cors-headers` allows cross-origin requests from configured frontend origins.

**API Documentation:** OpenAPI 3.0 schema at `/api/v1/schema/`, Swagger UI at `/api/v1/docs/`, Redoc at `/api/v1/redoc/` — powered by `drf-spectacular`.

**CRUD Endpoints (11 ViewSets):**

| Endpoint | ViewSet | Key Features |
|---|---|---|
| `/api/v1/products/` | `ProductViewSet` | CRUD, search, filter by category/active, `/stock/` and `/movements/` sub-endpoints |
| `/api/v1/categories/` | `CategoryViewSet` | CRUD, search |
| `/api/v1/stock-locations/` | `StockLocationViewSet` | CRUD, `/stock/` sub-endpoint |
| `/api/v1/stock-records/` | `StockRecordViewSet` | Read-only, filter by product/location, `/low_stock/` |
| `/api/v1/stock-movements/` | `StockMovementViewSet` | List/retrieve/create only (immutable), create routes through `StockService` |
| `/api/v1/suppliers/` | `SupplierViewSet` | CRUD, search, filter by active/payment terms |
| `/api/v1/purchase-orders/` | `PurchaseOrderViewSet` | CRUD with nested lines, `/confirm/` and `/cancel/` actions |
| `/api/v1/goods-received-notes/` | `GoodsReceivedNoteViewSet` | CRUD, `/receive/` action (creates stock movements) |
| `/api/v1/customers/` | `CustomerViewSet` | CRUD, search, filter by active |
| `/api/v1/sales-orders/` | `SalesOrderViewSet` | CRUD with nested lines, `/confirm/` and `/cancel/` actions |
| `/api/v1/dispatches/` | `DispatchViewSet` | CRUD, `/process/` action (creates stock movements) |

**Auth Endpoints:**

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/auth/login/` | POST | Obtain JWT access + refresh tokens (includes user and tenant info) |
| `/api/v1/auth/refresh/` | POST | Refresh an expired access token |
| `/api/v1/auth/me/` | GET/PATCH | Current user profile with tenant context and memberships |
| `/api/v1/auth/change-password/` | POST | Change password (requires old password) |

**Reports Endpoints:**

| Endpoint | Query Params | Service |
|---|---|---|
| `/api/v1/reports/stock-valuation/` | `?method`, `?export` | `InventoryReportService` |
| `/api/v1/reports/movement-history/` | `?date_from`, `?date_to`, `?type`, `?export` | `InventoryReportService` |
| `/api/v1/reports/low-stock/` | `?export` | `InventoryReportService` |
| `/api/v1/reports/overstock/` | `?threshold`, `?export` | `InventoryReportService` |
| `/api/v1/reports/purchase-summary/` | `?period`, `?date_from`, `?date_to`, `?export` | `OrderReportService` |
| `/api/v1/reports/sales-summary/` | `?period`, `?date_from`, `?date_to`, `?export` | `OrderReportService` |

**Dashboard Endpoints:**

| Endpoint | Response |
|---|---|
| `/api/v1/dashboard/summary/` | KPI counts (products, locations, low stock, orders) |
| `/api/v1/dashboard/stock-by-location/` | `{labels, data}` for bar charts |
| `/api/v1/dashboard/movement-trends/` | `{labels, data}` for line charts (30 days) |
| `/api/v1/dashboard/order-status/` | `{purchase_orders, sales_orders}` for doughnut charts |

**Tenant Endpoints:**

| Endpoint | Method | Permission |
|---|---|---|
| `/api/v1/tenants/current/` | GET/PATCH | Member (read) / Admin (write) |
| `/api/v1/tenants/members/` | GET | Member |
| `/api/v1/tenants/members/<id>/` | PATCH/DELETE | Admin/Owner |

**Import Endpoint:** POST `/api/v1/import/` — multipart file upload for CSV/Excel bulk imports.

**Pagination:** `StandardPagination` — 25 items per page, configurable via `?page_size=N` (max 100).

---

### `tenants/` — Phase 5 (Built)

Multi-tenancy infrastructure enabling multiple organizations to share a single deployment with isolated data.

**Models:**

| Model | Type | Purpose |
|---|---|---|
| `Tenant` | Django Model (indexed) | Organization root — name, slug, active flag, branding (site name, colour, logo), subscription metadata (plan, status, limits) |
| `TenantMembership` | Django Model | Links a user to a tenant with a role (owner / admin / manager / viewer). `unique_together = ("tenant", "user")` |

**Middleware:** `TenantMiddleware` runs after `AuthenticationMiddleware`.  It resolves the current tenant and stores it in `request.tenant` and thread-local context.  Resolution order: `X-Tenant` header → `?tenant=` query param → default membership → first active membership → `None`.

**Manager:** `TenantAwareManager` overrides `get_queryset()` to auto-filter by the current tenant.  Returns unfiltered results when no tenant is set (safe for management commands and migrations).  `unscoped()` bypasses filtering for cross-tenant operations.

**RBAC Roles:**

| Role | `can_manage` | `can_admin` | `is_owner` |
|---|---|---|---|
| Owner | Yes | Yes | Yes |
| Admin | Yes | Yes | No |
| Manager | Yes | No | No |
| Viewer | No | No | No |

**DRF Permission Classes:** `IsTenantMember`, `IsTenantManager`, `IsTenantAdmin`, `IsTenantOwner`, `TenantReadOnlyOrManager`.

**Branding:** `tenant_branding` context processor injects `tenant_site_name`, `tenant_primary_color`, and `tenant_logo` into templates.

**Subscription Hooks:** `Tenant.subscription_plan` (free/starter/professional/enterprise), `subscription_status` (active/trial/past_due/cancelled/suspended), `max_users`, `max_products`.  Helper methods `is_within_user_limit()` and `is_within_product_limit()` enforce plan limits.

### Seeding with Multi-Tenancy

The seeder system (in `inventory/seeders/`) automatically handles tenant context during data initialization:

**Tenant-Scoped Seeding:**
- Each seeder accepts a `tenant` parameter: `seeder.execute(tenant=tenant_instance)`
- All created objects (Category, Product, StockLocation, etc.) are automatically linked to the tenant
- Thread-local tenant context is set via `set_current_tenant(tenant)` during seeding
- Supports multi-tenant data initialization: seed the same data independently for each tenant

**Seeder Architecture:**

The seeding pipeline consists of:

| Seeder | Purpose | Tenant-Aware |
|---|---|---|
| `TenantSeeder` | Creates or retrieves the "Default" tenant | Yes |
| `CategorySeeder` | Creates product categories (hierarchical) | Yes |
| `ProductSeeder` | Creates products across categories | Yes |
| `StockLocationSeeder` | Creates warehouse structure (hierarchical) | Yes |
| `StockRecordSeeder` | Creates stock-location associations | Yes |
| `StockMovementSeeder` | Creates movement history (receive, issue, transfer, adjustment) | Yes |
| `LowStockSeeder` | Creates low-stock scenarios for testing alerts | Yes |

All seeders inherit from `BaseSeeder` and receive the tenant instance via `execute(tenant=tenant)`. The `SeederManager` orchestrates execution in dependency order, ensuring all data is properly scoped.

**CLI Usage:**
```bash
# Seed for Default tenant (auto-creates if missing)
python manage.py seed_database --clear --create-default

# Seed for a specific tenant
python manage.py seed_database --clear --tenant=acme-corp

# Seed specific models only
python manage.py seed_database --models categories,products --tenant=acme-corp

# Create multiple tenants, then seed each independently
python manage.py createtenant --name="Tenant A" --slug="tenant-a"
python manage.py seed_database --clear --tenant=tenant-a
```

**Data Isolation:**
- Each tenant has independent copies of all inventory data (categories, products, locations, stock records, movements)
- Queries are automatically scoped to current tenant via `TenantAwareManager`
- No orphaned data: all seeded objects have `tenant` assigned
- Tenant field is non-nullable after migration TS-06, enforcing data integrity

**Programmatic Usage:**
```python
from inventory.seeders import SeederManager
from tenants.models import Tenant
from tenants.context import set_current_tenant, clear_current_tenant

# Get or create a tenant
tenant, _ = Tenant.objects.get_or_create(
    slug="acme-corp",
    defaults={"name": "ACME Corp", "is_active": True}
)

# Set tenant context (required for audit logging)
set_current_tenant(tenant)

try:
    # Seed all data for this tenant
    manager = SeederManager(verbose=True, clear_data=True)
    manager.seed(tenant=tenant)
finally:
    # Always clear context after seeding
    clear_current_tenant()
```

**Troubleshooting:**
- **"Default tenant does not exist"** → Use `--create-default` flag or specify `--tenant=<slug>`
- **"Tenant with slug 'xyz' not found"** → Create the tenant first with `python manage.py createtenant --name="..." --slug="xyz"`
- **Orphaned data (NULL tenant values)** → Run migration TS-06 to backfill and enforce non-nullable tenant field

For complete seeding documentation, see [inventory/seeders/README.md](../inventory/seeders/README.md).

For Tenant model details, see [tenants/models.py](../tenants/models.py).

---

## URL Routing

| Path | Handler | Purpose |
|---|---|---|
| `/admin/` | `wagtail.admin.urls` | Wagtail admin (primary UI) |
| `/django-admin/` | `django.contrib.admin` | Django admin (low-level) |
| `/documents/` | `wagtail.documents.urls` | Document library |
| `/search/` | `search.views.search` | Site-wide search |
| `/` (catch-all) | `wagtail.urls` | Wagtail page serving |

| `/api/v1/` | DRF `DefaultRouter` | REST API (Phase 4) |

---

## Database

- **Development:** SQLite (`db.sqlite3` at project root). Zero configuration needed.
- **Production:** PostgreSQL, configured via environment variables (`DATABASE_URL` or individual `DB_*` vars).

Django migrations manage all schema changes. Each app maintains its own `migrations/` directory.

---

## Search

Wagtail's built-in search framework indexes model fields marked with `search.SearchField` and `search.FilterField`. The **database backend** is used by default, which requires no external services.

For production deployments needing advanced full-text search, an **Elasticsearch backend** can be swapped in via settings (planned for Phase 4).

---

## Deployment

### Docker

A `Dockerfile` is provided for containerized deployments. The image:

1. Installs Python dependencies from `requirements.txt`
2. Collects static files
3. Runs migrations
4. Starts the WSGI server

### Environment Variables (Production)

| Variable | Purpose |
|---|---|
| `DJANGO_SETTINGS_MODULE` | `the_inventory.settings.production` |
| `SECRET_KEY` | Django secret key |
| `DATABASE_URL` | PostgreSQL connection string |
| `ALLOWED_HOSTS` | Comma-separated allowed hostnames |

---

## Contributing

See the [Contributing Guide](../CONTRIBUTING.md) for development workflow, coding standards, and PR guidelines.
