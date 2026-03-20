# Project Tasks

> Tasks are independent unless noted in the **Depends On** column.
> All tasks are part of the **Tenant-Scoping Security Initiative** to ensure all features properly enforce tenant isolation and prevent cross-tenant data leakage.

---

## Tenant-Scoping Security Tasks (TSS-*)

Fixing tenant-scoping issues across the codebase to ensure all features properly enforce tenant isolation and prevent cross-tenant data leakage.

---

### TSS-01 — Add explicit tenant filtering to InventoryReportService

**Priority:** HIGH | **Depends On:** None | **Parallel:** Yes

**Problem:**
The `InventoryReportService` queries Product, StockMovement, StockReservation, and other models without explicit tenant filtering. While these models inherit from `TenantAwareModel` and should auto-filter via the manager, the service doesn't explicitly set tenant context. This could lead to cross-tenant data leakage if tenant context is not properly set in the request middleware.

**Scope:**

| Capability | Description |
| ---------- | ----------- |
| Explicit tenant filtering | Add explicit `.filter(tenant=tenant)` to all querysets |
| Accept tenant parameter | Update all service methods to accept optional `tenant` parameter |
| Fallback to context | Use `get_current_tenant()` if tenant parameter not provided |
| Validation | Raise error if no tenant can be determined |

**Acceptance Criteria:**

- [x] `reports/services/inventory_reports.py` updated
- [x] All methods that query models accept optional `tenant` parameter
- [x] Methods use `get_current_tenant()` as fallback if tenant not provided
- [x] All querysets include explicit `.filter(tenant=tenant)` after model query
- [x] Methods affected: `get_stock_valuation()`, `get_low_stock_products()`, `get_overstock_products()`, `get_movement_history()`, `get_movement_summary()`, `get_reservation_summary()`, `get_availability_report()`, `get_variance_report()`, `get_variance_summary()`, `get_cycle_history()`, `get_expiring_lots()`, `get_expired_lots()`, `get_lot_history()`, `get_product_traceability()`
- [x] Raises `ValueError` if tenant cannot be determined
- [x] Tested: All report methods return only current tenant's data
- [x] Tested: Cross-tenant queries are blocked

**Files to Modify:**
- `reports/services/inventory_reports.py` — Add tenant parameter and filtering

**Implementation Notes:**
- Import `get_current_tenant` from `tenants.context`
- Add tenant parameter to method signatures: `def method_name(self, *, tenant=None, ...)`
- Use pattern: `tenant = tenant or get_current_tenant()` followed by `if not tenant: raise ValueError(...)`

---

### TSS-02 — Add explicit tenant filtering to OrderReportService

**Priority:** HIGH | **Depends On:** None | **Parallel:** Yes

**Problem:**
The `OrderReportService` queries PurchaseOrder and SalesOrder without explicit tenant filtering. While these models inherit from `TenantAwareModel`, the service relies on implicit tenant context filtering which may not be reliable in all scenarios.

**Scope:**

| Capability | Description |
| ---------- | ----------- |
| Explicit tenant filtering | Add explicit `.filter(tenant=tenant)` to all querysets |
| Accept tenant parameter | Update all service methods to accept optional `tenant` parameter |
| Fallback to context | Use `get_current_tenant()` if tenant parameter not provided |
| Validation | Raise error if no tenant can be determined |

**Acceptance Criteria:**

- [ ] `reports/services/order_reports.py` updated
- [ ] All methods that query models accept optional `tenant` parameter
- [ ] Methods use `get_current_tenant()` as fallback if tenant not provided
- [ ] All querysets include explicit `.filter(tenant=tenant)` after model query
- [ ] Methods affected: `get_purchase_summary()`, `get_purchase_totals()`, `get_sales_summary()`, `get_sales_totals()`
- [ ] Raises `ValueError` if tenant cannot be determined
- [ ] Tested: All report methods return only current tenant's data
- [ ] Tested: Cross-tenant queries are blocked

**Files to Modify:**
- `reports/services/order_reports.py` — Add tenant parameter and filtering

**Implementation Notes:**
- Import `get_current_tenant` from `tenants.context`
- Add tenant parameter to method signatures: `def method_name(self, *, tenant=None, ...)`
- Use pattern: `tenant = tenant or get_current_tenant()` followed by `if not tenant: raise ValueError(...)`

---

### TSS-03 — Add explicit tenant verification to Report API views

**Priority:** HIGH | **Depends On:** None | **Parallel:** Yes

**Problem:**
Report API views instantiate `InventoryReportService` and `OrderReportService` without explicitly verifying or setting tenant context. While the middleware should set this, there's no explicit validation that the current tenant matches the authenticated user's tenant.

**Scope:**

| Capability | Description |
| ---------- | ----------- |
| Tenant verification | Add explicit check that user belongs to current tenant |
| Pass tenant to services | Pass tenant parameter to all service method calls |
| Permission checks | Verify user has access to tenant before returning data |

**Acceptance Criteria:**

- [ ] `api/views/reports.py` updated
- [ ] All report view classes add tenant verification in `get()` method
- [ ] Add helper method `_get_current_tenant()` that verifies user belongs to tenant
- [ ] All service method calls pass `tenant=self.tenant` parameter
- [ ] Views affected: `StockValuationView`, `MovementHistoryView`, `LowStockReportView`, `OverstockReportView`, `ReservationSummaryView`, `AvailabilityReportView`, `PurchaseSummaryView`, `SalesSummaryView`, `ProductExpiryView`, `LotHistoryView`, `VarianceReportView`, `CycleHistoryView`, `ProductTraceabilityView`
- [ ] Returns 403 Forbidden if user doesn't belong to tenant
- [ ] Tested: Authenticated user can only access their tenant's reports
- [ ] Tested: Cross-tenant access is blocked with 403

**Files to Modify:**
- `api/views/reports.py` — Add tenant verification and pass to services

**Implementation Notes:**
- Add method: `def _get_current_tenant(self):` that calls `get_current_tenant()` and verifies user membership
- Use `from tenants.context import get_current_tenant`
- Add permission check: verify user is in `tenant.members.all()`

---

### TSS-04 — Add explicit tenant filtering to Wagtail report views

**Priority:** HIGH | **Depends On:** None | **Parallel:** Yes

**Problem:**
Wagtail admin report views (StockValuationView, MovementHistoryView, etc.) don't explicitly filter by tenant. These views are accessible to admin users and could potentially expose data from other tenants if tenant context is not properly set.

**Scope:**

| Capability | Description |
| ---------- | ----------- |
| Explicit tenant filtering | Add explicit `.filter(tenant=tenant)` to all querysets |
| Tenant verification | Verify tenant context is set in get_context_data |
| Permission checks | Add tenant-based permission checks |

**Acceptance Criteria:**

- [x] `reports/views.py` updated
- [x] All report view classes verify tenant context in `get_context_data()`
- [x] All querysets include explicit `.filter(tenant=tenant)` filtering
- [x] Views affected: `StockValuationView`, `MovementHistoryView`, `LowStockReportView`, `OverstockReportView`, `ExpiryReportView`, `PurchaseSummaryView`, `SalesSummaryView`
- [x] Add helper method `_get_current_tenant()` for tenant verification
- [x] Returns error or empty results if tenant context is not set
- [x] Tested: Admin users can only see their tenant's reports
- [x] Tested: Cross-tenant access is blocked

**Files to Modify:**
- `reports/views.py` — Add tenant verification and filtering
- `reports/services/inventory_reports.py` — Add tenant parameter to methods used by views

**Implementation Notes:**
- Add method: `def _get_current_tenant(self):` that calls `get_current_tenant()` and raises error if None
- Use `from tenants.context import get_current_tenant`
- Add to all `get_context_data()` methods: `tenant = self._get_current_tenant()`

---

### TSS-05 — Add explicit tenant filtering to Inventory admin views

**Priority:** HIGH | **Depends On:** None | **Parallel:** Yes

**Problem:**
`LowStockAlertView` and `InventorySearchView` query Product, Category, and StockLocation without explicit tenant filtering. While these models inherit from `TenantAwareModel`, the views should explicitly verify tenant context.

**Scope:**

| Capability | Description |
| ---------- | ----------- |
| Explicit tenant filtering | Add explicit `.filter(tenant=tenant)` to all querysets |
| Tenant verification | Verify tenant context is set in get_queryset |
| Permission checks | Add tenant-based permission checks |

**Acceptance Criteria:**

- [x] `inventory/views.py` updated
- [x] `LowStockAlertView.get_queryset()` includes explicit tenant filtering
- [x] `InventorySearchView.get_context_data()` includes explicit tenant filtering
- [x] Add helper method `_get_current_tenant()` for tenant verification
- [x] All querysets include explicit `.filter(tenant=tenant)` filtering
- [x] Returns error or empty results if tenant context is not set
- [x] Tested: Admin users can only see their tenant's inventory
- [x] Tested: Cross-tenant access is blocked

**Files to Modify:**
- `inventory/views.py` — Add tenant verification and filtering
- `inventory/filters.py` — Add tenant-scoped category/location dropdowns

**Implementation Notes:**
- Add method: `def _get_current_tenant(self):` that calls `get_current_tenant()` and raises PermissionDenied if None
- Use `from tenants.context import get_current_tenant` and `from tenants.permissions import get_membership`
- Update `get_queryset()` and `get_context_data()` methods
- ProductFilterSet accepts `tenant` kwarg to restrict category/location filter choices

---

### TSS-06 — Add explicit tenant verification to Inventory API viewsets

**Priority:** HIGH | **Depends On:** None | **Parallel:** Yes

**Problem:**
`CategoryViewSet`, `ProductViewSet`, `StockLocationViewSet`, and other inventory viewsets rely on implicit tenant filtering via `TenantAwareManager`. While this should work, there's no explicit validation that the user belongs to the tenant being queried.

**Scope:**

| Capability | Description |
| ---------- | ----------- |
| Explicit tenant filtering | Override `get_queryset()` to explicitly filter by current tenant |
| Permission checks | Add permission checks to verify user belongs to tenant |
| Custom actions | Add tenant verification to custom actions (stock, movements, etc.) |

**Acceptance Criteria:**

- [x] `api/views/inventory.py` updated
- [x] All viewsets override `get_queryset()` to explicitly filter by current tenant
- [x] Add helper method `_get_current_tenant()` for tenant verification (`TenantScopedInventoryMixin`)
- [x] All querysets include explicit `.filter(tenant=tenant)` filtering
- [x] Viewsets affected: `CategoryViewSet`, `ProductViewSet`, `StockLocationViewSet`, `StockRecordViewSet`, `StockMovementViewSet`, `StockLotViewSet`
- [x] Custom actions (stock, movements, availability, lots) verify tenant ownership
- [x] Returns 403 Forbidden if user doesn't belong to tenant (or no resolvable tenant)
- [x] Tested: Authenticated user can only access their tenant's data
- [x] Tested: Cross-tenant data access blocked; users without tenant membership get 403

**Files to Modify:**
- `api/views/inventory.py` — Add tenant verification and filtering
- `api/views/reservation.py` — `product_availability_action` explicit tenant filters
- `tenants/middleware.py` — `resolve_tenant_for_request()` for DRF Token auth (middleware runs before DRF auth)

**Implementation Notes:**
- Add method: `def _get_current_tenant(self):` that calls `get_current_tenant()` and raises error if None
- Override `get_queryset()` in each viewset to add explicit filtering
- Use `from tenants.context import get_current_tenant`
- Add tenant checks to custom actions

---

### TSS-07 — Add tenant field to PurchaseOrderLine model

**Priority:** MEDIUM | **Depends On:** None | **Parallel:** Yes

**Problem:**
`PurchaseOrderLine` inherits from `TimeStampedModel` but doesn't have explicit tenant field. While it's related to `PurchaseOrder` which has tenant, there's no direct tenant field on `PurchaseOrderLine`, making it harder to query by tenant directly.

**Scope:**

| Capability | Description |
| ---------- | ----------- |
| Add tenant field | Add explicit `tenant` FK to PurchaseOrderLine |
| Add constraint | Add unique constraint on (tenant, purchase_order, product) |
| Migration | Create migration to backfill tenant from purchase_order |
| Validation | Ensure tenant is set when creating PurchaseOrderLine instances |

**Acceptance Criteria:**

- [x] `procurement/models/order.py` updated
- [x] `PurchaseOrderLine` model adds `tenant` FK field *(via `TimeStampedModel`; documented on the model)*
- [x] Tenant field: `tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, ...)`
- [x] Add unique constraint: `UniqueConstraint(fields=["tenant", "purchase_order", "product"], ...)`
- [x] Migration created to backfill tenant from purchase_order
- [x] Migration file: `procurement/migrations/0004_add_tenant_to_purchaseorderline.py`
- [x] Tested: All PurchaseOrderLine instances have tenant populated
- [x] Tested: Unique constraint prevents duplicate lines per tenant
- [x] Tested: Queries can filter by tenant directly on PurchaseOrderLine

**Files to Create:**
- `procurement/migrations/XXXX_add_tenant_to_purchaseorderline.py` *(new)*

**Files to Modify:**
- `procurement/models/order.py` — Add tenant field and constraint

**Implementation Notes:**
- Use data migration (RunPython) to backfill tenant from related purchase_order
- Add `null=False, blank=False` to tenant field after backfill

---

### TSS-08 — Add tenant field to SalesOrderLine model

**Priority:** MEDIUM | **Depends On:** None | **Parallel:** Yes

**Problem:**
`SalesOrderLine` inherits from `TimeStampedModel` but doesn't have explicit tenant field. While it's related to `SalesOrder` which has tenant, there's no direct tenant field on `SalesOrderLine`.

**Scope:**

| Capability | Description |
| ---------- | ----------- |
| Add tenant field | Add explicit `tenant` FK to SalesOrderLine |
| Add constraint | Add unique constraint on (tenant, sales_order, product) |
| Migration | Create migration to backfill tenant from sales_order |
| Validation | Ensure tenant is set when creating SalesOrderLine instances |

**Acceptance Criteria:**

- [x] `sales/models/order.py` updated
- [x] `SalesOrderLine` model adds `tenant` FK field *(via `TimeStampedModel`, same as `PurchaseOrderLine`)*
- [x] Tenant field: `tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, ...)`
- [x] Add unique constraint: `UniqueConstraint(fields=["tenant", "sales_order", "product"], ...)`
- [x] Migration created to backfill tenant from sales_order
- [x] Migration file: `sales/migrations/XXXX_add_tenant_to_salesorderline.py`
- [x] Tested: All SalesOrderLine instances have tenant populated
- [x] Tested: Unique constraint prevents duplicate lines per tenant
- [x] Tested: Queries can filter by tenant directly on SalesOrderLine

**Files to Create:**
- `sales/migrations/0004_add_tenant_to_salesorderline.py` *(new)*

**Files to Modify:**
- `sales/models/order.py` — Add tenant field and constraint

**Implementation Notes:**
- Use data migration (RunPython) to backfill tenant from related sales_order
- Add `null=False, blank=False` to tenant field after backfill

---

### TSS-09 — Add logging and fallback to TenantAwareManager

**Priority:** MEDIUM | **Depends On:** None | **Parallel:** Yes

**Problem:**
The `TenantAwareManager` in `tenants/managers.py` returns unfiltered querysets when no tenant is set in context. This could lead to data leakage if tenant context is accidentally cleared or not set. There's no explicit validation or warning.

**Scope:**

| Capability | Description |
| ---------- | ----------- |
| Add logging | Log warning when tenant context is None |
| Add fallback | Add explicit tenant parameter to manager methods as fallback |
| Add validation | Optionally raise exception in production when tenant context is missing |

**Acceptance Criteria:**

- [x] `tenants/managers.py` updated
- [x] Add logging import: `import logging`
- [x] Add logger: `logger = logging.getLogger(__name__)`
- [x] Log warning when `get_current_tenant()` returns None: `logger.warning("Querying without tenant context")`
- [x] Add `for_tenant(tenant)` method to explicitly filter by tenant
- [x] Add `unscoped()` method to explicitly bypass tenant filtering (for admin/migrations)
- [x] Add docstring explaining when to use each method
- [x] Tested: Warning logged when tenant context is None
- [x] Tested: `for_tenant(tenant)` filters correctly
- [x] Tested: `unscoped()` returns all records

**Files to Modify:**
- `tenants/managers.py` — Add logging, fallback methods, validation

**Implementation Notes:**
- Use `logger.warning()` for non-critical cases
- Consider `logger.error()` for production environments
- Document when to use `unscoped()` (migrations, management commands only)

---

### TSS-10 — Add tenant verification to ProductViewSet and StockLocationViewSet custom actions

**Priority:** MEDIUM | **Depends On:** None | **Parallel:** Yes

**Problem:**
The `stock()` action in `ProductViewSet` and `StockLocationViewSet` retrieves records without verifying that the product/location belongs to the current tenant. An authenticated user could potentially access data from other tenants.

**Scope:**

| Capability | Description |
| ---------- | ----------- |
| Tenant verification | Add explicit tenant check in custom actions |
| Verify ownership | Verify product/location tenant matches current tenant |
| Add similar checks | Apply to movements(), availability(), and lots() actions |

**Acceptance Criteria:**

- [x] `api/views/inventory.py` updated
- [x] `ProductViewSet.stock()` action verifies `product.tenant == current_tenant`
- [x] `ProductViewSet.movements()` action verifies `product.tenant == current_tenant`
- [x] `ProductViewSet.availability()` action verifies `product.tenant == current_tenant`
- [x] `ProductViewSet.lots()` action verifies `product.tenant == current_tenant`
- [x] `StockLocationViewSet.stock()` action verifies `location.tenant == current_tenant`
- [x] Returns 403 Forbidden if tenant doesn't match
- [x] Tested: User can only access their tenant's product stock data
- [x] Tested: Cross-tenant access is blocked with 403

**Files to Modify:**
- `api/views/inventory.py` — Add tenant verification to custom actions

**Implementation Notes:**
- Add helper method: `def _verify_tenant_ownership(self, obj):` that checks `obj.tenant == get_current_tenant()`
- Raise `PermissionDenied` if tenant doesn't match
- Use `from rest_framework.exceptions import PermissionDenied`

---

## Dependency Graph

```
TSS-01 (InventoryReportService)
TSS-02 (OrderReportService)
TSS-03 (Report API views) ──→ depends on TSS-01, TSS-02
TSS-04 (Wagtail report views)
TSS-05 (Inventory admin views)
TSS-06 (Inventory API viewsets)
TSS-07 (PurchaseOrderLine tenant field)
TSS-08 (SalesOrderLine tenant field)
TSS-09 (TenantAwareManager logging)
TSS-10 (Custom action verification)

All tasks are independent and can be implemented in parallel.
```

---

## Recommended Execution Order

All 10 tasks are **independent** and can be implemented in parallel. However, for logical grouping:

### Group 1 — Service Layer (TSS-01, TSS-02)
- TSS-01: Add explicit tenant filtering to InventoryReportService
- TSS-02: Add explicit tenant filtering to OrderReportService

### Group 2 — API & View Layer (TSS-03, TSS-04, TSS-05, TSS-06, TSS-10)
- TSS-03: Add explicit tenant verification to Report API views
- TSS-04: Add explicit tenant filtering to Wagtail report views
- TSS-05: Add explicit tenant filtering to Inventory admin views
- TSS-06: Add explicit tenant verification to Inventory API viewsets
- TSS-10: Add tenant verification to custom actions

### Group 3 — Model Layer (TSS-07, TSS-08, TSS-09)
- TSS-07: Add tenant field to PurchaseOrderLine model
- TSS-08: Add tenant field to SalesOrderLine model
- TSS-09: Add logging and fallback to TenantAwareManager

---

## Testing Strategy

After implementing each task:

1. Run unit tests for the modified module
2. Run integration tests to verify tenant isolation
3. Run full test suite: `python manage.py test`
4. Manual testing: verify cross-tenant access is blocked

---

## Security Checklist

- [ ] All querysets explicitly filter by tenant
- [ ] All API views verify user belongs to tenant
- [ ] All custom actions verify tenant ownership
- [ ] All models with tenant FK have non-nullable tenant field
- [ ] All migrations backfill tenant data correctly
- [ ] No cross-tenant data leakage in reports
- [ ] No cross-tenant data leakage in API responses
- [ ] Logging captures tenant context for audit trail
