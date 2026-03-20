# Development Guidelines & Patterns

## Code Quality Standards

### Python Backend

**Formatting & Style**
- Use `ruff` for linting and formatting
- Follow PEP 8 conventions
- Line length: 100 characters (ruff default)
- Use type hints throughout (PEP 484)
- Docstrings: Google-style format with examples

**Example Pattern:**
```python
def get_stock_level(product_id: int, location_id: int) -> int:
    """Get current stock level for a product at a location.
    
    Parameters
    ----------
    product_id : int
        The product ID
    location_id : int
        The location ID
        
    Returns
    -------
    int
        Current stock quantity
    """
    # Implementation
```

**Imports Organization**
- Standard library imports first
- Third-party imports second
- Local imports last
- Use `from __future__ import annotations` for forward references

**Example:**
```python
from __future__ import annotations

import logging
from datetime import date
from typing import TYPE_CHECKING, Any

from django.db.models import Count, Sum
from django.utils import timezone

from inventory.models import Product, StockRecord
from tenants.context import get_current_tenant

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractBaseUser
```

### TypeScript/React Frontend

**Component Structure**
- Use `"use client"` directive for client components
- Functional components with hooks
- Props typed with TypeScript interfaces
- Consistent naming: PascalCase for components, camelCase for functions

**Example Pattern:**
```typescript
"use client"

import type { ColumnDef } from "@tanstack/react-table"
import { Badge } from "@/components/ui/badge"
import type { StockValuationItem } from "../types/reports.types"

export function getStockValuationColumns(): ColumnDef<StockValuationItem>[] {
  return [
    {
      accessorKey: "sku",
      header: ({ column }) => <DataTableColumnHeader column={column} title="SKU" />,
      cell: ({ row }) => <span className="font-medium">{row.getValue("sku")}</span>,
    },
  ]
}
```

**Styling**
- Use Tailwind CSS utility classes
- Avoid inline styles
- Use `cn()` utility for conditional classes
- Dark mode support with `dark:` prefix

**Example:**
```typescript
className={cn(
  "fixed inset-0 isolate z-50 bg-black/10 duration-100",
  "supports-backdrop-filter:backdrop-blur-xs",
  "data-open:animate-in data-open:fade-in-0",
  "data-closed:animate-out data-closed:fade-out-0",
  className
)}
```

## Architectural Patterns

### Service Layer Pattern

**Purpose**: Encapsulate business logic separate from models and views

**Structure:**
- Service classes contain business logic
- Methods are focused and single-responsibility
- Use type hints for all parameters and returns
- Include docstrings with usage examples

**Example from codebase:**
```python
class OrderReportService:
    """Read-only reporting on purchase and sales order activity."""
    
    def get_purchase_summary(
        self,
        *,
        period: str = "monthly",
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> list[dict]:
        """Aggregate purchase orders by time period."""
        # Implementation
```

**Key Characteristics:**
- Keyword-only arguments (using `*`) for clarity
- Optional parameters with sensible defaults
- Return types are explicit
- Methods are stateless or minimal state

### Caching Strategy

**Pattern**: Tenant-aware cache keys with smart invalidation

**Key Functions:**
- `cache_get(key)` - Fetch with logging
- `cache_set(key, value, kind)` - Set with TTL
- `invalidate_stock_record(product_id, location_id)` - Single entry
- `invalidate_product_stock(product_id, location_ids)` - Bulk invalidation
- `invalidate_dashboard()` - Dashboard cache wipe

**Example:**
```python
def stock_record_key(product_id: int, location_id: int) -> str:
    """Build stock:{tenant}:{product}:{location}."""
    return f"{STOCK_RECORD_PREFIX}:{_tenant_id()}:{product_id}:{location_id}"

def get_cached_stock_record(product_id: int, location_id: int):
    """Return cached stock-record dict or None."""
    return cache_get(stock_record_key(product_id, location_id))
```

**Characteristics:**
- Tenant-scoped keys for multi-tenancy
- Separate TTLs for different data types (stock: 10min, dashboard: 5min)
- Graceful degradation (works with any cache backend)
- Pattern-based invalidation for bulk operations

### Data Export Pattern

**Pattern**: Structured export with JSON + CSV in ZIP

**Structure:**
- Service class with entity-specific export methods
- Each method returns `(json_rows, csv_rows)` tuple
- Consistent field ordering across formats
- Metadata manifest included

**Example:**
```python
class TenantExportService:
    ENTITY_TYPES = ["categories", "products", "locations", ...]
    
    def _export_categories(self) -> tuple[list[dict], list[list[str]]]:
        """Export categories as JSON-serializable and CSV rows."""
        # Implementation returns (json_data, csv_rows)
    
    def export_to_zip(self) -> io.BytesIO:
        """Build ZIP containing JSON and CSV files."""
        # Orchestrates all exports
```

**Characteristics:**
- Date filtering support
- Decimal/datetime serialization handling
- Flat dict conversion for CSV compatibility
- Manifest file with export metadata

### Tenant Creation Pattern

**Pattern**: Flexible tenant creation with multiple owner assignment options

**Key Function:**
```python
def create_tenant_with_owner(
    *,
    name: str,
    slug: str,
    subscription_plan: str = SubscriptionPlan.FREE,
    owner_user: AbstractBaseUser | None = None,
    owner_username: str | None = None,
    owner_email: str | None = None,
    owner_password: str | None = None,
    send_owner_invitation: bool = False,
    invited_by: AbstractBaseUser | None = None,
) -> tuple[Tenant, TenantInvitation | None]:
    """Create a tenant and optionally assign an owner."""
```

**Characteristics:**
- Atomic transaction for consistency
- Multiple owner resolution paths
- Automatic staff flag assignment
- Returns both tenant and optional invitation
- Comprehensive docstring with resolution logic

## Common Code Idioms

### Tenant Context Management

**Pattern**: Thread-local tenant context for request isolation

```python
from tenants.context import get_current_tenant, set_current_tenant

# In middleware or view
set_current_tenant(tenant)
# ... operations use current tenant
current = get_current_tenant()
```

### QuerySet Filtering

**Pattern**: Automatic tenant filtering via managers

```python
# Models inherit from TenantAwareModel
class Product(TenantAwareModel):
    # Automatically filtered by tenant
    pass

# Usage - automatically scoped
products = Product.objects.all()  # Only current tenant's products
```

### Date Filtering Helper

**Pattern**: Reusable date range filtering

```python
@staticmethod
def _apply_date_filter(qs, field_name, date_from, date_to):
    if date_from:
        qs = qs.filter(**{f"{field_name}__gte": date_from})
    if date_to:
        qs = qs.filter(**{f"{field_name}__lte": date_to})
    return qs
```

### Aggregation with Coalesce

**Pattern**: Safe aggregation with null handling

```python
from django.db.models import Count, Sum, Coalesce, F, DecimalField

qs.annotate(
    total_cost=Coalesce(
        Sum(
            F("lines__quantity") * F("lines__unit_cost"),
            output_field=DecimalField(),
        ),
        0,
        output_field=DecimalField(),
    ),
)
```

### React Column Definition Pattern

**Pattern**: Reusable column definitions for data tables

```typescript
export function getStockValuationColumns(): ColumnDef<StockValuationItem>[] {
  return [
    {
      accessorKey: "sku",
      header: ({ column }) => <DataTableColumnHeader column={column} title="SKU" />,
      cell: ({ row }) => <span className="font-medium">{row.getValue("sku")}</span>,
    },
    {
      accessorKey: "total_value",
      header: ({ column }) => <DataTableColumnHeader column={column} title="Total Value" />,
      cell: ({ row }) => formatCurrency(row.getValue("total_value")),
    },
  ]
}
```

**Characteristics:**
- Exported as functions returning column arrays
- Consistent header/cell structure
- Type-safe with TypeScript generics
- Reusable formatting utilities

### Badge Variant Mapping

**Pattern**: Enum-like mapping for UI variants

```typescript
const MOVEMENT_TYPE_VARIANT: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  receipt: "default",
  issue: "destructive",
  transfer: "secondary",
  adjustment: "outline",
}

// Usage
<Badge variant={MOVEMENT_TYPE_VARIANT[type] ?? "secondary"}>
  {type}
</Badge>
```

## Frequently Used Annotations & Decorators

### Python

**Type Hints**
- `from __future__ import annotations` - Enable postponed evaluation
- `TYPE_CHECKING` - Conditional imports for type hints only
- `Optional[T]` or `T | None` - Nullable types
- `list[dict]` - Generic types (Python 3.9+)

**Django Decorators**
- `@transaction.atomic()` - Database transaction wrapping
- `@staticmethod` - Static methods in service classes
- `@property` - Computed properties on models

### TypeScript/React

**Type Annotations**
- `type ColumnDef<T>` - Generic column definitions
- `Record<string, Type>` - Object type mapping
- `Pick<Type, Keys>` - Partial type selection
- `Omit<Type, Keys>` - Type exclusion

**React Patterns**
- `"use client"` - Client component directive
- `type Props = { ... }` - Component prop types
- `React.ComponentProps<T>` - Extract component props

## Best Practices Summary

### Backend
1. Always use type hints
2. Keep services focused and single-responsibility
3. Use keyword-only arguments for clarity
4. Include comprehensive docstrings with examples
5. Implement proper error handling with custom exceptions
6. Use transactions for multi-step operations
7. Cache strategically with tenant awareness
8. Log at appropriate levels (DEBUG for cache, INFO for operations)

### Frontend
1. Use TypeScript for type safety
2. Keep components small and focused
3. Extract column/helper functions for reusability
4. Use Tailwind for consistent styling
5. Implement proper error boundaries
6. Use custom hooks for shared logic
7. Type all props and return values
8. Use semantic HTML and accessibility attributes

### General
1. Follow the existing code style in the codebase
2. Write tests for new functionality
3. Document complex business logic
4. Use meaningful variable and function names
5. Keep functions small (single responsibility)
6. Avoid deep nesting
7. Use early returns to reduce complexity
8. Comment the "why", not the "what"
