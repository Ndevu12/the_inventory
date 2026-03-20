# Project Structure & Architecture

## Directory Organization

```
the_inventory/                    # Project root
├── the_inventory/                # Django project configuration
│   ├── settings/
│   │   ├── base.py              # Shared settings (Django, Wagtail, DRF, Celery)
│   │   ├── dev.py               # Development overrides
│   │   └── production.py         # Production overrides
│   ├── urls.py                  # Root URL configuration
│   ├── wsgi.py                  # WSGI application
│   ├── celery.py                # Celery configuration
│   ├── templates/               # Project-level templates (base, 404, 500)
│   └── static/                  # Project-level static files
│
├── home/                         # Landing page app
│   ├── models.py                # HomePage model
│   ├── views.py                 # Home page views
│   ├── templates/               # Home page templates
│   └── migrations/
│
├── search/                       # Site-wide search app
│   ├── views.py                 # Search views
│   └── templates/               # Search templates
│
├── tenants/                      # Multi-tenancy core
│   ├── models.py                # Tenant, TenantMembership, TenantRole, TenantInvitation
│   ├── managers.py              # Tenant-aware query managers
│   ├── services.py              # Tenant service layer
│   ├── context.py               # Tenant context management (get/set_current_tenant)
│   ├── middleware.py            # TenantMiddleware, ImpersonationMiddleware
│   ├── permissions.py           # Tenant-based permissions
│   ├── context_processors.py    # Template context processors
│   ├── wagtail_hooks.py         # Wagtail admin customizations
│   ├── wagtail_views.py         # Wagtail admin views
│   ├── wagtail_forms.py         # Wagtail admin forms
│   ├── snippets.py              # Wagtail snippets
│   ├── panels/                  # Wagtail dashboard panels
│   ├── tests/                   # Comprehensive tenant tests
│   └── migrations/
│
├── inventory/                    # Core inventory management (Phase 1)
│   ├── models/
│   │   ├── base.py              # TenantAwareModel, TimestampedModel base classes
│   │   ├── category.py          # Category model
│   │   ├── product.py           # Product, ProductImage, ProductTag models
│   │   ├── stock.py             # StockLocation, StockRecord, StockMovement, StockLot models
│   │   ├── lot.py               # Lot and movement lot tracking
│   │   ├── reservation.py       # StockReservation, ReservationRule models
│   │   ├── cycle.py             # InventoryCycle, CycleCountLine, InventoryVariance models
│   │   ├── audit.py             # ComplianceAuditLog model
│   │   └── job.py               # AsyncJob model for background tasks
│   │
│   ├── services/
│   │   ├── stock.py             # StockService (process_movement, get_stock_level, etc.)
│   │   ├── audit.py             # AuditService (log_action, get_audit_trail)
│   │   ├── cache.py             # CacheService (stock level caching)
│   │   ├── bulk.py              # BulkService (bulk operations)
│   │   ├── cycle.py             # CycleService (inventory cycle management)
│   │   └── reservation.py       # ReservationService (stock reservation logic)
│   │
│   ├── seeders/
│   │   ├── base.py              # BaseSeed base class
│   │   ├── seeder_manager.py    # SeederManager orchestration
│   │   ├── tenant_seeder.py     # TenantSeeder
│   │   ├── category_seeder.py   # CategorySeeder
│   │   ├── product_seeder.py    # ProductSeeder
│   │   ├── stock_location_seeder.py
│   │   ├── stock_record_seeder.py
│   │   ├── stock_movement_seeder.py
│   │   ├── low_stock_seeder.py
│   │   └── README.md            # Seeding documentation
│   │
│   ├── panels/                  # Wagtail dashboard panels
│   │   ├── stock_summary.py
│   │   ├── low_stock.py
│   │   ├── recent_movements.py
│   │   ├── expiring_lots.py
│   │   ├── pending_reservations.py
│   │   ├── movement_trend_chart.py
│   │   ├── stock_by_location_chart.py
│   │   └── order_status_chart.py
│   │
│   ├── imports/
│   │   ├── importers.py         # CSV/Excel importers
│   │   ├── parsers.py           # Data parsers
│   │   ├── forms.py             # Import forms
│   │   ├── views.py             # Import views
│   │   └── tests/
│   │
│   ├── management/commands/     # Django management commands
│   ├── filters.py               # DjangoFilter filters
│   ├── views.py                 # Wagtail admin views
│   ├── admin.py                 # Django admin configuration
│   ├── wagtail_hooks.py         # Wagtail admin customizations
│   ├── tasks.py                 # Celery tasks
│   ├── exceptions.py            # Custom exceptions
│   ├── tests/                   # Comprehensive test suite
│   ├── templates/               # Wagtail templates
│   ├── static/                  # Static files
│   └── migrations/
│
├── procurement/                  # Purchase order management (Phase 2)
│   ├── models/
│   │   ├── order.py             # PurchaseOrder, PurchaseOrderLine models
│   │   └── supplier.py          # Supplier model
│   ├── services/
│   │   └── procurement.py       # ProcurementService
│   ├── tests/
│   ├── admin.py
│   ├── wagtail_hooks.py
│   └── migrations/
│
├── sales/                        # Sales order management (Phase 2)
│   ├── models/
│   │   ├── order.py             # SalesOrder, SalesOrderLine, Dispatch models
│   │   └── customer.py          # Customer model
│   ├── services/
│   │   └── sales.py             # SalesService
│   ├── tests/
│   ├── admin.py
│   ├── wagtail_hooks.py
│   └── migrations/
│
├── reports/                      # Reporting & analytics
│   ├── services/
│   │   ├── inventory_reports.py # Inventory report generation
│   │   └── order_reports.py     # Order report generation
│   ├── exports.py               # Export utilities
│   ├── pdf.py                   # PDF generation
│   ├── filters.py               # Report filters
│   ├── views.py                 # Report views
│   ├── tests/
│   ├── templates/
│   ├── wagtail_hooks.py
│   └── migrations/
│
├── api/                          # RESTful API
│   ├── views/
│   │   ├── inventory.py         # Product, Category, StockRecord, StockMovement viewsets
│   │   ├── procurement.py       # PurchaseOrder viewsets
│   │   ├── sales.py             # SalesOrder viewsets
│   │   ├── reports.py           # Report viewsets
│   │   ├── tenants.py           # Tenant management viewsets
│   │   ├── users.py             # User management viewsets
│   │   ├── auth.py              # Authentication viewsets
│   │   ├── audit.py             # Audit log viewsets
│   │   ├── bulk.py              # Bulk operation viewsets
│   │   ├── cycle.py             # Inventory cycle viewsets
│   │   ├── reservation.py       # Stock reservation viewsets
│   │   ├── jobs.py              # Async job viewsets
│   │   ├── dashboard.py         # Dashboard data viewsets
│   │   ├── invitations.py       # Tenant invitation viewsets
│   │   └── billing.py           # Billing viewsets
│   │
│   ├── serializers/
│   │   ├── inventory.py         # Product, Category, Stock serializers
│   │   ├── procurement.py       # PurchaseOrder serializers
│   │   ├── sales.py             # SalesOrder serializers
│   │   ├── reports.py           # Report serializers
│   │   ├── tenants.py           # Tenant serializers
│   │   ├── users.py             # User serializers
│   │   ├── auth.py              # Auth serializers
│   │   ├── audit.py             # Audit serializers
│   │   ├── bulk.py              # Bulk operation serializers
│   │   ├── cycle.py             # Cycle serializers
│   │   ├── reservation.py       # Reservation serializers
│   │   ├── jobs.py              # Job serializers
│   │   ├── dashboard.py         # Dashboard serializers
│   │   ├── invitations.py       # Invitation serializers
│   │   └── billing.py           # Billing serializers
│   │
│   ├── permissions.py           # Custom DRF permissions
│   ├── pagination.py            # Custom pagination classes
│   ├── middleware.py            # JWT middleware
│   ├── urls.py                  # API URL routing
│   ├── tests/                   # API test suite
│   └── apps.py
│
├── frontend/                     # Next.js React frontend
│   ├── src/
│   │   ├── app/                 # Next.js app directory
│   │   ├── components/          # Reusable React components
│   │   ├── features/            # Feature-specific components
│   │   ├── hooks/               # Custom React hooks
│   │   ├── lib/                 # Utility functions
│   │   └── types/               # TypeScript type definitions
│   ├── public/                  # Static assets
│   ├── package.json
│   ├── tsconfig.json
│   ├── next.config.ts
│   └── README.md
│
├── docs/                         # Project documentation
│   ├── ARCHITECTURE.md          # Technical architecture
│   ├── ROADMAP.md               # Development roadmap
│   ├── SEEDING_GUIDE.md         # Database seeding guide
│   └── TASKS.MD                 # Task tracking
│
├── .amazonq/rules/              # Amazon Q rules
│   └── memory-bank/             # Memory bank documentation
│
├── .github/
│   ├── workflows/ci.yml         # CI/CD pipeline
│   ├── ISSUE_TEMPLATE/
│   └── PULL_REQUEST_TEMPLATE.md
│
├── requirements.txt             # Python dependencies
├── requirements-dev.txt         # Development dependencies
├── manage.py                    # Django management script
├── Dockerfile                   # Docker configuration
├── docker-compose.yml           # Docker Compose configuration
├── entrypoint.sh                # Docker entrypoint
├── README.md                    # Project README
├── CONTRIBUTING.md              # Contributing guide
├── CODE_OF_CONDUCT.md           # Code of conduct
├── CHANGELOG.md                 # Release history
├── LICENSE                      # BSD 3-Clause License
└── .env.example                 # Environment variables template
```

## Core Components & Relationships

### Multi-Tenancy Layer
- **Tenant Model**: Represents an organization/workspace
- **TenantMembership**: Links users to tenants with roles
- **TenantMiddleware**: Sets current tenant context from request
- **TenantAwareModel**: Base class ensuring all models are tenant-scoped
- **TenantContext**: Thread-local storage for current tenant

### Inventory Core
- **Product**: SKU, name, description, images, tags, reorder point
- **Category**: Product categorization with hierarchy
- **StockLocation**: Warehouse/storage locations with capacity
- **StockRecord**: Current stock level at a location
- **StockMovement**: Historical record of stock changes (receive, transfer, adjust, etc.)
- **StockLot**: Batch tracking with expiration dates
- **StockReservation**: Reserve stock for pending orders
- **InventoryCycle**: Physical inventory counts and variance analysis

### Service Layer
- **StockService**: Core business logic for stock operations
- **AuditService**: Compliance and audit trail logging
- **CacheService**: Stock level caching for performance
- **BulkService**: Bulk import/export operations
- **CycleService**: Inventory cycle management
- **ReservationService**: Stock reservation logic

### API Layer
- **ViewSets**: DRF viewsets for each model
- **Serializers**: Data serialization/deserialization
- **Permissions**: Tenant-based access control
- **Pagination**: Standardized pagination
- **Middleware**: JWT authentication, tenant context

### Frontend Layer
- **Next.js App**: React-based SPA
- **Components**: Reusable UI components
- **Features**: Feature-specific modules
- **Hooks**: Custom React hooks
- **Types**: TypeScript definitions

## Architectural Patterns

### Tenant Isolation
- All models inherit from TenantAwareModel
- Tenant context set via middleware
- QuerySets automatically filtered by tenant
- API endpoints enforce tenant permissions

### Service Layer Pattern
- Business logic in service classes
- Models contain only data structure
- Services handle validation and transactions
- Celery tasks delegate to services

### Factory Pattern
- Test factories for creating test data
- Seeders for database population
- Consistent data generation

### Middleware Pattern
- TenantMiddleware: Sets current tenant
- JWTAuthMiddleware: Handles JWT authentication
- ImpersonationMiddleware: Admin impersonation support

### Caching Strategy
- Stock levels cached for 10 minutes
- Dashboard data cached for 5 minutes
- Redis backend in production
- Local memory cache in development
