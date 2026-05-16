# Development Guide

This guide is for contributors who want to develop and extend **The Inventory** backend.

---

## Table of Contents

- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Architecture Overview](#architecture-overview)
- [Testing](#testing)
- [Code Standards](#code-standards)
- [Common Development Tasks](#common-development-tasks)
- [Debugging](#debugging)

---

## Development Setup

### Prerequisites

- Python 3.12+
- Git
- PostgreSQL (optional, SQLite for dev)

### Initial Setup

```bash
# Clone repository
git clone https://github.com/Ndevu12/the_inventory.git
cd the_inventory

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Navigate to backend
cd src

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Seed database (optional)
python manage.py seed_database --clear --create-default

# Start development server
python manage.py runserver
```

### Verify Setup

```bash
# Check Django setup
python manage.py check

# Run tests
python manage.py test

# Access admin
# Visit http://localhost:8000/admin/
```

---

## Project Structure

```
src/
├── manage.py                    # Django entry point
├── the_inventory/               # Project configuration
│   ├── settings/
│   │   ├── base.py             # Shared settings
│   │   ├── dev.py              # Development settings
│   │   └── production.py        # Production settings
│   ├── urls.py                 # Root URL configuration
│   ├── wsgi.py                 # WSGI application
│   └── templates/              # Project templates
│
├── api/                         # REST API app
│   ├── views.py                # API viewsets
│   ├── serializers.py          # DRF serializers
│   ├── permissions.py          # Permission classes
│   ├── filters.py              # Filtering logic
│   └── tests/                  # API tests
│
├── inventory/                   # Core inventory app
│   ├── models/                 # Domain models
│   │   ├── base.py             # TimeStampedModel
│   │   ├── product.py          # Product, ProductImage
│   │   ├── category.py         # Category
│   │   └── stock.py            # Stock models
│   ├── services/               # Business logic
│   │   └── stock.py            # StockService
│   ├── admin.py                # Django admin
│   └── tests/                  # Inventory tests
│
├── procurement/                 # Procurement app
├── sales/                       # Sales app
├── reports/                     # Reporting app
├── tenants/                     # Multi-tenancy app
└── locale/                      # Translations

tests/                           # Test suite (repo root)
├── runner.py                   # Custom test runner
├── api/                        # API tests
├── inventory/                  # Inventory tests
└── seeders/                    # Seeder tests
```

---

## Architecture Overview

### Layered Architecture

```
┌─────────────────────────────────────────┐
│         REST API Layer (api/)           │
│  - Viewsets, Serializers, Permissions   │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│      Service Layer (*/services/)        │
│  - Business Logic, Validation           │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│       Model Layer (*/models/)           │
│  - Domain Models, Relationships         │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│         Database (PostgreSQL)           │
└─────────────────────────────────────────┘
```

### Key Design Patterns

**Object-Oriented Programming (OOP)**
- All business logic in classes
- Services encapsulate domain operations
- Models define data structure

**Multi-Tenancy**
- All models inherit from `TimeStampedModel`
- `tenant` FK on all models
- `TenantMiddleware` resolves tenant per request
- `TenantAwareManager` auto-scopes queries

**Immutable Movements**
- Stock movements are immutable (no update/delete)
- Complete audit trail
- Point-in-time cost tracking

---

## Testing

### Run Tests

```bash
cd src

# All tests (seeders excluded)
python manage.py test

# Specific app
python manage.py test tests.api
python manage.py test tests.inventory

# Specific test class
python manage.py test tests.api.test_auth.AuthTestCase

# Specific test method
python manage.py test tests.api.test_auth.AuthTestCase.test_login

# With coverage
coverage run --source='.' manage.py test
coverage report
```

### Write Tests

**Example test:**

```python
from django.test import TestCase
from inventory.models import Product, Category

class ProductTestCase(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name="Electronics",
            slug="electronics"
        )

    def test_create_product(self):
        product = Product.objects.create(
            sku="PROD-001",
            name="Widget",
            category=self.category,
            unit_of_measure="pcs",
            unit_cost=10.00
        )
        self.assertEqual(product.sku, "PROD-001")
        self.assertEqual(product.name, "Widget")

    def test_product_str(self):
        product = Product.objects.create(
            sku="PROD-001",
            name="Widget",
            category=self.category,
            unit_of_measure="pcs",
            unit_cost=10.00
        )
        self.assertEqual(str(product), "Widget (PROD-001)")
```

### Test Organization

- **Unit tests** — Test individual models/functions
- **Integration tests** — Test workflows across services
- **API tests** — Test REST endpoints
- **Seeder tests** — Test database seeding

---

## Code Standards

### Python Style

Follow [PEP 8](https://peps.python.org/pep-0008/):

```bash
# Check code style
ruff check src tests

# Format code
ruff format src tests
```

### Naming Conventions

- **Models:** Singular, PascalCase (`Product`, not `Products`)
- **Functions:** Lowercase with underscores (`get_product_by_sku`)
- **Constants:** UPPERCASE (`MAX_PAGE_SIZE`)
- **Private methods:** Leading underscore (`_validate_quantity`)

### Docstrings

```python
class StockService:
    """Service for managing stock movements and levels."""

    def process_movement(self, movement):
        """
        Process a stock movement and update stock records.

        Args:
            movement: StockMovement instance

        Returns:
            Updated StockRecord

        Raises:
            ValidationError: If movement is invalid
        """
        # Implementation
```

### Imports

Organize imports:

```python
# Standard library
import json
from datetime import datetime

# Third-party
from django.db import models
from rest_framework import serializers

# Local
from inventory.models import Product
from .services import StockService
```

---

## Common Development Tasks

### Add a New Model

1. **Create model** in `app/models/`:

```python
# inventory/models/product.py
class Product(TimeStampedModel):
    sku = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)
    # ... fields
```

2. **Create migration:**

```bash
python manage.py makemigrations
python manage.py migrate
```

3. **Create serializer** in `api/serializers.py`:

```python
class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'sku', 'name', ...]
```

4. **Create viewset** in `api/views.py`:

```python
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
```

5. **Register in URLs** in `api/urls.py`:

```python
router.register(r'products', ProductViewSet)
```

6. **Write tests** in `tests/api/test_products.py`:

```python
class ProductAPITestCase(TestCase):
    def test_list_products(self):
        # Test implementation
```

### Add a New API Endpoint

1. **Create viewset method:**

```python
class ProductViewSet(viewsets.ModelViewSet):
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        product = self.get_object()
        product.is_active = True
        product.save()
        return Response({'status': 'activated'})
```

2. **Test the endpoint:**

```python
def test_activate_product(self):
    response = self.client.post(f'/api/v1/products/{product.id}/activate/')
    self.assertEqual(response.status_code, 200)
```

### Add a New Service Method

1. **Create service method:**

```python
class StockService:
    def get_low_stock_items(self, tenant):
        """Get all items below reorder point."""
        return StockRecord.objects.filter(
            tenant=tenant,
            quantity__lte=F('product__reorder_point')
        )
```

2. **Test the service:**

```python
def test_get_low_stock_items(self):
    items = StockService().get_low_stock_items(self.tenant)
    self.assertEqual(len(items), 1)
```

3. **Use in viewset:**

```python
class StockRecordsViewSet(viewsets.ReadOnlyModelViewSet):
    @action(detail=False)
    def low_stock(self, request):
        items = StockService().get_low_stock_items(request.tenant)
        serializer = self.get_serializer(items, many=True)
        return Response(serializer.data)
```

---

## Debugging

### Django Shell

```bash
python manage.py shell

# Import models
from inventory.models import Product

# Query data
products = Product.objects.all()
product = Product.objects.get(sku='PROD-001')

# Create data
product = Product.objects.create(
    sku='PROD-002',
    name='New Product',
    unit_of_measure='pcs',
    unit_cost=15.00
)

# Update data
product.name = 'Updated Name'
product.save()

# Delete data
product.delete()
```

### Print Debugging

```python
import logging

logger = logging.getLogger(__name__)

def process_movement(self, movement):
    logger.debug(f"Processing movement: {movement.id}")
    logger.info(f"Movement type: {movement.movement_type}")
    logger.error(f"Error processing movement: {error}")
```

### Django Debug Toolbar

Install and configure:

```bash
pip install django-debug-toolbar
```

Add to `settings/dev.py`:

```python
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
INTERNAL_IPS = ['127.0.0.1']
```

Access at: http://localhost:8000/__debug__/

### Breakpoint Debugging

```python
def process_movement(self, movement):
    breakpoint()  # Execution pauses here
    # Use pdb commands: n (next), s (step), c (continue), p (print)
```

---

## Performance Optimization

### Database Queries

Use `select_related()` and `prefetch_related()`:

```python
# Bad: N+1 queries
products = Product.objects.all()
for product in products:
    print(product.category.name)  # Query per product

# Good: Single query
products = Product.objects.select_related('category')
for product in products:
    print(product.category.name)  # No additional queries
```

### Caching

```python
from django.core.cache import cache

def get_products(self):
    cached = cache.get('products_list')
    if cached:
        return cached

    products = Product.objects.all()
    cache.set('products_list', products, 300)  # Cache for 5 minutes
    return products
```

### Indexing

Add database indexes for frequently queried fields:

```python
class Product(models.Model):
    sku = models.CharField(max_length=100, unique=True, db_index=True)
    name = models.CharField(max_length=255, db_index=True)
```

---

## Next Steps

- **Read Architecture:** See [Architecture Guide](architecture.md)
- **Contributing:** See [Contributing Guide](../CONTRIBUTING.md)
- **Testing:** See [Testing Guide](../README.md#testing)
- **Deployment:** See [Deployment Guide](deployment.md)

---

## Need Help?

- 📖 Check [FAQ](faq.md)
- 🐛 See [Troubleshooting Guide](troubleshooting.md)
- 💬 Open an [Issue on GitHub](https://github.com/Ndevu12/the_inventory/issues)
