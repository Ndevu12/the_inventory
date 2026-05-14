# Architecture

This document describes the technical design of **The Inventory** — an open-source inventory management system built on [Wagtail CMS](https://wagtail.org/) and [Django](https://djangoproject.com/).

---

## High-Level Overview

```
┌──────────────────────────────────────────────────────────────┐
│                     Browser / clients                         │
└─────────────┬───────────────────────────────┬────────────────┘
              │                               │
   ┌──────────▼──────────┐         ┌──────────▼──────────┐
   │  Next.js frontend   │         │  Wagtail / Django   │
   │  (tenant inventory) │  JSON   │  admin (platform)   │
   └──────────┬──────────┘  REST   └──────────┬──────────┘
              │          ┌─────────────────────┘
              └──────────┤  Django / Wagtail (WSGI)
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

**Who uses which surface**

| Audience | Primary UI | Protocol |
| -------- | ---------- | -------- |
| **Tenant companies** (inventory operators) | [frontend/](../frontend/) (Next.js) | **DRF** at `/api/v1/` (JWT and related auth) |
| **Platform / internal staff** | **Wagtail admin** at `/admin/` | Session, reports, tenant management, imports; **optional** registered snippets for inventory entities when you want monitoring or support tooling in admin |

**Current default:** inventory listing menus are not in Wagtail ([inventory/wagtail_hooks.py](../inventory/wagtail_hooks.py)). **Evolving the architecture** to register Product, Category, or related models as **tenant-scoped** snippets (see [tenants/snippets.py](../tenants/snippets.py)) is fine for **staff monitoring, audits, or translation workflows**—as long as **tenant companies** still treat the **Next.js app + `/api/v1/`** as their **primary** place for day-to-day inventory operations. Domain models use Wagtail-friendly patterns (`panels`, `ClusterableModel`, images) because the stack is Wagtail-based; that does not imply admin is the main operator UI.

The standard Django admin remains at `/django-admin/` for low-level access when needed.

---

## Tenant plane vs platform plane (RBAC)

The product separates **who can use the tenant inventory app** from **who can operate the platform**. Do not rely on Django `is_superuser` or `is_staff` to bypass tenant scoping on tenant inventory REST routes: effective tenant and an **active** [`TenantMembership`](../tenants/models.py) are required.

| Plane | Audience | Primary UI | Auth | Tenant inventory API (`/api/v1/*` excluding platform routers) |
| ----- | -------- | ---------- | ---- | ----- |
| **Tenant** | Organization members (operators, managers, owners) | Next.js dashboard under `frontend/` | JWT from `/api/v1/auth/login/` and `/api/v1/auth/refresh/` | Must resolve a tenant and pass membership-aware permissions. Superuser **without** membership does **not** get tenant data via these endpoints. |
| **Platform** | Internal staff, break-glass support | **Wagtail** at `/admin/` (session cookie) | Wagtail / Django session | Cross-tenant work happens here, not through the tenant SPA. Optional `/api/v1/platform/` may exist for automation; it is **not** a substitute for membership on tenant routes. |

**JWT login rules**

- Issuing and refreshing access tokens requires **at least one active** `TenantMembership`. If a user is valid for Wagtail but has no active organization membership, login responds with **403** and a stable payload including `code: "no_tenant_membership"` and guidance that platform operators should use Wagtail.
- Refresh re-checks membership so sessions cannot be extended after the last membership is revoked.
- **User payload:** read-only `is_superuser` (and optionally `is_staff`) on login and `/api/v1/auth/me/` lets the Next.js app gate platform-only UI without probing 403 on every visit. Contract details: [API_SHARED_CONTRACT.md](API_SHARED_CONTRACT.md). Tenant REST routes still require membership; platform flags are **not** tenant capabilities.

- **Dual-console accounts:** If a person is deliberately given both Wagtail access (`is_staff` / `is_superuser`) **and** an active `TenantMembership`, they obtain tenant JWTs and use the SPA like any other member. The inventory app does **not** block the SPA solely because those Django flags are set; lack of membership is what keeps typical platform operators out of the tenant app.

**API impersonation (support, WS07)**

Platform break-glass on **tenant** inventory APIs must use a **member** identity, not raw superuser on tenant ViewSets:

| Endpoint | Who | Purpose |
| -------- | --- | ------- |
| `POST /api/v1/auth/impersonate/start/` | `IsAuthenticated` + **Django superuser** (`IsPlatformSuperuser`) | Returns JWT + profile + `memberships` for a **target user that has ≥ 1 active `TenantMembership`**. Each start is written to the compliance audit log. |
| `POST /api/v1/auth/impersonate/end/` | Bearer token from an impersonation JWT (carries `impersonated_by`) | Records end-of-session in the audit log; client restores the operator’s stored tokens locally. |

`ENABLE_API_IMPERSONATION` in settings (default **True**) can disable the **token-swap** routes while **Wagtail session impersonation** (`/admin/impersonate/...`) remains available for staff workflows.

**Next.js dashboard**

- Only users with **≥ 1** active membership are expected to use the SPA for inventory work. `AuthGuard` redirects when `memberships` is empty after bootstrap; it does **not** exclude users only because `is_staff` or `is_superuser` is true on the server. A dedicated **no-organization** route handles the edge case where a client still has credentials but no membership (defense in depth alongside the login gate).
- Platform-only pages in the SPA (cross-tenant settings, platform audit, etc.) are removed or reduced: platform work belongs in Wagtail.

**When `is_staff` and `is_superuser` still matter**

| Flag | Typical use in this project |
| ---- | --------------------------- |
| `is_superuser` | Full Django/Wagtail access; platform break-glass. Does **not** grant tenant REST “god mode” when RBAC gates are enforced. |
| `is_staff` | Can access Wagtail admin (and related staff workflows). **Platform-provisioned** users (e.g. created via platform APIs for staff) may remain `is_staff=True`. **Tenant-only** signups (register tenant, accept invitation as a new user) should be created with `is_staff=False` so routine tenant operators are not conflated with platform staff. |
| Neither | Normal tenant-only accounts; access only via JWT + membership. |

**Migrating existing deployments**

- After tightening login and permissions, ensure every person who should use the Next.js app has an **active** `TenantMembership`. Users who only need Wagtail need accounts with appropriate `is_staff` / `is_superuser`, not necessarily a tenant membership.
- Historical data may have tenant owners with `is_staff=True` from older provisioning. You may normalize those rows to `is_staff=False` when they are not platform operators (optional data migration or one-off script); Wagtail access remains governed by staff flags independent of tenant roles.
- API clients and scripts that assumed “superuser sees all tenants over `/api/v1/`” must move cross-tenant operations to **Wagtail**, **platform** endpoints where explicitly supported, or dedicated service patterns — not generic tenant CRUD.

**Vocabulary: tenant identifiers vs platform terminology**

In code, APIs, and docs, keep **“admin”** language clearly **platform-oriented** (Wagtail, Django staff, superuser). Tenant-scoped names should encode **tenant + capability** (e.g. manage memberships, governance, audit) so they are not confused with platform admin.

The second-tier tenant governance role is stored as **`coordinator`** (`TenantRole.COORDINATOR`); older databases are migrated from the legacy value `admin`. Tenant-scoped identifiers avoid the substring **admin** except when referring to **platform** (Wagtail, Django staff, superuser).

| Concept | Implementation |
| --- | --- |
| Governance role (owner + second tier) | `TenantRole.OWNER`, `TenantRole.COORDINATOR`; `_TENANT_GOVERNANCE_ROLES` in `api/permissions.py` |
| Membership / permission helpers | `TenantMembership.can_manage_organization`; `can_manage_organization()` in `tenants/permissions.py` |
| DRF: organization governance | `IsTenantGovernanceMember` |
| DRF: compliance audit log (JWT) | `IsTenantMemberAuthorizedForAuditLog` |

User-visible copy uses labels such as “Coordinator” (i18n under `SettingsTenant.roles.coordinator`).

See also: [TEST_USERS.md](../TEST_USERS.md) for seeded accounts and which plane they exercise.

---

## Tech Stack

| Layer | Technology | Notes |
|---|---|---|
| Language | Python 3.12+ | |
| Web framework | Django 6.0 | |
| CMS / Admin UI | Wagtail 7.3 | Platform/staff UI; tenant inventory CRUD via API + Next.js |
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

The backend is a **headless API** for **tenant** applications: the **[frontend/](../frontend/)** Next.js app calls **DRF** at `/api/v1/`. **Wagtail admin** serves **platform** workflows (tenants, reports under `/admin/`, imports, dashboards)—not the main path for tenant inventory operators.

| Layer | Technology | Role |
|---|---|---|
| Tenant app | **Next.js** (App Router) | Primary inventory UX for companies; consumes REST API |
| API | **Django REST Framework** | CRUD, auth, OpenAPI (`drf-spectacular`) |
| Platform admin | **Wagtail 7** | Staff UI, reports; inventory snippets **if registered** (monitoring/support—not primary for tenant operators) |
| Legacy / optional templates | Django templates, **HTMX**, **Alpine.js**, **Tailwind** | Some reports, imports, or custom views under Wagtail—not the tenant Next.js app |

**Internationalization:** The stack uses **more than next-intl**. **Static tenant UI copy** (nav, forms, errors in the SPA) uses **next-intl** and JSON under `frontend/public/locales/` (loaded at runtime; many trees are produced from `frontend/scripts/` via `yarn locale:merge`—see [I18N_FRONTEND.md](I18N_FRONTEND.md)). **Catalog and domain content** (product name, descriptions, etc.) uses **Wagtail i18n + [wagtail-localize](https://www.wagtail-localize.org/)** (`TranslatableMixin`) with **linked rows per locale** in the database—not those JSON files. The **REST API** exposes the correct language variant via `GET ?language=` and write rules below. Tenant **reads** use `GET ?language=` (then tenant default, then `Accept-Language`) to overlay translated strings while list endpoints keep **canonical locale ids**. **Writes** (`POST`/`PATCH`/`PUT`) use `?language=` when set; otherwise the tenant **canonical** locale (`Accept-Language` is not used on writes). **POST** in a non-canonical locale requires body field **`translation_of`**: the primary key of the **canonical** row (the id from default list responses). **PATCH** with `?language=` updates that locale’s row (creating the linked translation when missing). Wagtail admin remains available for staff where snippets are registered. Task breakdown: [TASKS.MD](TASKS.MD) (I18N-*). **Next.js catalogs (scripts, merge, runtime):** [I18N_FRONTEND.md](I18N_FRONTEND.md). **Stack boundaries and limitations:** [I18N_LIMITATIONS.md](I18N_LIMITATIONS.md).

**Why this split?**

- **Multi-tenant SaaS:** companies use a dedicated SPA experience while the same Django project powers APIs, permissions, and Wagtail for operators.
- **Wagtail** remains valuable for media, search fields, tree models, and staff tooling without forcing tenants through `/admin/` for day-to-day stock work.

**Dependencies (representative):**

- `django-cors-headers`, `djangorestframework-simplejwt` — SPA auth and CORS
- `django-htmx` — where HTMX-backed Wagtail or Django views exist

> The Next.js app lives under `frontend/` with its own `package.json`; Python packages do not install React.

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

## Facility vs stock location (contributor governance)

Operators distinguish **what** they hold (**inventory / stock** quantities) from **where** it sits. In this codebase that split is modeled, not only worded in the UI:

- **`Warehouse`** — Tenant-scoped **facility or site** (e.g. distribution center, named building) when the business needs that level of identity (address, timezone, site-level reporting, inter-facility logic).
- **`StockLocation`** — **Granular place** (aisle, bin, zone, “stockroom”). It may link to a warehouse via an optional `warehouse` FK. When `warehouse` is **null**, the tenant is in **location-only / retail-style** mode: stock is “at location L,” not “at warehouse W → L.” **Do not invent a fake `Warehouse` row** to satisfy copy or dashboards in that mode; use neutral labels (e.g. store / tenant name) instead.

**Full-stack rule:** Treating this as a **locale-only rename**, **dashboard-only label**, or **Next.js-only** workaround is **not sufficient**. New or changed behavior should respect the same semantics across **models and migrations**, **domain services** (stock, reservations, cycles, transfers), **API serializers and filters**, **reports and tasks**, **seeders**, **tests**, and **frontend types** that mirror the API.

**Tree scope:** `StockLocation` trees (**treebeard**) are partitioned by **`(tenant, warehouse_id)`**, including **`warehouse_id IS NULL`** as its own forest, so retail location hierarchies do not collide with paths per facility.

For day-to-day stack conventions, see [Contributing](../CONTRIBUTING.md).

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
├── frontend/               ← Next.js tenant app (calls `/api/v1/`)
│   └── package.json        ← Node dependencies (separate from requirements.txt)
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
│   ├── wagtail_hooks.py    ← Inventory removed from Wagtail menus; API is tenant path
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
| `Category` | Django model (`treebeard.MP_Node`; Wagtail `panels`) | `name`, `slug`, `description`, `is_active` | Hierarchical product categories; **primary CRUD via DRF** for tenant operators |
| `Product` | Django model (`ClusterableModel`; Wagtail `panels`) | `sku` (unique), `name`, `description`, `category` (FK), `unit_of_measure`, `unit_cost`, `reorder_point`, `is_active` | Catalog items; **primary CRUD via DRF** for tenant operators |
| `ProductImage` | `Orderable` inline on Product | `image` (FK → wagtailimages), `caption` | Multiple images per product |
| `ProductTag` | `TaggedItemBase` | `content_object` (ParentalKey → Product) | Free-form tags via `django-taggit` |
| `StockLocation` | Django model (`treebeard.MP_Node`; Wagtail `panels`) | `name`, `description`, `is_active` | Hierarchical physical locations; **primary CRUD via DRF** for tenant operators |
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

- **API** and Next.js client (e.g. availability / reporting endpoints)
- Wagtail admin dashboard widgets (staff)
- Future: webhook/email notifications (Phase 4)

#### Future-Proofing Notes

These notes explain how the Phase 1 schema accommodates future phases without requiring breaking migrations:

- **Supplier link (Phase 2):** `procurement/` will add a `Supplier` model and either a FK on `Product` or a `SupplierProduct` junction table. The Phase 1 `Product` model does not need a supplier field yet.
- **Order references (Phase 2):** `StockMovement.reference` stores PO/SO numbers as free text. Phase 2 apps may add a dedicated FK alongside this field for structured lookups.
- **Stock valuation (Phase 3):** `StockMovement.unit_cost` captures point-in-time cost. Combined with movement history, this supports FIFO, LIFO, or weighted-average valuation without schema changes.
- **API (Phase 4, current):** DRF viewsets under `/api/v1/` are the **primary** CRUD path for tenant inventory; models use clean FKs and serializers.

---

> **Note:** All apps below (procurement, sales, reports, API, tenants) are now built.

---

### `procurement/` — Phase 2 (Built)

| Model | Type | Purpose |
|---|---|---|
| `Supplier` | Django model (Wagtail `panels`; snippet registration optional for staff) | Vendor / supplier details; **primary CRUD via DRF** for tenant operators |
| `PurchaseOrder` | Django Model | Order placed with a supplier (status workflow: draft → confirmed → received / cancelled) |
| `PurchaseOrderLine` | Django Model | Line items (FK → Product, quantity, unit cost; unique per PO + product) |
| `GoodsReceivedNote` | Django Model | Confirmation of goods arrival — triggers `receive` StockMovements via `ProcurementService` |

**Service:** `ProcurementService` — `confirm_order()`, `cancel_order()`, `receive_goods()`.  GRN processing creates atomic receive movements for each PO line and transitions the PO to received status.

---

### `sales/` — Phase 2 (Built)

| Model | Type | Purpose |
|---|---|---|
| `Customer` | Django model (Wagtail `panels`) | Customer / client details; **primary CRUD via DRF** for tenant operators |
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

**Shared REST contract (user flags, audit list `summary` / `event_scope`, tenant audit filtering):** [API_SHARED_CONTRACT.md](API_SHARED_CONTRACT.md).

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
| `/api/v1/tenants/current/` | GET/PATCH | Member (read) / governance role — owner or tenant admin role — (write) |
| `/api/v1/tenants/members/` | GET | Member |
| `/api/v1/tenants/members/<id>/` | PATCH/DELETE | Owner or tenant admin role |

**Import Endpoint:** POST `/api/v1/import/` — multipart file upload for CSV/Excel bulk imports.

**Pagination:** `StandardPagination` — 25 items per page, configurable via `?page_size=N` (max 100).

---

### `tenants/` — Phase 5 (Built)

Multi-tenancy infrastructure enabling multiple organizations to share a single deployment with isolated data.

**Models:**

| Model | Type | Purpose |
|---|---|---|
| `Tenant` | Django Model (indexed) | Organization root — name, slug, active flag, branding (site name, colour, logo), subscription metadata (plan, status, limits) |
| `TenantMembership` | Django Model | Links a user to a tenant with a role (owner / coordinator / manager / viewer). `unique_together = ("tenant", "user")` |

**Middleware:** `TenantMiddleware` runs after `AuthenticationMiddleware`.  It resolves the current tenant and stores it in `request.tenant` and thread-local context.  Resolution order: `X-Tenant` header → `?tenant=` query param → default membership → first active membership → `None`.

**Manager:** `TenantAwareManager` overrides `get_queryset()` to auto-filter by the current tenant.  Returns unfiltered results when no tenant is set (safe for management commands and migrations).  `unscoped()` bypasses filtering for cross-tenant operations.

**RBAC Roles** (tenant scope; see [Tenant plane vs platform plane](#tenant-plane-vs-platform-plane-rbac)):

| Role | `can_manage` | `can_manage_organization` | `is_owner` |
|---|---|---|---|
| Owner | Yes | Yes | Yes |
| Coordinator (tenant governance) | Yes | Yes | No |
| Manager | Yes | No | No |
| Viewer | No | No | No |

**DRF Permission Classes:** `IsTenantMember`, `IsTenantManager`, `IsTenantGovernanceMember`, `IsTenantOwner`, `TenantReadOnlyOrManager`, plus `IsTenantMemberAuthorizedForAuditLog` for tenant compliance audit routes.

**Branding:** `tenant_branding` context processor injects `tenant_site_name`, `tenant_primary_color`, and `tenant_logo` into templates.

**Subscription Hooks:** `Tenant.subscription_plan` (free/starter/professional/enterprise), `subscription_status` (active/trial/past_due/cancelled/suspended), `max_users`, `max_products`.  Helper methods `is_within_user_limit()` and `is_within_product_limit()` enforce plan limits.

**Wagtail snippets:** Only **`Tenant`** is registered as a snippet viewset in the default tree ([tenants/snippets.py](../tenants/snippets.py)). **`TenantScopedSnippetViewSet`** is the base class for registering **tenant-scoped** inventory (or other) models when you want them visible in Wagtail for **monitoring, support, or admin workflows**. Doing so is a **deliberate product/architecture decision**; it does **not** replace the **API + Next.js** path as the **primary** channel for tenant operators’ routine inventory work.

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
| `/admin/` | `wagtail.admin.urls` | Wagtail admin (**platform** UI: tenants, reports, imports, etc.) |
| `/django-admin/` | `django.contrib.admin` | Django admin (low-level) |
| `/documents/` | `wagtail.documents.urls` | Document library |
| `/search/` | `search.views.search` | Site-wide search |
| `/` (catch-all) | `wagtail.urls` | Wagtail page serving |

| `/api/v1/` | DRF `DefaultRouter` | **REST API — primary tenant inventory CRUD** |

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
4. Optionally runs `seed_database` when `AUTO_SEED_DATABASE` is set (see below)
5. Starts Gunicorn with `--access-logfile -` and `--error-logfile -` so each HTTP request and worker errors show up in the container/platform log stream (e.g. Render **Logs**)

**Auto-seed environment variables** (`AUTO_SEED_DATABASE`, `SEED_*`) are **not** Django settings and **not** gunicorn arguments. They are **OS environment variables** read only by `entrypoint.sh` at container start (after `migrate`, before gunicorn). Configure them in your host platform: Render **Environment** tab, Docker `-e` / Compose `environment` or `env_file`, etc. Local `manage.py runserver` does not run the entrypoint — use `python manage.py seed_database` manually there.

### Environment Variables (Production)

For a **complete reference of all environment variables, setup guides, and troubleshooting**, see the [Environment Configuration Guide](ENVIRONMENT.md).

**Quick production checklist:**

| Variable | Purpose | Required |
|---|---|---|
| `DJANGO_SETTINGS_MODULE` | `the_inventory.settings.production` | Yes |
| `SECRET_KEY` | Django secret key (generate a new one) | Yes |
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `ALLOWED_HOSTS` | Comma-separated allowed hostnames | Yes |
| `FRONTEND_URL` | Frontend application URL (for emails, redirects) | Recommended |
| `REDIS_URL` | Redis for caching and Celery (optional; LocMemCache used if unset) | Optional |
| `AUTO_SEED_DATABASE` | Container env only: if truthy, `entrypoint.sh` runs `seed_database` after migrate | Optional |
| `CORS_ALLOWED_ORIGINS` | Allowed frontend origins for CORS requests | Recommended |
| `EMAIL_HOST`, `EMAIL_PORT`, etc. | SMTP configuration for transactional emails | Optional |

Additional tunables (CORS, CSRF, JWT lifetimes, cache TTLs, OpenAPI docs, pagination, email, etc.) are read from the environment in `the_inventory/settings/base.py` via `env_utils`. See [.env.example](../.env.example) for complete names and defaults.

Production settings automatically:
- Set `DEBUG = False` (enforce security)
- Require `SECRET_KEY` (raises error if missing)
- Use `ManifestStaticFilesStorage` (hash-based static file caching)
- Default `JWT_COOKIE_SECURE` to true
- Set `SECURE_PROXY_SSL_HEADER` when `USE_X_FORWARDED_PROTO` is true (default)

**For full documentation:**
- [Environment Configuration Guide](ENVIRONMENT.md) — All variables, examples, setup for local/Docker/production
- [Seeding Guide](SEEDING_GUIDE.md) — Database seeding with environment variables
- [Seeder Documentation](../seeders/README.md) — Complete seeding system reference

---

## Contributing

See the [Contributing Guide](../CONTRIBUTING.md) for development workflow, coding standards, and PR guidelines.
