"""Inventory App Seeder Documentation

This module provides a comprehensive seeding system for populating the inventory
database with realistic sample data for development and testing.

## Quick Start

Seed the entire database with all sample data:

    python manage.py seed_database --clear

This will:
1. Delete all existing inventory data
2. Create 10 product categories (hierarchical)
3. Create 15 products across categories
4. Create 17 stock locations (warehouse with aisles, shelves, bins)
5. Create 19 stock records (linking products to locations)
6. Create 10 stock movements (receives, issues, transfers, adjustments)

## Usage Examples

### Seed Everything
    python manage.py seed_database --clear

### Seed Specific Models
Seed only categories:
    python manage.py seed_database --clear --models categories

Seed multiple models:
    python manage.py seed_database --clear --models categories,products,locations

Available models:
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
├── category_seeder.py          # CategorySeeder
├── product_seeder.py           # ProductSeeder
├── stock_location_seeder.py    # StockLocationSeeder
├── stock_record_seeder.py      # StockRecordSeeder
├── stock_movement_seeder.py    # StockMovementSeeder
└── seeder_manager.py           # SeederManager orchestrator

inventory/management/commands/
└── seed_database.py            # Django management command
```

### Seeder Classes

Each seeder extends `BaseSeeder` and implements the `seed()` method:

**BaseSeeder** (`base.py`)
- Abstract base class providing common interface
- Handles transaction wrapping for atomicity
- Provides `log()` utility for verbose output
- Subclasses must implement `seed()`

**CategorySeeder** (`category_seeder.py`)
- Creates a realistic product category hierarchy
- **Data:**
  - 3 root categories: Electronics, Furniture, Office Supplies
  - 8 nested categories under roots (Phones, Laptops, Accessories, Desks, Chairs, Pens, Paper)
- **Depends on:** Nothing
- **Used by:** ProductSeeder

**ProductSeeder** (`product_seeder.py`)
- Creates 15 products across categories
- **Data:**
  - Electronics: iPhones, Samsung, MacBooks, Dell, Accessories
  - Furniture: Desks, Chairs
  - Office: Pens, Paper, Notebooks
  - Each product has: SKU, name, description, unit cost, reorder point
- **Depends on:** Categories must exist
- **Used by:** StockRecordSeeder, StockMovementSeeder

**StockLocationSeeder** (`stock_location_seeder.py`)
- Creates a realistic warehouse structure
- **Data:**
  - Main Warehouse (root)
    - Aisles A, B, C
      - Shelves (A1, A2, A3, B1, B2, C1, C2)
        - Bins (A1-1, A1-2, A2-1, A2-2)
  - Secondary Warehouse (root)
    - Overflow Section
- **Depends on:** Nothing
- **Used by:** StockRecordSeeder, StockMovementSeeder

**StockRecordSeeder** (`stock_record_seeder.py`)
- Creates stock-location associations with quantities
- **Data:** 19 stock records distributed across warehouse
- **Depends on:** Products and Locations must exist
- **Used by:** Nothing (terminal node)

**StockMovementSeeder** (`stock_movement_seeder.py`)
- Creates realistic movement history
- **Data:**
  - 4 Receives (inbound stock)
  - 2 Issues (outbound/sales)
  - 2 Transfers (internal repositioning)
  - 2 Adjustments (inventory corrections)
- **Depends on:** Products and Locations must exist
- **Used by:** Nothing (terminal node)

**SeederManager** (`seeder_manager.py`)
- Orchestrates all seeders in dependency order
- Handles selective seeding (individual models)
- Manages data clearing
- **Execution order:** Categories → Products → Locations → Records → Movements

### Programmatic Usage

Import and use SeederManager directly in scripts or tests:

```python
from inventory.seeders import SeederManager

# Seed everything, clearing first
manager = SeederManager(verbose=True, clear_data=True)
manager.seed()

# Seed specific models
manager = SeederManager(verbose=True)
manager.seed_categories_only()
manager.seed_products_only()

# Seed silently
manager = SeederManager(verbose=False)
manager.seed()
```

## Sample Data

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
# Fresh start with complete dataset
python manage.py seed_database --clear

# Add products to existing categories
python manage.py seed_database --models products
```

### Testing
```python
# In test setup
from inventory.seeders import SeederManager

class MyTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        SeederManager(verbose=False, clear_data=True).seed()
```

### Customization
Extend seeders for project-specific data:

```python
from inventory.seeders import ProductSeeder

class CustomProductSeeder(ProductSeeder):
    def seed(self):
        # Your custom logic
        category = Category.objects.first()
        product = Product.objects.create(
            sku="CUSTOM-001",
            name="My Product",
            category=category,
            ...
        )
        self.log(f"Created: {product.name}")
```

## Atomicity & Rollback

All seeders are wrapped in transactions:
- If any seeder fails, all changes are rolled back
- Errors include full validation messages
- Useful for development: errors don't leave partial data

Example:
```bash
$ python manage.py seed_database
# If product creation fails, all categories are rolled back
```

## Removing Seed Data

Clear only specific models:
```python
from inventory.models import Product
Product.objects.all().delete()
```

Or use `--clear` flag to remove all before seeding:
```bash
python manage.py seed_database --clear
```

## Future Enhancements

Potential improvements:
- Seed users and permissions data
- Create purchase orders and invoices
- Generate multiple datasets (realistic vs. stress test)
- Seed historical data spanning months/years
- Add factories for test-case specific data
