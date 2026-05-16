# Features

**The Inventory** is a comprehensive REST API for managing inventory, procurement, sales, and reporting. It's built with Django and designed for multi-tenant SaaS deployments.

---

## Core Capabilities

### 📦 Inventory Management

**Manage your product catalog and stock levels**

- **Products** — Create and manage product catalog with SKU, descriptions, images, and pricing
- **Categories** — Organize products into hierarchical categories
- **Stock Locations** — Define warehouse and storage locations with hierarchical structure
- **Stock Tracking** — Real-time stock levels per product per location
- **Stock Movements** — Complete audit trail of all inventory changes (receive, issue, transfer, adjustment)
- **Low Stock Alerts** — Automatic alerts when stock falls below reorder points
- **Unit of Measure** — Support for different units (pieces, kg, liters, meters, boxes, packs)

### 🛒 Procurement

**Manage supplier relationships and purchase orders**

- **Suppliers** — Maintain supplier contacts, lead times, and terms
- **Purchase Orders** — Create and manage purchase orders with line items
- **Goods Received Notes (GRN)** — Track incoming goods and auto-update stock
- **Order Status Workflows** — Draft → Confirmed → Fulfilled
- **Procurement Services** — Confirm, cancel, and receive goods with validation

### 💳 Sales

**Manage customer relationships and sales orders**

- **Customers** — Maintain customer contacts and information
- **Sales Orders** — Create and manage sales orders with line items
- **Dispatch/Shipment** — Track shipments and auto-update stock
- **Order Status Workflows** — Draft → Confirmed → Fulfilled
- **Sales Services** — Confirm, cancel, and process dispatch with validation

### 📊 Reporting & Analytics

**Gain insights into inventory health and business metrics**

- **Stock Valuation Reports** — Weighted average and latest cost analysis
- **Movement History** — Complete audit trail with filtering by date, type, product, location
- **Low Stock Report** — Identify items below reorder points
- **Overstock Report** — Identify overstocked items
- **Purchase Summaries** — Daily, weekly, monthly aggregations
- **Sales Summaries** — Daily, weekly, monthly aggregations
- **CSV & PDF Export** — Export all reports in multiple formats
- **Dashboard Charts** — Visual analytics (stock by location, trends, order status)

### 🔐 Multi-Tenancy & SaaS

**Support multiple organizations on a single deployment**

- **Tenant Isolation** — Complete data separation between organizations
- **Tenant Management** — Create and manage organizations
- **User Memberships** — Assign users to organizations with roles
- **Role-Based Access Control (RBAC)** — Owner, Coordinator, Manager, Viewer roles
- **Per-Tenant Branding** — Customize admin interface per organization
- **Subscription Hooks** — Support for billing and plan limits

### 🌍 Internationalization

**Support multiple languages**

- **Multi-Language Support** — Backend supports multiple languages
- **Language Parameter** — API endpoint parameter for language selection
- **Translation Workflow** — Manage translations for product names, descriptions, etc.
- **Supported Languages** — English, Spanish, French, Arabic, Swahili, Kinyarwanda

### 🔌 REST API

**Comprehensive REST API for all operations**

- **RESTful Endpoints** — Standard HTTP methods (GET, POST, PUT, PATCH, DELETE)
- **JWT Authentication** — Stateless token-based authentication
- **Token Authentication** — API token support for scripts and integrations
- **Session Authentication** — Browser-based authentication
- **Pagination** — Configurable page sizes with max limits
- **Filtering** — Advanced filtering on all list endpoints
- **Search** — Full-text search on products, suppliers, customers
- **Ordering** — Sort results by any field
- **OpenAPI Schema** — Auto-generated API documentation
- **Swagger UI** — Interactive API explorer
- **Redoc** — Beautiful API documentation

### 🔒 Security & Compliance

**Enterprise-grade security features**

- **JWT Tokens** — Secure stateless authentication
- **CORS Support** — Cross-origin requests for frontend integration
- **CSRF Protection** — Cross-site request forgery prevention
- **Permission Enforcement** — Fine-grained access control
- **Audit Logging** — Track all user actions
- **API Impersonation** — Support staff break-glass access
- **Tenant Scoping** — Automatic data isolation per tenant

### 🛠️ Admin Interface

**Wagtail-based admin for platform operators**

- **Wagtail Admin** — Powerful admin interface at `/admin/`
- **Tenant Management** — Create and manage organizations
- **User Management** — Create users and assign roles
- **Reports** — View all reports in admin
- **Imports** — Bulk import products, suppliers, customers
- **Dashboard** — Overview of system health and metrics

---

## Technical Capabilities

### Database

- **SQLite** — Development (file-based)
- **PostgreSQL** — Production (recommended)
- **Migrations** — Automatic schema management

### Search

- **Database Search** — Default full-text search backend
- **Elasticsearch** — Optional advanced search (Phase 4)

### Performance

- **Caching** — Redis-based caching for frequently accessed data
- **Pagination** — Efficient data retrieval with configurable page sizes
- **Indexing** — Database indexes on frequently queried fields
- **Async Tasks** — Celery support for background jobs

### Deployment

- **Docker** — Container-ready with Dockerfile
- **Environment Variables** — Flexible configuration
- **Gunicorn** — Production WSGI server
- **Static Files** — Optimized static file serving
- **Media Storage** — Support for local and cloud storage

---

## What's NOT Included

### Frontend
- **No UI included** — This is a headless API
- **Frontend is separate** — See [the-inventory-ui](https://github.com/Ndevu12/the-inventory-ui) for Next.js frontend
- **API-first design** — Build any frontend you want

### Advanced Features (Planned)
- **Barcode scanning** — Planned for future release
- **QR codes** — Planned for future release
- **Webhooks** — Planned for future release
- **Advanced analytics** — Planned for future release

---

## Use Cases

### Small Business
- Track inventory across single or multiple locations
- Manage suppliers and purchase orders
- Monitor stock levels and reorder points
- Generate reports for decision-making

### Growing Company
- Multi-location inventory management
- Supplier and customer management
- Sales order processing
- Financial reporting and analysis

### Enterprise
- Multi-tenant SaaS deployment
- Complex organizational structures
- Advanced reporting and analytics
- Integration with other systems

### Third-Party Integrations
- Build custom frontends
- Integrate with accounting systems
- Connect to e-commerce platforms
- Build mobile apps

---

## API Endpoints Overview

### Authentication
- `POST /api/v1/auth/login/` — User login
- `POST /api/v1/auth/refresh/` — Refresh access token
- `GET /api/v1/auth/me/` — Get current user profile

### Inventory
- `GET/POST /api/v1/products/` — Product management
- `GET/POST /api/v1/categories/` — Category management
- `GET/POST /api/v1/stock-locations/` — Location management
- `GET /api/v1/stock-records/` — Current stock levels
- `GET/POST /api/v1/stock-movements/` — Stock movement history

### Procurement
- `GET/POST /api/v1/suppliers/` — Supplier management
- `GET/POST /api/v1/purchase-orders/` — Purchase order management
- `GET/POST /api/v1/goods-received-notes/` — GRN management

### Sales
- `GET/POST /api/v1/customers/` — Customer management
- `GET/POST /api/v1/sales-orders/` — Sales order management
- `GET/POST /api/v1/dispatches/` — Dispatch management

### Reporting
- `GET /api/v1/reports/stock-valuation/` — Stock valuation report
- `GET /api/v1/reports/movements/` — Movement history report
- `GET /api/v1/reports/low-stock/` — Low stock report
- `GET /api/v1/reports/overstock/` — Overstock report
- `GET /api/v1/reports/purchases/` — Purchase summary report
- `GET /api/v1/reports/sales/` — Sales summary report

### Tenants
- `GET /api/v1/tenants/current/` — Current tenant info
- `GET /api/v1/tenants/memberships/` — User memberships

---

## Getting Started

Ready to get started? Follow the [Getting Started Guide](getting-started.md).

For detailed API reference, see the [API Documentation](api.md).

For deployment, see the [Deployment Guide](deployment.md).
