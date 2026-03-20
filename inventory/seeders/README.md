"""Inventory App Seeder Documentation

This module provides a comprehensive seeding system for populating the inventory
database with realistic sample data for development and testing.

## Quick Start

Seed the entire database with all sample data:

    python manage.py seed_database --clear

This will:
1. Delete all existing inventory data
2. Auto-create a "Default" tenant (if it doesn't exist)
3. Create 3 test users (admin, manager, user) linked to the Default tenant
4. Create 10 product categories (hierarchical) linked to the Default tenant
5. Create 15 products across categories linked to the Default tenant
6. Create 17 stock locations (warehouse with aisles, shelves, bins) linked to the Default tenant
7. Create 19 stock records (linking products to locations) linked to the Default tenant
8. Create 10 stock movements (receives, issues, transfers, adjustments) linked to the Default tenant

**All seeded data is now tenant-scoped** — no orphaned data without tenant context.

---

## Tenant-Scoped Seeding

### Overview

All inventory data (categories, products, stock locations, stock records, and movements) is now **automatically linked to a tenant**. This enforces multi-tenancy at the database level and prevents orphaned data.

**Key Benefits:**
- ✅ **No Orphaned Data** — Every seeded object has a tenant assigned
- ✅ **Multi-Tenant Safe** — Seed data for multiple tenants independently
- ✅ **Automatic Context** — Tenant context is managed automatically during seeding
- ✅ **Isolation** — Each tenant's data is isolated and queried separately

### Default Tenant Behavior

By default, seeding uses the **"Default" tenant** (slug: `default`):

- If the Default tenant **already exists**, it is reused
- If the Default tenant **doesn't exist**, it is automatically created (with `--create-default` flag)
- All seeded data is linked to this tenant

### CLI Usage Examples

#### 1. Seed with Default Tenant (Auto-Create)
```bash
# Create default tenant if needed, then seed all data
python manage.py seed_database --clear --create-default
```

#### 2. Seed with Existing Tenant
```bash
# Use existing "acme-corp" tenant (fails if doesn't exist)
python manage.py seed_database --clear --tenant=acme-corp
```

#### 3. Seed Multiple Tenants
```bash
# Seed the Default tenant
python manage.py seed_database --clear --create-default

# Create a new tenant separately (using tenants management command)
python manage.py createtenant --name="ACME Corp" --slug="acme-corp"

# Seed the same data for ACME tenant
python manage.py seed_database --clear --tenant=acme-corp
```

#### 4. Seed Only Specific Models
```bash
# Seed only categories and products to an existing tenant
python manage.py seed_database --models categories,products --tenant=acme-corp
```

#### 5. Seed Without Clearing
```bash
# Add to existing data without removing (soft seed)
python manage.py seed_database --tenant=acme-corp
```

### Programmatic Usage with Tenants

Use SeederManager directly in scripts or tests:

```python
from inventory.seeders import SeederManager
from tenants.models import Tenant
from tenants.context import set_current_tenant

# Get or create a tenant
tenant, created = Tenant.objects.get_or_create(
    slug="acme-corp",
    defaults={"name": "ACME Corp", "is_active": True}
)

# Set tenant context (required for proper audit logging)
set_current_tenant(tenant)

try:
    # Seed everything for this tenant
    manager = SeederManager(verbose=True, clear_data=True)
    manager.seed(tenant=tenant)
finally:
    # Always clear context after seeding
    set_current_tenant(None)
```

### Understanding Tenant Context

During seeding:

1. **Tenant is set** via `set_current_tenant(tenant)` in the management command
2. **All seeders access** `self.tenant` from `BaseSeeder`
3. **Data is created** with `tenant=self.tenant` automatically
4. **Context is cleared** after seeding completes

See [tenants/context.py](../../tenants/context.py) for thread-local context implementation.

---

## Usage Examples

### Seed Everything (with Default Tenant)
    python manage.py seed_database --clear --create-default

### Seed Everything (using existing tenant)
    python manage.py seed_database --clear --tenant=acme-corp

### Seed Specific Models (with tenant)
Seed only users and categories for Default tenant:
    python manage.py seed_database --clear --create-default --models users,categories

Seed locations for a specific tenant:
    python manage.py seed_database --clear --tenant=acme-corp --models locations

Available models:
- `users`: Test users with tenant memberships
- `categories`: Product categories (hierarchical)
- `products`: Products with details
- `locations`: Stock locations (warehouse structure)
- `records`: Stock records (inventory levels)
- `movements`: Stock movements (audit log)

### Suppress Output
    python manage.py seed_database --quiet

### Seed Without Clearing
By default, seeding preserves existing data (only adds new records).
To clear first, use `--clear`:

    python manage.py seed_database --clear
    python manage.py seed_database --clear --models products

## Architecture

### File Structure
```
inventory/seeders/
├── __init__.py                 # Module exports
├── base.py                     # BaseSeeder abstract class
├── tenant_seeder.py            # TenantSeeder (tenant management)
├── user_seeder.py              # UserSeeder (test users)
├── category_seeder.py          # CategorySeeder
├── product_seeder.py           # ProductSeeder
├── stock_location_seeder.py    # StockLocationSeeder
├── stock_record_seeder.py      # StockRecordSeeder
├── stock_movement_seeder.py    # StockMovementSeeder
├── low_stock_seeder.py         # LowStockSeeder
└── seeder_manager.py           # SeederManager orchestrator

inventory/management/commands/
└── seed_database.py            # Django management command (tenant-aware)
```

### Seeder Classes

Each seeder extends `BaseSeeder` and implements the `execute()` method:

**BaseSeeder** (`base.py`)
- Abstract base class providing common interface
- **Signature:** `execute(tenant=None)` — accepts tenant parameter
- Stores `self.tenant` as instance variable for all child seeders
- Provides helper methods:
  - `create_with_tenant(model, **kwargs)` — creates model with tenant assigned
  - `add_root_with_tenant(model, **kwargs)` — creates treebeard root with tenant
- Handles transaction wrapping for atomicity
- Provides `log()` utility for verbose output
- **Important:** Raises error if `self.tenant` is None in helpers (tenant required)

**TenantSeeder** (`tenant_seeder.py`) — **NEW**
- Manages default tenant during seeding
- **Creates:** A "Default" tenant (slug: `default`) if missing
- **Returns:** Tenant instance for downstream seeders
- **Idempotent:** Returns existing tenant if already present
- **Used by:** SeederManager to initialize tenant context
- **Note:** Typically run automatically; not called directly

**UserSeeder** (`user_seeder.py`) — **NEW**
- Creates test users and assigns them to the tenant
- **Creates:** 3 test users with different roles:
  - `admin` / `admin123` — Superuser (ADMIN role)
  - `manager` / `manager123` — Staff user (EDITOR role)
  - `user` / `user123` — Regular user (VIEWER role)
- **Tenant-Aware:** Uses `TenantMembership` to link users to tenant with appropriate roles
- **Idempotent:** Returns existing users if already present
- **Depends on:** Tenant must exist
- **Used by:** SeederManager (runs after TenantSeeder)

**CategorySeeder** (`category_seeder.py`)
- Creates a realistic product category hierarchy
- **Data:**
  - 3 root categories: Electronics, Furniture, Office Supplies
  - 8 nested categories under roots
- **Tenant-Aware:** Uses `self.add_root_with_tenant()` to create categories linked to tenant
- **Depends on:** Nothing (executes after UserSeeder)
- **Used by:** ProductSeeder

**ProductSeeder** (`product_seeder.py`)
- Creates 15 products across categories
- **Tenant-Aware:** Uses `self.create_with_tenant()` to create products linked to tenant
- **Depends on:** Categories must exist and be linked to same tenant
- **Used by:** StockRecordSeeder, StockMovementSeeder

**StockLocationSeeder** (`stock_location_seeder.py`)
- Creates a realistic warehouse structure
- **Tenant-Aware:** Uses `self.add_root_with_tenant()` for location hierarchy linked to tenant
- **Depends on:** Nothing
- **Used by:** StockRecordSeeder, StockMovementSeeder

**StockRecordSeeder** (`stock_record_seeder.py`)
- Creates stock-location associations with quantities
- **Tenant-Aware:** Uses `self.create_with_tenant()` for records linked to tenant
- **Data:** 19 stock records distributed across warehouse
- **Depends on:** Products and Locations (all linked to same tenant)
- **Used by:** Nothing (terminal node)

**StockMovementSeeder** (`stock_movement_seeder.py`)
- Creates realistic movement history
- **Tenant-Aware:** Uses `self.create_with_tenant()` for movements linked to tenant
- **Data:**
  - 4 Receives (inbound stock)
  - 2 Issues (outbound/sales)
  - 2 Transfers (internal repositioning)
  - 2 Adjustments (inventory corrections)
- **Depends on:** Products and Locations (all linked to same tenant)
- **Used by:** Nothing (terminal node)

**LowStockSeeder** (`low_stock_seeder.py`) — Optional
- Creates low-stock scenarios for testing alerts
- **Tenant-Aware:** Uses `self.create_with_tenant()` for scenarios linked to tenant
- **Depends on:** Products and StockRecords (all linked to same tenant)
- **Used by:** Nothing (terminal node)

**SeederManager** (`seeder_manager.py`)
- Orchestrates all seeders in dependency order
- **Tenant-Aware:**
  - Runs `TenantSeeder` first (ensures tenant exists)
  - Captures returned tenant instance
  - Passes `tenant` parameter to all downstream `seeder.execute(tenant=tenant)` calls
  - Supports optional `--tenant` flag from CLI
- Handles selective seeding (individual models)
- Manages data clearing
- **Execution order:** TenantSeeder → Users → Categories → Products → Locations → Records → Movements → (LowStock)

### Programmatic Usage

Import and use SeederManager directly in scripts or tests:

```python
from inventory.seeders import SeederManager
from tenants.models import Tenant

# Option 1: Seed with default tenant (auto-creates if missing)
manager = SeederManager(verbose=True, clear_data=True)
manager.seed()  # Uses "Default" tenant automatically

# Option 2: Seed specific tenant
tenant = Tenant.objects.get(slug="acme-corp")
manager = SeederManager(verbose=True, clear_data=True)
manager.seed(tenant=tenant)

# Option 3: Seed specific models for a tenant
tenant = Tenant.objects.get(slug="acme-corp")
manager = SeederManager(verbose=True)
manager.seed_categories_only(tenant=tenant)
manager.seed_products_only(tenant=tenant)

# Option 4: Seed silently
manager = SeederManager(verbose=False)
manager.seed()
```

**Important:** Always pass `tenant` parameter if you want to control which tenant the data is seeded to. If omitted, the command will use the Default tenant.

## Sample Data

### Test Users
- **admin** (password: `admin123`)
  - Superuser with ADMIN role in Default tenant
  - Full access to all features
- **manager** (password: `manager123`)
  - Staff user with EDITOR role in Default tenant
  - Can create and modify inventory data
- **user** (password: `user123`)
  - Regular user with VIEWER role in Default tenant
  - Read-only access to inventory data

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
- **High-value items:** iPhones, MacBooks, Samsung Galaxy, Dell XPS
- **Medium-value items:** Desks, Chairs
- **Low-value items:** Cables, Mice, Pens, Paper

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

## Best Practices

### Development
```bash
# Fresh start with complete dataset (uses Default tenant)
python manage.py seed_database --clear --create-default

# Login with test users
# Admin: admin / admin123
# Manager: manager / manager123
# User: user / user123

# Add products to existing categories (same tenant)
python manage.py seed_database --models products --tenant=acme-corp

# Seed for a different tenant
python manage.py seed_database --clear --tenant=other-tenant
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

### Testing
```python
# In test setup
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

### Customization
Extend seeders for project-specific data:

```python
from inventory.seeders import ProductSeeder
from inventory.models import Category

class CustomProductSeeder(ProductSeeder):
    def execute(self, tenant=None):
        # Call parent to set tenant context
        self.tenant = tenant
        
        # Your custom logic
        category = Category.objects.filter(tenant=tenant).first()
        product = self.create_with_tenant(
            Category,
            sku="CUSTOM-001",
            name="My Product",
            category=category,
            # tenant is added automatically by create_with_tenant
        )
        self.log(f"Created: {product.name}")
```

## Atomicity & Rollback

All seeders are wrapped in transactions:
- If any seeder fails, all changes are rolled back
- Errors include full validation messages
- Useful for development: errors don't leave partial data
- **Tenant context is preserved** during transaction rollback

Example:
```bash
$ python manage.py seed_database --tenant=acme-corp
# If product creation fails during seeding, all categories linked to acme-corp are rolled back
# Other tenants' data is unaffected
```

## Removing Seed Data

### Clear All Data for a Tenant
Clear only seeded data for a specific tenant:
```python
from inventory.models import Product, Category, StockLocation, StockRecord, StockMovement
from tenants.models import Tenant

tenant = Tenant.objects.get(slug="acme-corp")
Product.objects.filter(tenant=tenant).delete()
Category.objects.filter(tenant=tenant).delete()
StockLocation.objects.filter(tenant=tenant).delete()
StockRecord.objects.filter(tenant=tenant).delete()
StockMovement.objects.filter(tenant=tenant).delete()
```

### Re-Seed with --Clear Flag
Use `--clear` flag to remove all tenant data before seeding:
```bash
# Clear and reseed Default tenant
python manage.py seed_database --clear --create-default

# Clear and reseed specific tenant
python manage.py seed_database --clear --tenant=acme-corp
```

### Verify Tenant Data is Isolated
Always check that you're only deleting the intended tenant's data:
```python
from inventory.models import Product
from tenants.models import Tenant

tenant = Tenant.objects.get(slug="acme-corp")
count = Product.objects.filter(tenant=tenant).count()
print(f"Deleting {count} products from {tenant.name}")
Product.objects.filter(tenant=tenant).delete()
```

---

## Troubleshooting

### Issue: "Default tenant does not exist"

**Error:**
```
CommandError: Default tenant does not exist. Use --create-default to auto-create it, 
or use --tenant=<slug> to seed for a specific tenant.
```

**Solution 1: Auto-create Default tenant**
```bash
python manage.py seed_database --clear --create-default
```

**Solution 2: Use an existing tenant**
```bash
# List all available tenants
python manage.py shell
>>> from tenants.models import Tenant
>>> Tenant.objects.values_list('slug', flat=True)
<QuerySet ['acme-corp', 'other-tenant', ...]>

# Seed for an existing tenant
python manage.py seed_database --clear --tenant=acme-corp
```

### Issue: "Tenant with slug 'xyz' not found"

**Error:**
```
CommandError: Tenant with slug 'xyz' not found. Available tenants: acme-corp, ...
```

**Solution:**
```bash
# Create the tenant first
python manage.py createtenant --name="XYZ Corp" --slug="xyz"

# Then seed for it
python manage.py seed_database --clear --tenant=xyz
```

### Issue: Found orphaned data (NULL tenant values)

**Problem:** Existing data without tenant assignment (from old seeding runs)

**Solution:** Run the migration (TS-06) to backfill:
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

### Issue: Seeding to wrong tenant

**Problem:** Data was seeded to the wrong tenant by mistake

**Solution:** Use `--clear` with the correct tenant:
```bash
# Clear and reseed for the correct tenant
python manage.py seed_database --clear --tenant=correct-tenant-slug
```

### Getting Help

1. **Check CLI help:** `python manage.py seed_database --help`
2. **View available tenants:** `python manage.py shell` → `Tenant.objects.all()`
3. **Check seeding status:** Database queries in shell to verify tenant linkage
4. **Review logs:** Seeding output shows which tenant was used and what was created

---

## Tenant Model Reference

For details on the Tenant model, see [tenants/models.py](../../tenants/models.py):

- `name` — Display name (e.g., "Default", "ACME Corp")
- `slug` — URL-safe identifier (e.g., "default", "acme-corp")
- `is_active` — Whether tenant can be seeded or used
- `created_at`, `updated_at` — Timestamps

All inventory data is linked via `ForeignKey(..., on_delete=models.CASCADE)` to ensure data integrity.

---

## Future Enhancements

### Completed ✅
- ✅ **Tenant-Scoped Seeding** — All inventory data now linked to tenant
- ✅ **Multi-Tenant Support** — Seed independent data for multiple tenants
- ✅ **Automatic Tenant Context** — Thread-local tenant context during seeding
- ✅ **CLI Tenant Flags** — `--tenant` and `--create-default` options

### Planned for Future Phases
- Create purchase orders and invoices during seeding
- Generate multiple datasets (realistic vs. stress test)
- Seed historical data spanning months/years
- Add factories for test-case specific data
- Performance optimization for large-scale multi-tenant seeding
- Async seeding for complex warehouses
- Seed additional test users with custom roles and permissions
