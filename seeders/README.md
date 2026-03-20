# Seeders App

The `seeders` app is an independent Django application responsible for populating the database with sample data for development and testing. It provides a flexible, extensible seeding system with support for multi-tenancy, idempotent operations, and selective model seeding.

## Quick Start

Seed the entire database with all sample data:

```bash
python manage.py seed_database --clear --create-default
```

This will:
1. Create a "Default" tenant (if it doesn't exist)
2. Create 3 test users linked to the Default tenant
3. Create 10 product categories (hierarchical)
4. Create 15 products across categories
5. Create 17 stock locations (warehouse structure)
6. Create 19 stock records (inventory levels)
7. Create 10 stock movements (audit history)
8. Create low-stock scenarios for testing alerts

## App Structure

```
seeders/
├── management/
│   └── commands/
│       └── seed_database.py      # Django management command
├── tests/                         # Comprehensive test suite (72 tests)
│   ├── test_base_seeder.py
│   ├── test_seed_command.py
│   ├── test_seeder_manager.py
│   └── test_seeder_tenant.py
├── apps.py                        # Django app configuration
├── base.py                        # BaseSeeder abstract class
├── seeder_manager.py              # SeederManager orchestration
├── tenant_seeder.py               # TenantSeeder
├── user_seeder.py                 # UserSeeder
├── category_seeder.py             # CategorySeeder
├── product_seeder.py              # ProductSeeder
├── stock_location_seeder.py       # StockLocationSeeder
├── stock_record_seeder.py         # StockRecordSeeder
├── stock_movement_seeder.py       # StockMovementSeeder
├── low_stock_seeder.py            # LowStockSeeder
└── README.md                      # This file
```

## Architecture

### Seeder Execution Order

Seeders run in dependency order to respect foreign key relationships:

1. **TenantSeeder** — Creates/retrieves the tenant
2. **UserSeeder** — Creates tenant users with roles
3. **CategorySeeder** — Creates product categories (hierarchical)
4. **ProductSeeder** — Creates products
5. **StockLocationSeeder** — Creates warehouse locations
6. **StockRecordSeeder** — Creates stock records (inventory levels)
7. **StockMovementSeeder** — Creates stock movements (audit history)
8. **LowStockSeeder** — Creates low-stock scenarios

### Key Components

#### BaseSeeder
Abstract base class providing common functionality:
- Transaction management via `transaction.atomic()`
- Tenant context handling
- Verbose logging
- Helper methods for creating tenant-aware models

#### SeederManager
Orchestrates all seeders in the correct dependency order:
- Runs TenantSeeder first to ensure tenant exists
- Passes tenant to all downstream seeders
- Supports selective model seeding
- Handles data clearing

#### Individual Seeders
Each seeder is responsible for one or more related models and implements idempotent operations.

## Usage

### Basic Seeding

Seed all models into the Default tenant:
```bash
python manage.py seed_database --create-default
```

### Clear and Reseed

Clear existing data and reseed:
```bash
python manage.py seed_database --clear --create-default
```

### Seed Specific Tenant

Seed into a specific tenant:
```bash
python manage.py seed_database --tenant=acme-corp
```

### Seed Specific Models

Seed only certain models:
```bash
python manage.py seed_database --models=categories,products
```

Available models: `categories`, `products`, `locations`, `records`, `movements`

### Quiet Mode

Suppress verbose output:
```bash
python manage.py seed_database --quiet --create-default
```

## Idempotency

All seeders are **idempotent** — they can be safely re-run without creating duplicates:

- **TenantSeeder**: Uses `get_or_create()` to retrieve existing tenant
- **CategorySeeder**: Checks existence before creating child nodes
- **ProductSeeder**: Uses `get_or_create()` by SKU
- **StockLocationSeeder**: Checks existence before creating child nodes
- **StockRecordSeeder**: Uses `get_or_create()` by product + location
- **StockMovementSeeder**: Checks existence before creating
- **LowStockSeeder**: Checks existence before creating scenarios

## Multi-Tenancy

All seeders support multi-tenancy:

1. **TenantSeeder** creates/retrieves a tenant and returns it
2. **SeederManager** passes the tenant to all downstream seeders
3. Each seeder receives the tenant via `execute(tenant=tenant_instance)`
4. All created models are automatically associated with the tenant

### Example: Programmatic Seeding

```python
from seeders import SeederManager
from tenants.models import Tenant
from tenants.context import set_current_tenant, clear_current_tenant

# Get or create tenant
tenant = Tenant.objects.get_or_create(
    slug="acme-corp",
    defaults={"name": "ACME Corporation", "is_active": True}
)[0]

# Set tenant context
set_current_tenant(tenant)

try:
    # Seed data
    manager = SeederManager(verbose=True, clear_data=False)
    manager.seed(tenant=tenant)
finally:
    # Clear tenant context
    clear_current_tenant()
```

## Creating Custom Seeders

To create a custom seeder:

1. Inherit from `BaseSeeder`
2. Implement the `seed()` method
3. Use `self.create_with_tenant()` or `self.add_root_with_tenant()` for model creation
4. Add to `SeederManager` in the correct dependency order

### Example

```python
from seeders.base import BaseSeeder
from inventory.models import Product

class CustomSeeder(BaseSeeder):
    """Custom seeder for specific models."""

    def seed(self):
        """Seed custom data."""
        self.log("Creating custom products...")
        
        # Check if already exists
        if Product.objects.filter(sku="CUSTOM-001").exists():
            self.log("Custom product already exists, skipping")
            return
        
        # Create product
        product = self.create_with_tenant(
            Product,
            sku="CUSTOM-001",
            name="Custom Product",
            description="A custom product"
        )
        self.log(f"Created product: {product.name}")
```

## Testing

Run all seeder tests:
```bash
python manage.py test seeders.tests
```

Run specific test class:
```bash
python manage.py test seeders.tests.test_seeder_tenant.TenantSeederTestCase
```

Run with verbose output:
```bash
python manage.py test seeders.tests --verbosity=2
```

### Test Coverage

The seeders app includes 72 comprehensive tests covering:

- **BaseSeeder**: Transaction handling, tenant context, error handling
- **TenantSeeder**: Tenant creation, idempotency, concurrent execution
- **Individual Seeders**: Data creation, idempotency, relationships
- **SeederManager**: Orchestration, dependency order, data integrity
- **Management Command**: CLI argument parsing, tenant resolution, error handling

## Sample Data

### Test Users
- **admin** (password: `admin123`) — Superuser with ADMIN role
- **manager** (password: `manager123`) — Staff user with MANAGER role
- **user** (password: `user123`) — Regular user with VIEWER role

### Categories
- Electronics (root)
  - Phones
  - Laptops
  - Accessories
- Furniture (root)
  - Desks
  - Chairs
- Office Supplies (root)
  - Pens & Pencils
  - Paper & Notepads

### Products (15 total)
- High-value items: iPhones, MacBooks, Samsung Galaxy, Dell XPS
- Medium-value items: Desks, Chairs
- Low-value items: Cables, Mice, Pens, Paper

### Warehouse Structure
- 2 Warehouses
- 3 Aisles in main warehouse
- 6 Shelves across aisles
- 4 Bins for detailed storage
- 17 locations total with hierarchical relationships

### Stock Levels
- High-stock items: 50-200 units (accessories, consumables)
- Medium-stock items: 5-30 units (products, furniture)
- Low-stock items: 3-15 units (expensive electronics)

### Movement History
- 4 Receives (initial stock and restocks)
- 2 Issues (sales/fulfillment)
- 2 Transfers (internal repositioning)
- 2 Adjustments (corrections)
- Timestamps varied over 10 days

## Performance Considerations

- All seeding operations use `transaction.atomic()` for consistency
- Seeders use `get_or_create()` to avoid duplicate creation
- Bulk operations are used where possible
- Verbose logging can be disabled with `--quiet` flag

## Troubleshooting

### "Default tenant does not exist"

Use `--create-default` flag:
```bash
python manage.py seed_database --create-default
```

### "Tenant with slug 'X' not found"

Create the tenant first via admin or use `--create-default` for the Default tenant.

### Duplicate data after re-running

All seeders are idempotent. If duplicates appear, check that:
1. Seeders are using `get_or_create()` or existence checks
2. Unique constraints are properly defined on models
3. No custom seeders are bypassing idempotency checks

## Integration with Django

The seeders app is registered in `INSTALLED_APPS` in `the_inventory/settings/base.py`:

```python
INSTALLED_APPS = [
    # ...
    "seeders",
    # ...
]
```

This enables:
- Management command discovery
- Test discovery
- App configuration loading

## Future Enhancements

- [ ] Seed data fixtures (JSON/YAML)
- [ ] Conditional seeding based on environment
- [ ] Performance profiling for large datasets
- [ ] Seed data versioning
- [ ] Rollback/cleanup utilities
