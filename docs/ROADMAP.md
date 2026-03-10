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

## Phase 2 — Procurement & Sales 📋

Extend the system to track the full lifecycle of goods — from purchase orders to customer sales.

**Apps:** `procurement/`, `sales/`

**Planned models:** `Supplier`, `PurchaseOrder`, `PurchaseOrderLine`, `GoodsReceivedNote`, `Customer`, `SalesOrder`, `SalesOrderLine`, `Dispatch`

| Feature | Status |
|---|---|
| Supplier management (contacts, lead times, terms) | 📋 |
| Purchase orders with line items | 📋 |
| Goods received notes (GRN) — auto-create `receive` StockMovement | 📋 |
| Customer / client management | 📋 |
| Sales orders with line items | 📋 |
| Dispatch / shipment tracking — auto-create `issue` StockMovement | 📋 |
| Order status workflows (draft → confirmed → fulfilled) | 📋 |

---

## Phase 3 — Reporting & Analytics 📋

Provide insight into inventory health, movement trends, and financial summaries.

**App:** `reports/` (no persistent models — read-only views and exports)

| Feature | Status |
|---|---|
| Stock valuation reports (FIFO / weighted average via `StockMovement.unit_cost`) | 📋 |
| Movement history & audit trail (via `TimeStampedModel` fields) | 📋 |
| Low-stock & overstock reports | 📋 |
| Purchase & sales summaries (daily / weekly / monthly) | 📋 |
| Exportable reports (CSV, PDF) | 📋 |
| Dashboard charts (Wagtail admin or standalone) | 📋 |

---

## Phase 4 — API & Integrations 📋

Open up the system for external consumers and third-party integrations.

**App:** `api/`

| Feature | Status |
|---|---|
| RESTful API (Django REST Framework) for products, stock, orders | 📋 |
| Token / API-key authentication | 📋 |
| Webhook support for stock events (low stock, new order) | 📋 |
| Barcode / QR code scanning support | 📋 |
| Import / export via CSV & Excel | 📋 |
| Optional Elasticsearch backend for advanced search | 📋 |

---

## Phase 5 — Multi-tenancy & SaaS (Stretch) 📋

Enable multiple organizations to use a single deployment.

| Feature | Status |
|---|---|
| Tenant-aware models and queries | 📋 |
| Per-tenant admin branding | 📋 |
| Role-based access control (RBAC) | 📋 |
| Subscription / billing hooks | 📋 |

---

## How to Contribute

Pick any **📋 Planned** item, open an issue to discuss your approach, and submit a PR. See the [Contributing Guide](../CONTRIBUTING.md) for workflow details.
