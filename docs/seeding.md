# Tenant-Scoped Seeding Guide

This document provides a quick reference for seeding the inventory database with tenant-scoped data.

## Quick Start

### Default Tenant (Auto-Create)
```bash
python manage.py seed_database --clear --create-default
```

This will:
1. Auto-create a "Default" tenant (if it doesn't exist)
2. Clear all existing inventory data
3. Seed all models (categories, products, locations, records, movements) linked to the Default tenant

### Specific Tenant
```bash
python manage.py seed_database --clear --tenant=acme-corp
```

This will seed data for the "acme-corp" tenant. The tenant must already exist.

## Common Scenarios

### Scenario 1: Fresh Development Setup
```bash
# Create Default tenant and seed all data
python manage.py seed_database --clear --create-default
```

### Scenario 2: Multi-Tenant Development
```bash
# Create tenants
python manage.py createtenant --name="Tenant A" --slug="tenant-a"
python manage.py createtenant --name="Tenant B" --slug="tenant-b"

# Seed data for each tenant independently
python manage.py seed_database --clear --tenant=tenant-a
python manage.py seed_database --clear --tenant=tenant-b

# Verify isolation
python manage.py shell
>>> from inventory.models import Product
>>> from tenants.models import Tenant
>>> Tenant.objects.get(slug="tenant-a").inventory_product_set.count()
15
>>> Tenant.objects.get(slug="tenant-b").inventory_product_set.count()
15
```

### Scenario 3: Seed Specific Models Only
```bash
# Seed only categories and products for a tenant
python manage.py seed_database --models categories,products --tenant=acme-corp

# Available models: categories, products, locations, records, movements
```

### Scenario 4: Add Data Without Clearing
```bash
# Seed without clearing existing data (soft seed)
python manage.py seed_database --tenant=acme-corp
```

### Scenario 5: Suppress Output
```bash
# Run seeding silently
python manage.py seed_database --clear --create-default --quiet
```

## Programmatic Usage

Use `SeederManager` directly in scripts or tests:

```python
from inventory.seeders import SeederManager
from tenants.models import Tenant
from tenants.context import set_current_tenant, clear_current_tenant

# Get or create a tenant
tenant, created = Tenant.objects.get_or_create(
    slug="acme-corp",
    defaults={"name": "ACME Corp", "is_active": True}
)

# Set tenant context (required for audit logging)
set_current_tenant(tenant)

try:
    # Seed everything for this tenant
    manager = SeederManager(verbose=True, clear_data=True)
    manager.seed(tenant=tenant)
finally:
    # Always clear context after seeding
    clear_current_tenant()
```

## Seeded Data Overview

### Categories (10 total)
- **Electronics** (root)
  - Phones
  - Laptops
  - Accessories
- **Furniture** (root)
  - Desks
  - Chairs
- **Office Supplies** (root)
  - Pens & Pencils
  - Paper & Notepads

### Products (15 total)
- High-value: iPhones, MacBooks, Samsung Galaxy, Dell XPS
- Medium-value: Desks, Chairs
- Low-value: Cables, Mice, Pens, Paper

### Stock Locations (17 total)
- 2 Warehouses
- 3 Aisles in main warehouse
- 6 Shelves across aisles
- 4 Bins for detailed storage

### Stock Records (19 total)
- Distributed across warehouse locations
- Stock levels: 3-200 units depending on product type

### Stock Movements (10 total)
- 4 Receives (inbound stock)
- 2 Issues (outbound/sales)
- 2 Transfers (internal repositioning)
- 2 Adjustments (inventory corrections)

## Troubleshooting

### Error: "Default tenant does not exist"

**Solution 1: Auto-create Default tenant**
```bash
python manage.py seed_database --clear --create-default
```

**Solution 2: Use an existing tenant**
```bash
# List available tenants
python manage.py shell
>>> from tenants.models import Tenant
>>> list(Tenant.objects.values_list('slug', flat=True))

# Seed for an existing tenant
python manage.py seed_database --clear --tenant=existing-slug
```

### Error: "Tenant with slug 'xyz' not found"

**Solution:**
```bash
# Create the tenant first
python manage.py createtenant --name="XYZ Corp" --slug="xyz"

# Then seed for it
python manage.py seed_database --clear --tenant=xyz
```

### Found orphaned data (NULL tenant values)

**Problem:** Existing data without tenant assignment (from old seeding runs before migration TS-06)

**Solution:** Run the migration to backfill:
```bash
python manage.py migrate
```

This migration:
1. Automatically assigns all NULL tenant records to the Default tenant
2. Makes the `tenant` field non-nullable to prevent future orphaning

**Verify no orphaned data:**
```bash
python manage.py shell
>>> from inventory.models import Product
>>> Product.objects.filter(tenant__isnull=True).count()
0  # Should be zero
```

### Seeding to wrong tenant

**Problem:** Data was seeded to the wrong tenant by mistake

**Solution:** Clear and reseed for the correct tenant:
```bash
python manage.py seed_database --clear --tenant=correct-tenant-slug
```

## Key Concepts

### Tenant Context
During seeding, the tenant context is automatically set via `set_current_tenant(tenant)`. This ensures:
- All created objects are linked to the tenant
- Audit fields (`created_by`) respect tenant context
- Thread-local context is available to all seeders

### Data Isolation
- Each tenant has independent copies of all inventory data
- Queries are automatically scoped to current tenant via `TenantAwareManager`
- No orphaned data: all seeded objects have `tenant` assigned
- Tenant field is non-nullable after migration TS-06

### Atomicity
All seeders are wrapped in transactions:
- If any seeder fails, all changes are rolled back
- Errors include full validation messages
- Useful for development: errors don't leave partial data
- Tenant context is preserved during transaction rollback

## Architecture

### Seeder Classes

| Seeder | Purpose | Tenant-Aware |
|---|---|---|
| `TenantSeeder` | Creates or retrieves the "Default" tenant | Yes |
| `CategorySeeder` | Creates product categories (hierarchical) | Yes |
| `ProductSeeder` | Creates products across categories | Yes |
| `StockLocationSeeder` | Creates warehouse structure (hierarchical) | Yes |
| `StockRecordSeeder` | Creates stock-location associations | Yes |
| `StockMovementSeeder` | Creates movement history | Yes |
| `LowStockSeeder` | Creates low-stock scenarios for alerts | Yes |

### Execution Order
1. TenantSeeder (ensures tenant exists)
2. CategorySeeder (needed by ProductSeeder)
3. ProductSeeder (needed by StockRecordSeeder and StockMovementSeeder)
4. StockLocationSeeder (needed by StockRecordSeeder and StockMovementSeeder)
5. StockRecordSeeder (depends on Products and Locations)
6. StockMovementSeeder (depends on Products and Locations)
7. LowStockSeeder (optional, creates alert scenarios)

## Related Documentation

- **Full Seeding Documentation:** [inventory/seeders/README.md](../inventory/seeders/README.md)
- **Architecture Overview:** [docs/ARCHITECTURE.md](./ARCHITECTURE.md)
- **Tenant Model Reference:** [tenants/models.py](../tenants/models.py)
- **Tenant Context:** [tenants/context.py](../tenants/context.py)
- **Management Command:** [inventory/management/commands/seed_database.py](../inventory/management/commands/seed_database.py)

## Best Practices

### Development
```bash
# Fresh start with complete dataset (uses Default tenant)
python manage.py seed_database --clear --create-default

# Add products to existing categories (same tenant)
python manage.py seed_database --models products --tenant=acme-corp

# Seed for a different tenant
python manage.py seed_database --clear --tenant=other-tenant
```

### Testing
```python
from inventory.seeders import SeederManager
from tenants.models import Tenant

class MyTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create test tenant
        tenant = Tenant.objects.create(
            name="Test Tenant",
            slug="test-tenant",
            is_active=True
        )
        # Seed data into it
        SeederManager(verbose=False, clear_data=True).seed(tenant=tenant)
        cls.tenant = tenant
    
    def test_product_count(self):
        from inventory.models import Product
        count = Product.objects.filter(tenant=self.tenant).count()
        self.assertEqual(count, 15)
```

### Multi-Tenant Setup
```bash
# Create tenants first
python manage.py createtenant --name="Tenant A" --slug="tenant-a"
python manage.py createtenant --name="Tenant B" --slug="tenant-b"

# Seed data for each
python manage.py seed_database --clear --tenant=tenant-a
python manage.py seed_database --clear --tenant=tenant-b

# Verify isolation: data is segregated by tenant
python manage.py shell
>>> from inventory.models import Product
>>> from tenants.models import Tenant
>>> tenant_a = Tenant.objects.get(slug="tenant-a")
>>> Product.objects.filter(tenant=tenant_a).count()
15  # 15 products for tenant-a
>>> tenant_b = Tenant.objects.get(slug="tenant-b")
>>> Product.objects.filter(tenant=tenant_b).count()
15  # 15 products for tenant-b (isolated)
```

## Getting Help

1. **Check CLI help:** `python manage.py seed_database --help`
2. **View available tenants:** `python manage.py shell` → `Tenant.objects.all()`
3. **Check seeding status:** Database queries in shell to verify tenant linkage
4. **Review logs:** Seeding output shows which tenant was used and what was created
5. **Full documentation:** See [inventory/seeders/README.md](../inventory/seeders/README.md)
