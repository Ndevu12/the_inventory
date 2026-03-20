# The Inventory - Product Overview

## Project Purpose

The Inventory is an open-source, multi-tenant inventory management system built with Wagtail CMS and Django. It provides a comprehensive platform for managing products, stock levels, warehouses, purchases, and sales through Wagtail's powerful admin interface and a RESTful API.

## Key Features & Capabilities

### Core Inventory Management (Phase 1)
- **Product Management**: Create, update, and manage products with SKUs, descriptions, images, and tags
- **Stock Tracking**: Real-time stock level monitoring across multiple warehouse locations
- **Stock Movements**: Track inbound/outbound movements with movement types (receive, transfer, adjust, etc.)
- **Stock Locations**: Manage multiple warehouse locations with capacity constraints
- **Stock Lots**: Track product batches with expiration dates and compliance information
- **Inventory Cycles**: Conduct physical inventory counts and variance analysis
- **Stock Reservations**: Reserve stock for pending orders with automatic fulfillment

### Procurement (Phase 2)
- Purchase order management
- Goods received notes (GRN)
- Supplier management
- Procurement workflows

### Sales (Phase 2)
- Sales order management
- Customer management
- Dispatch tracking
- Automatic stock reservation on order creation

### Reporting & Analytics
- Inventory reports (stock levels, movements, variance)
- Order reports (sales, procurement)
- PDF export capabilities
- Dashboard with charts and metrics

### Multi-Tenancy
- Complete tenant isolation with tenant-scoped data
- Tenant membership and role-based access control
- Tenant invitations and user management
- Billing and subscription management

### API & Integration
- RESTful API with OpenAPI/Swagger documentation
- JWT and token-based authentication
- Bulk operations support
- Async job processing with Celery

### Search & Indexing
- Full-text search on products, categories, and locations
- Wagtail search backend with database or Elasticsearch support

## Target Users & Use Cases

### Primary Users
- **Warehouse Managers**: Monitor stock levels, process movements, manage locations
- **Procurement Officers**: Create and track purchase orders, manage suppliers
- **Sales Teams**: Create sales orders, manage customer inventory
- **Business Analysts**: Generate reports and analyze inventory trends
- **System Administrators**: Manage tenants, users, and system configuration

### Use Cases
- Small to medium-sized businesses managing single or multiple warehouses
- Multi-location retail operations
- E-commerce fulfillment centers
- Manufacturing inventory tracking
- Hosted SaaS inventory management platform
- Self-hosted enterprise inventory systems

## Technology Stack

| Layer | Technology |
|---|---|
| Language | Python 3.12+ |
| Web Framework | Django 6.0 |
| CMS / Admin UI | Wagtail 7.3 |
| API Framework | Django REST Framework |
| Database | SQLite (dev) / PostgreSQL (production) |
| Search | Wagtail search backend (database or Elasticsearch) |
| Task Queue | Celery with Redis |
| Frontend | Next.js (React) |
| Containerization | Docker |
| Authentication | JWT + Token-based |

## Deployment Options

- **Development**: SQLite database, local Redis, Django development server
- **Production**: PostgreSQL database, Redis cache/broker, Gunicorn + Nginx
- **Docker**: Containerized deployment with Docker Compose
- **Hosted SaaS**: Multi-tenant cloud deployment with public registration
- **Self-Hosted**: Private deployment with restricted tenant creation
