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
| Containerization | Docker | Single-container for now |

### Frontend / UI Stack

The project uses a **server-rendered** approach with lightweight client-side enhancements — no Node.js build step required.

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
│   ── Planned apps ──
│
├── inventory/              ← [Phase 1] Core inventory models & logic
├── procurement/            ← [Phase 2] Suppliers & purchase orders
├── sales/                  ← [Phase 2] Customers & sales orders
├── reports/                ← [Phase 3] Reporting & analytics
└── api/                    ← [Phase 4] REST API
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

#### Schema Design Decisions

These decisions were made upfront to avoid costly migrations later:

| Decision | Choice | Rationale |
|---|---|---|
| Audit fields | `TimeStampedModel` abstract base | `created_at`, `updated_at`, `created_by` on all models |
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
    """Audit fields inherited by all inventory models."""
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

#### Models

| Model | Type | Key Fields | Purpose |
|---|---|---|---|
| `TimeStampedModel` | Abstract base | `created_at`, `updated_at`, `created_by` | Audit trail on all models |
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

Movement processing is transactional: quantity changes to `StockRecord` happen atomically inside `StockMovement.save()`. Validation rules:

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

> **Note:** The apps below do not exist yet. They are documented here so that Phase 1 schema decisions account for future needs. These designs may change based on Phase 1 learnings.

---

### `procurement/` — Phase 2 (Future)

| Model | Purpose |
|---|---|
| `Supplier` | Vendor / supplier details (contacts, lead times, payment terms) |
| `PurchaseOrder` | Order placed with a supplier (status workflow: draft → confirmed → received) |
| `PurchaseOrderLine` | Line items (FK → Product, quantity, unit cost) |
| `GoodsReceivedNote` | Confirmation of goods arrival — triggers a `receive` StockMovement automatically |

---

### `sales/` — Phase 2 (Future)

| Model | Purpose |
|---|---|
| `Customer` | Customer / client details |
| `SalesOrder` | Order from a customer (status workflow: draft → confirmed → fulfilled) |
| `SalesOrderLine` | Line items (FK → Product, quantity, unit price) |
| `Dispatch` | Shipment record — triggers an `issue` StockMovement automatically |

---

### `reports/` — Phase 3 (Future)

No persistent models — this app will provide **read-only views and exports** querying data from `inventory`, `procurement`, and `sales`.

- Stock valuation (FIFO / weighted average) — powered by `StockMovement.unit_cost`
- Movement audit trail — powered by `TimeStampedModel` fields
- Low-stock / overstock summaries
- Purchase & sales aggregations
- CSV / PDF export endpoints

---

### `api/` — Phase 4 (Future)

Built with **Django REST Framework**. Will expose serialized endpoints for:

- Products, categories, stock locations
- Stock levels & movements
- Purchase orders & sales orders
- Webhook registration for stock events

Authentication via token / API key. Pagination, filtering (`django-filter`), and search powered by the same Wagtail search backend.

---

## URL Routing

| Path | Handler | Purpose |
|---|---|---|
| `/admin/` | `wagtail.admin.urls` | Wagtail admin (primary UI) |
| `/django-admin/` | `django.contrib.admin` | Django admin (low-level) |
| `/documents/` | `wagtail.documents.urls` | Document library |
| `/search/` | `search.views.search` | Site-wide search |
| `/` (catch-all) | `wagtail.urls` | Wagtail page serving |

Future phases will add:
- `/api/v1/` — REST API endpoints (Phase 4)

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
