# Improvement Tasks — Inventory Management for Tenants

This document breaks down the enterprise inventory improvements into **independent, implementable tasks**. Each task can be worked on in isolation, with explicit cross-references to tasks that close remaining gaps.

> **Dependency notation:** `[depends: T-XX]` means the task cannot start until T-XX is merged. `[enhances: T-XX]` means the task builds on T-XX but can be developed in parallel on a feature branch.

---

## Legend

| Tag | Meaning |
|---|---|
| `[MODEL]` | Database model / migration work |
| `[SERVICE]` | Business logic in the service layer |
| `[API]` | REST API endpoints, serializers, permissions |
| `[ADMIN]` | Wagtail admin panels, views, hooks |
| `[TEST]` | Test coverage |
| `[INFRA]` | Cross-cutting infrastructure (middleware, caching, async) |
| `[REPORT]` | Reporting and analytics |

---

## Task Index

| ID | Title | Layer | Depends On | Priority |
|---|---|---|---|---|
| T-01 | Custom exception hierarchy | `[INFRA]` | — | HIGH |
| T-02 | Compliance audit log model | `[MODEL]` | — | HIGH |
| T-03 | Audit log service and middleware | `[SERVICE]` `[INFRA]` | T-02 | HIGH |
| T-04 | StockLot model (batch/lot tracking) | `[MODEL]` | — | HIGH |
| T-05 | StockMovementLot junction model | `[MODEL]` | T-04 | HIGH |
| T-06 | Product tracking mode field | `[MODEL]` | — | MEDIUM |
| T-07 | Lot-aware stock movement processing (FIFO/LIFO) | `[SERVICE]` | T-04, T-05, T-06 | HIGH |
| T-08 | Lot tracking API endpoints | `[API]` | T-04, T-07 | HIGH |
| T-09 | Lot tracking tests | `[TEST]` | T-07, T-08 | HIGH |
| T-10 | StockReservation model | `[MODEL]` | — | HIGH |
| T-11 | ReservationRule model (tenant-level policies) | `[MODEL]` | T-10 | MEDIUM |
| T-12 | Reservation service (create, fulfill, cancel, expire) | `[SERVICE]` | T-10 | HIGH |
| T-13 | Integrate reservations with available quantity | `[SERVICE]` | T-10, T-12 | HIGH |
| T-14 | Reservation API endpoints | `[API]` | T-10, T-12 | HIGH |
| T-15 | Reservation + lot integration | `[SERVICE]` | T-07, T-12 | MEDIUM |
| T-16 | Reservation tests | `[TEST]` | T-12, T-14 | HIGH |
| T-17 | InventoryCycle model (cycle counting) | `[MODEL]` | — | MEDIUM |
| T-18 | CycleCountLine model | `[MODEL]` | T-17 | MEDIUM |
| T-19 | InventoryVariance model | `[MODEL]` | T-17 | MEDIUM |
| T-20 | Cycle counting service | `[SERVICE]` | T-17, T-18, T-19 | MEDIUM |
| T-21 | Cycle counting API endpoints | `[API]` | T-17, T-20 | MEDIUM |
| T-22 | Cycle counting tests | `[TEST]` | T-20, T-21 | MEDIUM |
| T-23 | Warehouse capacity model and enforcement | `[MODEL]` `[SERVICE]` | — | MEDIUM |
| T-24 | Bulk stock operations service | `[SERVICE]` | — | MEDIUM |
| T-25 | Bulk operations API endpoints | `[API]` | T-24 | MEDIUM |
| T-26 | Bulk operations tests | `[TEST]` | T-24, T-25 | MEDIUM |
| T-27 | Enforce tenant subscription limits in API | `[API]` `[INFRA]` | — | HIGH |
| T-28 | Tenant-aware seed data customization | `[INFRA]` | — | LOW |
| T-29 | Tenant access audit trail | `[INFRA]` | T-02, T-03 | MEDIUM |
| T-30 | Audit log API and export endpoints | `[API]` `[REPORT]` | T-02, T-03 | MEDIUM |
| T-31 | Product expiry and lot reports | `[REPORT]` | T-04, T-07 | MEDIUM |
| T-32 | Reservation and availability reports | `[REPORT]` | T-10, T-12 | MEDIUM |
| T-33 | Variance and cycle count reports | `[REPORT]` | T-17, T-20 | MEDIUM |
| T-34 | Dashboard updates for reservations and lots | `[ADMIN]` | T-04, T-10 | LOW |
| T-35 | Async task processing with Celery | `[INFRA]` | — | LOW |
| T-36 | Redis caching for stock records | `[INFRA]` | — | LOW |
| T-37 | Product traceability (GS1) endpoint | `[API]` `[REPORT]` | T-04, T-07 | LOW |

---

## Task Details

---

### T-01: Custom Exception Hierarchy

**Layer:** `[INFRA]`
**Depends on:** None
**Priority:** HIGH
**Estimated effort:** Small (1–2 hours)

**Problem:** The system uses generic `ValidationError` for all error conditions. Callers cannot distinguish between insufficient stock, location hierarchy violations, reservation conflicts, or unknown movement types without parsing error message strings.

**Scope:**

Create `inventory/exceptions.py` with a domain exception hierarchy:

```python
class InventoryError(Exception):
    """Base for all inventory domain errors."""

class InsufficientStockError(InventoryError):
    """Raised when a movement would cause negative stock."""

class LocationHierarchyError(InventoryError):
    """Raised for invalid location tree operations."""

class ReservationConflictError(InventoryError):
    """Raised when reserved stock cannot be allocated."""

class MovementImmutableError(InventoryError):
    """Raised when attempting to update an existing movement."""

class TenantLimitExceededError(InventoryError):
    """Raised when a tenant exceeds subscription limits."""

class LotTrackingRequiredError(InventoryError):
    """Raised when a product requires lot info but none was provided."""
```

**Acceptance criteria:**
- [ ] Exception classes defined in `inventory/exceptions.py`
- [ ] `StockService.process_movement()` raises `InsufficientStockError` instead of `ValidationError` for stock shortage
- [ ] `StockMovement.save()` raises `MovementImmutableError` instead of `ValidationError`
- [ ] API views catch domain exceptions and return appropriate HTTP status codes (409 for conflicts, 422 for validation)
- [ ] Existing tests updated to assert on new exception types
- [ ] Backward-compatible: `InventoryError` inherits from `Exception`, not `ValidationError`, so callers using `except ValidationError` must be updated

**Files to modify:**
- `inventory/exceptions.py` (new)
- `inventory/services/stock.py`
- `inventory/models/stock.py`
- `api/views/inventory.py`

**Closes gap for:** T-07, T-12, T-23, T-27 (all need specific exception types)

---

### T-02: Compliance Audit Log Model

**Layer:** `[MODEL]`
**Depends on:** None
**Priority:** HIGH
**Estimated effort:** Small (2–3 hours)

**Problem:** No structured audit trail exists for compliance (GS1, pharmaceutical, food safety). `StockMovement` tracks stock changes but not user actions like login, tenant switching, bulk operations, or reservation management.

**Scope:**

Create `inventory/models/audit.py`:

```python
class AuditAction(models.TextChoices):
    STOCK_RECEIVED = "stock_received"
    STOCK_ISSUED = "stock_issued"
    STOCK_TRANSFERRED = "stock_transferred"
    STOCK_ADJUSTED = "stock_adjusted"
    RESERVATION_CREATED = "reservation_created"
    RESERVATION_FULFILLED = "reservation_fulfilled"
    RESERVATION_CANCELLED = "reservation_cancelled"
    CYCLE_COUNT_STARTED = "cycle_count_started"
    CYCLE_COUNT_RECONCILED = "cycle_count_reconciled"
    BULK_OPERATION = "bulk_operation"
    TENANT_ACCESSED = "tenant_accessed"

class ComplianceAuditLog(models.Model):
    tenant = models.ForeignKey("tenants.Tenant", ...)
    action = models.CharField(choices=AuditAction.choices, ...)
    product = models.ForeignKey("inventory.Product", null=True, ...)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, ...)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    details = models.JSONField(default=dict, blank=True)
```

**Acceptance criteria:**
- [ ] `ComplianceAuditLog` model with migration
- [ ] Indexed on `tenant`, `action`, `timestamp` for query performance
- [ ] `details` JSONField stores context-specific data (lot numbers, quantities, location names, etc.)
- [ ] No coupling to other new models — the FK to `Product` is optional (some actions are product-independent)
- [ ] Model registered in `inventory/models/__init__.py`

**Files to modify:**
- `inventory/models/audit.py` (new)
- `inventory/models/__init__.py`

**Enables:** T-03 (audit service), T-29 (tenant access audit), T-30 (audit API)

---

### T-03: Audit Log Service and Middleware

**Layer:** `[SERVICE]` `[INFRA]`
**Depends on:** T-02
**Priority:** HIGH
**Estimated effort:** Medium (3–4 hours)

**Problem:** T-02 creates the model but nothing writes to it. Other tasks (T-07, T-12, T-20, T-24) need a consistent way to log audit entries without duplicating code.

**Scope:**

Create `inventory/services/audit.py`:

```python
class AuditService:
    def log(self, *, tenant, action, user, product=None,
            ip_address=None, **details):
        """Create a ComplianceAuditLog entry."""

    def log_from_request(self, request, *, action, product=None, **details):
        """Convenience: extract tenant, user, IP from the request."""
```

Integrate into `StockService.process_movement()` as the first consumer — log every movement with action type, product, quantity, and locations.

**Acceptance criteria:**
- [ ] `AuditService` class in `inventory/services/audit.py`
- [ ] `StockService` calls `AuditService.log()` after successful movement processing
- [ ] IP address extracted from `request.META` when available
- [ ] Unit tests for `AuditService.log()` and `AuditService.log_from_request()`
- [ ] Integration test: processing a stock movement creates both a `StockMovement` and a `ComplianceAuditLog`

**Files to modify:**
- `inventory/services/audit.py` (new)
- `inventory/services/stock.py` (integrate audit logging)

**Enables:** T-29, T-30 (audit API), T-07 (lot audit), T-12 (reservation audit), T-20 (cycle count audit), T-24 (bulk ops audit)

---

### T-04: StockLot Model (Batch/Lot Tracking)

**Layer:** `[MODEL]`
**Depends on:** None
**Priority:** HIGH
**Estimated effort:** Medium (3–4 hours)

**Problem:** The system cannot track batches, serial numbers, or expiry dates. This blocks pharmaceutical, food, and manufacturing use cases. No FIFO/LIFO allocation is possible without lot-level tracking.

**Scope:**

Create `inventory/models/lot.py`:

```python
class StockLot(TimeStampedModel):
    product = models.ForeignKey("inventory.Product", on_delete=models.CASCADE, related_name="lots")
    lot_number = models.CharField(max_length=100, db_index=True)
    serial_number = models.CharField(max_length=100, blank=True)
    manufacturing_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    quantity_received = models.PositiveIntegerField()
    quantity_remaining = models.PositiveIntegerField()
    supplier = models.ForeignKey("procurement.Supplier", null=True, blank=True, on_delete=models.SET_NULL)
    purchase_order = models.ForeignKey("procurement.PurchaseOrder", null=True, blank=True, on_delete=models.SET_NULL)
    received_date = models.DateField()
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["tenant", "product", "lot_number"],
                name="unique_lot_per_product_per_tenant",
            ),
        ]

    def is_expired(self):
        ...

    def days_to_expiry(self):
        ...
```

**Acceptance criteria:**
- [ ] `StockLot` model with migration
- [ ] `lot_number` unique per product per tenant (constraint)
- [ ] `quantity_remaining` tracks unallocated stock in the lot
- [ ] `is_expired()` and `days_to_expiry()` helper methods
- [ ] FKs to `Supplier` and `PurchaseOrder` are optional (lots can be created independently)
- [ ] Registered in `inventory/models/__init__.py`
- [ ] Unit tests for model creation, uniqueness constraint, and helper methods

**Files to modify:**
- `inventory/models/lot.py` (new)
- `inventory/models/__init__.py`

**Enables:** T-05 (junction table), T-07 (lot-aware processing), T-08 (lot API), T-31 (expiry reports), T-37 (traceability)

---

### T-05: StockMovementLot Junction Model

**Layer:** `[MODEL]`
**Depends on:** T-04
**Priority:** HIGH
**Estimated effort:** Small (1–2 hours)

**Problem:** A single stock movement may consume quantities from multiple lots (e.g., issuing 150 units when Lot A has 100 and Lot B has 50). A direct FK from `StockMovement` to `StockLot` cannot represent this split.

**Scope:**

Create the junction table in `inventory/models/lot.py`:

```python
class StockMovementLot(models.Model):
    stock_movement = models.ForeignKey("inventory.StockMovement", on_delete=models.CASCADE, related_name="lot_allocations")
    stock_lot = models.ForeignKey("inventory.StockLot", on_delete=models.PROTECT, related_name="movement_allocations")
    quantity = models.PositiveIntegerField()

    class Meta:
        unique_together = ("stock_movement", "stock_lot")
```

**Acceptance criteria:**
- [ ] `StockMovementLot` model with migration
- [ ] Unique constraint on `(stock_movement, stock_lot)` — one allocation per lot per movement
- [ ] No business logic in this task — that lives in T-07
- [ ] Registered in `inventory/models/__init__.py`

**Files to modify:**
- `inventory/models/lot.py`
- `inventory/models/__init__.py`

**Enables:** T-07 (lot-aware processing uses this to record which lots were consumed)

---

### T-06: Product Tracking Mode Field

**Layer:** `[MODEL]`
**Depends on:** None
**Priority:** MEDIUM
**Estimated effort:** Small (1 hour)

**Problem:** Not all products need lot tracking (e.g., office supplies vs. pharmaceuticals). Without a per-product tracking mode, the system cannot enforce lot requirements selectively.

**Scope:**

Add a `tracking_mode` field to `Product`:

```python
class TrackingMode(models.TextChoices):
    NONE = "none", "No Tracking"
    OPTIONAL = "optional", "Optional Lot Tracking"
    REQUIRED = "required", "Required Lot Tracking"
```

Add `tracking_mode` field to `Product` model with default `NONE` for backward compatibility.

**Acceptance criteria:**
- [ ] `TrackingMode` choices and `tracking_mode` field on `Product`
- [ ] Default value `NONE` — existing products unaffected
- [ ] Migration with `default="none"` (no data migration needed)
- [ ] Field added to Product Wagtail panels under "Stock Management"
- [ ] Field added to `ProductSerializer` in the API
- [ ] Unit test: creating a product defaults to `tracking_mode="none"`

**Files to modify:**
- `inventory/models/product.py`
- `api/serializers/inventory.py`

**Enables:** T-07 (service validates lot info required when `tracking_mode="required"`)

---

### T-07: Lot-Aware Stock Movement Processing (FIFO/LIFO)

**Layer:** `[SERVICE]`
**Depends on:** T-04, T-05, T-06
**Priority:** HIGH
**Estimated effort:** Large (6–8 hours)

**Problem:** `StockService.process_movement()` knows nothing about lots. Receive movements don't create lots, and issue/transfer movements can't allocate from specific lots or use FIFO/LIFO strategies.

**Scope:**

Extend `StockService` with a new method `process_movement_with_lots()` while keeping `process_movement()` backward-compatible:

```python
def process_movement_with_lots(
    self, *,
    product, movement_type, quantity,
    from_location=None, to_location=None,
    lot_number=None, serial_number=None,
    manufacturing_date=None, expiry_date=None,
    allocation_strategy="FIFO",  # or "LIFO", "MANUAL"
    manual_lot_allocations=None,  # list of {lot_id, quantity}
    unit_cost=None, reference="", notes="", created_by=None,
) -> StockMovement:
    ...
```

**Logic by movement type:**
- **RECEIVE:** Create or update `StockLot`, link via `StockMovementLot`
- **ISSUE:** Enforce FIFO (oldest `received_date` first) or LIFO; create `StockMovementLot` entries; decrement `StockLot.quantity_remaining`
- **TRANSFER:** Preserve lot lineage — same lot, different location
- **ADJUSTMENT:** Optionally target specific lot

**Validation:**
- If `product.tracking_mode == "required"` and no lot info provided for RECEIVE, raise `LotTrackingRequiredError` (from T-01)
- If `product.tracking_mode == "none"`, lot info is silently ignored
- FIFO/LIFO: auto-select lots ordered by `received_date` ASC / DESC

**Acceptance criteria:**
- [ ] `process_movement_with_lots()` method on `StockService`
- [ ] RECEIVE creates `StockLot` + `StockMovementLot`
- [ ] ISSUE allocates from lots using FIFO or LIFO, creates multiple `StockMovementLot` entries if needed
- [ ] TRANSFER preserves lot identity
- [ ] `StockLot.quantity_remaining` decremented atomically (`select_for_update`)
- [ ] Original `process_movement()` unchanged (backward-compatible for clients that don't use lots)
- [ ] If T-03 is merged: audit log entries created for lot operations
- [ ] If T-01 is merged: domain-specific exceptions raised

**Files to modify:**
- `inventory/services/stock.py`

**Closes gap for:** Batch/lot tracking (HIGH severity gap from analysis)
**Enables:** T-08 (lot API), T-15 (reservation + lot integration), T-31 (expiry reports), T-37 (traceability)

---

### T-08: Lot Tracking API Endpoints

**Layer:** `[API]`
**Depends on:** T-04, T-07
**Priority:** HIGH
**Estimated effort:** Medium (4–5 hours)

**Problem:** Even with lot models and service logic, external clients (SPA, mobile) have no way to interact with lots via the API.

**Scope:**

1. **StockLotSerializer** — read-only, includes computed `is_expired`, `days_to_expiry`
2. **StockLotViewSet** — list and retrieve only (lots are created via movements, not directly)
3. **Update StockMovementCreateSerializer** — add optional lot fields (`lot_number`, `serial_number`, `manufacturing_date`, `expiry_date`, `allocation_strategy`)
4. **Update StockMovementSerializer** (read) — include nested `lot_allocations`
5. **New endpoint:** `GET /api/v1/products/{id}/lots/` — list all lots for a product
6. **Filter support:** filter lots by `is_active`, `expiry_date__lte` (expiring soon)

**Acceptance criteria:**
- [ ] `StockLotSerializer` and `StockLotViewSet` registered in router
- [ ] `StockMovementCreateSerializer` accepts lot fields, routes to `process_movement_with_lots()`
- [ ] Movements created without lot fields still work (calls original `process_movement()`)
- [ ] Product lots sub-endpoint works with pagination and filtering
- [ ] OpenAPI schema updated (drf-spectacular)
- [ ] API tests for lot creation via receive movement, FIFO issue, and lot listing

**Files to modify:**
- `api/serializers/inventory.py` (or new `api/serializers/lots.py`)
- `api/views/inventory.py` (or new `api/views/lots.py`)
- `api/urls.py`

---

### T-09: Lot Tracking Tests

**Layer:** `[TEST]`
**Depends on:** T-07, T-08
**Priority:** HIGH
**Estimated effort:** Medium (4–5 hours)

**Scope:**

Comprehensive test coverage for the lot tracking feature:

1. **Model tests** (`inventory/tests/test_models/test_lot.py`):
   - StockLot creation, uniqueness constraint, `is_expired()`, `days_to_expiry()`
   - StockMovementLot creation, unique_together constraint

2. **Service tests** (`inventory/tests/test_services/test_stock_service_lots.py`):
   - RECEIVE with lot info creates StockLot + StockMovementLot
   - ISSUE with FIFO allocates oldest lots first
   - ISSUE with LIFO allocates newest lots first
   - ISSUE spanning multiple lots creates multiple StockMovementLot records
   - TRANSFER preserves lot identity
   - Product with `tracking_mode="required"` and no lot info raises error
   - Product with `tracking_mode="none"` ignores lot info
   - Concurrent ISSUE movements don't over-allocate (race condition test)

3. **API tests** (`api/tests/test_lot_api.py`):
   - Create movement with lot info returns lot data
   - List lots for a product, filter by expiry
   - Backward compatibility: movement without lot fields works

**Acceptance criteria:**
- [ ] All tests pass
- [ ] Race condition test uses `select_for_update` verification
- [ ] At least 90% branch coverage on lot-related service code

---

### T-10: StockReservation Model

**Layer:** `[MODEL]`
**Depends on:** None
**Priority:** HIGH
**Estimated effort:** Medium (3–4 hours)

**Problem:** The system has no concept of reserved stock. When a sales order is confirmed, stock is not set aside — another order can consume it, causing over-selling. `StockRecord.quantity` shows total stock, not available stock.

**Scope:**

Create `inventory/models/reservation.py`:

```python
class ReservationStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    CONFIRMED = "confirmed", "Confirmed"
    FULFILLED = "fulfilled", "Fulfilled"
    CANCELLED = "cancelled", "Cancelled"
    EXPIRED = "expired", "Expired"

class StockReservation(TimeStampedModel):
    product = models.ForeignKey("inventory.Product", on_delete=models.CASCADE, related_name="reservations")
    location = models.ForeignKey("inventory.StockLocation", on_delete=models.CASCADE, related_name="reservations")
    quantity = models.PositiveIntegerField()
    sales_order = models.ForeignKey("sales.SalesOrder", null=True, blank=True, on_delete=models.SET_NULL, related_name="reservations")
    reserved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    status = models.CharField(choices=ReservationStatus.choices, default=ReservationStatus.PENDING)
    expires_at = models.DateTimeField(null=True, blank=True)
    fulfilled_movement = models.ForeignKey("inventory.StockMovement", null=True, blank=True, on_delete=models.SET_NULL)
    notes = models.TextField(blank=True)
```

**Acceptance criteria:**
- [ ] `StockReservation` model with migration
- [ ] Status workflow: PENDING -> CONFIRMED -> FULFILLED or CANCELLED or EXPIRED
- [ ] FK to `SalesOrder` is optional (manual reservations allowed)
- [ ] FK to `StockMovement` records which movement fulfilled the reservation
- [ ] `expires_at` enables automatic expiry (processed by T-12)
- [ ] Registered in `inventory/models/__init__.py`
- [ ] Unit tests for model creation and status values

**Files to modify:**
- `inventory/models/reservation.py` (new)
- `inventory/models/__init__.py`

**Enables:** T-11 (rules), T-12 (service), T-13 (available qty), T-14 (API), T-32 (reports)

---

### T-11: ReservationRule Model (Tenant-Level Policies)

**Layer:** `[MODEL]`
**Depends on:** T-10
**Priority:** MEDIUM
**Estimated effort:** Small (2 hours)

**Problem:** Different tenants may want different reservation policies (auto-allocate on order, expiry duration, allocation strategy). Without configurable rules, behavior is hardcoded.

**Scope:**

Add to `inventory/models/reservation.py`:

```python
class ReservationRule(TimeStampedModel):
    name = models.CharField(max_length=255)
    category = models.ForeignKey("inventory.Category", null=True, blank=True, on_delete=models.SET_NULL)
    product = models.ForeignKey("inventory.Product", null=True, blank=True, on_delete=models.SET_NULL)
    auto_reserve_on_order = models.BooleanField(default=False)
    reservation_expiry_hours = models.PositiveIntegerField(default=72)
    allocation_strategy = models.CharField(
        max_length=10,
        choices=[("FIFO", "FIFO"), ("LIFO", "LIFO")],
        default="FIFO",
    )
    is_active = models.BooleanField(default=True)
```

**Acceptance criteria:**
- [ ] `ReservationRule` model with migration
- [ ] Rules can target a specific product, a category, or be tenant-wide (both null)
- [ ] `auto_reserve_on_order` flag for `SalesService` integration (consumed in T-15)
- [ ] Unit tests for rule precedence (product > category > tenant-wide)

**Files to modify:**
- `inventory/models/reservation.py`
- `inventory/models/__init__.py`

**Enables:** T-12 (service uses rules), T-15 (auto-reservation on sales order)

---

### T-12: Reservation Service (Create, Fulfill, Cancel, Expire)

**Layer:** `[SERVICE]`
**Depends on:** T-10
**Priority:** HIGH
**Estimated effort:** Large (6–8 hours)

**Problem:** The reservation model (T-10) stores data but has no business logic. Creating, fulfilling, cancelling, and expiring reservations must enforce stock availability, atomic locking, and state transitions.

**Scope:**

Create `inventory/services/reservation.py`:

```python
class ReservationService:
    def create_reservation(self, *, product, location, quantity,
                           sales_order=None, reserved_by=None,
                           expires_at=None) -> StockReservation:
        """Reserve stock. Validates available quantity (total - already reserved)."""

    def fulfill_reservation(self, reservation, *, created_by=None) -> StockMovement:
        """Convert reservation to an ISSUE movement. Transitions to FULFILLED."""

    def cancel_reservation(self, reservation) -> None:
        """Cancel a PENDING or CONFIRMED reservation. Releases reserved quantity."""

    def expire_stale_reservations(self) -> int:
        """Bulk-expire reservations past their expires_at. Returns count expired.
        Designed to be called by a management command or periodic task."""

    def get_available_quantity(self, product, location) -> int:
        """StockRecord.quantity minus SUM of active reservation quantities."""
```

**Validation:**
- `create_reservation` must lock the `StockRecord` row and check `available_quantity >= requested_quantity`
- `fulfill_reservation` must be PENDING or CONFIRMED; calls `StockService.process_movement()` to create the ISSUE
- `cancel_reservation` only allowed from PENDING or CONFIRMED state
- If T-01 is merged: raise `InsufficientStockError` or `ReservationConflictError`
- If T-03 is merged: create audit log entries

**Acceptance criteria:**
- [ ] `ReservationService` class with all four methods
- [ ] Atomic transactions with `select_for_update` to prevent over-reservation
- [ ] `expire_stale_reservations()` can be called standalone (management command)
- [ ] State transition validation (can't fulfill a cancelled reservation, etc.)
- [ ] Management command `expire_reservations` that calls `expire_stale_reservations()`

**Files to modify:**
- `inventory/services/reservation.py` (new)
- `inventory/management/commands/expire_reservations.py` (new)

**Enables:** T-13 (available qty on StockRecord), T-14 (API), T-15 (lot + reservation integration)

---

### T-13: Integrate Reservations with Available Quantity

**Layer:** `[SERVICE]`
**Depends on:** T-10, T-12
**Priority:** HIGH
**Estimated effort:** Small (2–3 hours)

**Problem:** `StockRecord.quantity` currently represents total stock. With reservations, clients need to know how much is actually available (total minus reserved). The `is_low_stock` property also needs updating.

**Scope:**

1. Add to `StockRecord`:

```python
@property
def reserved_quantity(self):
    return self.product.reservations.filter(
        location=self.location,
        status__in=["pending", "confirmed"],
    ).aggregate(total=Sum("quantity"))["total"] or 0

@property
def available_quantity(self):
    return self.quantity - self.reserved_quantity
```

2. Update `is_low_stock` to use `available_quantity` instead of `quantity`.

3. Update `StockRecordSerializer` to include `reserved_quantity` and `available_quantity`.

4. Update `SalesOrderSerializer` to include a `can_fulfill` computed field.

**Acceptance criteria:**
- [ ] `reserved_quantity` and `available_quantity` properties on `StockRecord`
- [ ] `is_low_stock` uses `available_quantity`
- [ ] API serializers expose the new fields
- [ ] Low-stock report and dashboard updated to use available quantity
- [ ] Unit tests for the computed properties
- [ ] Backward-compatible: without reservations, `available_quantity == quantity`

**Files to modify:**
- `inventory/models/stock.py`
- `api/serializers/inventory.py`
- `reports/services/inventory_reports.py` (low-stock calculation)

**Closes gap for:** Stock Reservations/Allocations (HIGH severity gap from analysis)

---

### T-14: Reservation API Endpoints

**Layer:** `[API]`
**Depends on:** T-10, T-12
**Priority:** HIGH
**Estimated effort:** Medium (4–5 hours)

**Scope:**

1. **StockReservationSerializer** (read) — includes `product`, `location`, `sales_order` details
2. **StockReservationCreateSerializer** — validates inputs, calls `ReservationService`
3. **StockReservationViewSet:**
   - `POST /api/v1/reservations/` — create reservation
   - `GET /api/v1/reservations/` — list reservations (filterable by status, product, location)
   - `GET /api/v1/reservations/{id}/` — retrieve
   - `POST /api/v1/reservations/{id}/fulfill/` — fulfill (custom action)
   - `POST /api/v1/reservations/{id}/cancel/` — cancel (custom action)
4. **New endpoint:** `GET /api/v1/products/{id}/availability/` — returns `{quantity, reserved, available}` per location

**Acceptance criteria:**
- [ ] ViewSet registered in router
- [ ] Create, list, retrieve, fulfill, cancel actions work correctly
- [ ] Product availability endpoint aggregates across locations
- [ ] Permission: managers can create/fulfill/cancel; viewers can list/retrieve
- [ ] OpenAPI schema updated
- [ ] API tests for all actions and permission scenarios

**Files to modify:**
- `api/serializers/reservation.py` (new)
- `api/views/reservation.py` (new)
- `api/urls.py`

---

### T-15: Reservation + Lot Integration

**Layer:** `[SERVICE]`
**Depends on:** T-07, T-12
**Priority:** MEDIUM
**Estimated effort:** Medium (4–5 hours)

**Problem:** T-07 and T-12 are independent — reservations don't know about lots, and lot allocation doesn't consider reservations. For full functionality, fulfilling a reservation should allocate from specific lots using FIFO/LIFO.

**Scope:**

1. Add optional `stock_lot` FK to `StockReservation` (lot-specific reservations)
2. Update `ReservationService.fulfill_reservation()` to call `process_movement_with_lots()` when a lot is specified
3. Update `ReservationService.create_reservation()` to optionally auto-assign a lot based on `ReservationRule.allocation_strategy`
4. Update `SalesService.confirm_order()` to auto-create reservations if `ReservationRule.auto_reserve_on_order` is true

**Acceptance criteria:**
- [ ] Reservations can optionally target a specific lot
- [ ] Fulfillment creates lot-aware movements
- [ ] Auto-reservation on sales order confirmation (when rule enabled)
- [ ] Tests for lot-specific and lot-agnostic reservation flows

**Files to modify:**
- `inventory/models/reservation.py` (add `stock_lot` FK)
- `inventory/services/reservation.py`
- `sales/services/sales.py` (auto-reservation hook)

**Closes gap for:** Full end-to-end lot + reservation flow

---

### T-16: Reservation Tests

**Layer:** `[TEST]`
**Depends on:** T-12, T-14
**Priority:** HIGH
**Estimated effort:** Medium (4–5 hours)

**Scope:**

1. **Model tests:**
   - Reservation creation, status transitions, expiry logic

2. **Service tests:**
   - Create reservation with sufficient stock succeeds
   - Create reservation with insufficient available stock fails
   - Concurrent reservation creation doesn't over-reserve (race condition)
   - Fulfill transitions to FULFILLED and creates ISSUE movement
   - Cancel releases reserved quantity
   - Expire stale reservations bulk operation
   - `get_available_quantity` correctness

3. **API tests:**
   - CRUD operations, custom actions
   - Permission enforcement (viewer cannot create)
   - Product availability endpoint accuracy

4. **Integration tests:**
   - Sales order -> reservation -> fulfillment -> dispatch full flow

**Acceptance criteria:**
- [ ] All tests pass
- [ ] Race condition coverage using `select_for_update`
- [ ] State transition edge cases covered (can't fulfill cancelled, etc.)

---

### T-17: InventoryCycle Model (Cycle Counting)

**Layer:** `[MODEL]`
**Depends on:** None
**Priority:** MEDIUM
**Estimated effort:** Medium (3 hours)

**Problem:** No built-in process exists for physical inventory verification. Warehouse staff cannot record physical counts and compare them against system records.

**Scope:**

Create `inventory/models/cycle.py`:

```python
class CycleStatus(models.TextChoices):
    SCHEDULED = "scheduled", "Scheduled"
    IN_PROGRESS = "in_progress", "In Progress"
    COMPLETED = "completed", "Completed"
    RECONCILED = "reconciled", "Reconciled"

class InventoryCycle(TimeStampedModel):
    name = models.CharField(max_length=255)
    location = models.ForeignKey("inventory.StockLocation", null=True, blank=True, on_delete=models.SET_NULL)
    status = models.CharField(choices=CycleStatus.choices, default=CycleStatus.SCHEDULED)
    scheduled_date = models.DateField()
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    started_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="cycles_started")
    notes = models.TextField(blank=True)
```

**Acceptance criteria:**
- [ ] `InventoryCycle` model with migration
- [ ] Status workflow: SCHEDULED -> IN_PROGRESS -> COMPLETED -> RECONCILED
- [ ] Location is optional (null = full warehouse count)
- [ ] Registered in `inventory/models/__init__.py`
- [ ] Unit tests for model and status values

**Files to modify:**
- `inventory/models/cycle.py` (new)
- `inventory/models/__init__.py`

**Enables:** T-18, T-19, T-20, T-21

---

### T-18: CycleCountLine Model

**Layer:** `[MODEL]`
**Depends on:** T-17
**Priority:** MEDIUM
**Estimated effort:** Small (2 hours)

**Scope:**

Add to `inventory/models/cycle.py`:

```python
class CycleCountLine(TimeStampedModel):
    cycle = models.ForeignKey("inventory.InventoryCycle", on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey("inventory.Product", on_delete=models.PROTECT, related_name="cycle_count_lines")
    location = models.ForeignKey("inventory.StockLocation", on_delete=models.PROTECT)
    system_quantity = models.IntegerField(help_text="System stock at time of count")
    counted_quantity = models.IntegerField(null=True, blank=True, help_text="Physical count")
    counted_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="counts_performed")
    counted_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    @property
    def variance(self):
        if self.counted_quantity is None:
            return None
        return self.counted_quantity - self.system_quantity

    class Meta:
        unique_together = ("cycle", "product", "location")
```

**Acceptance criteria:**
- [ ] `CycleCountLine` with migration
- [ ] `system_quantity` captured at count time (snapshot)
- [ ] `variance` computed property
- [ ] Unique per cycle + product + location
- [ ] Unit tests for variance computation

---

### T-19: InventoryVariance Model

**Layer:** `[MODEL]`
**Depends on:** T-17
**Priority:** MEDIUM
**Estimated effort:** Small (2 hours)

**Scope:**

Add to `inventory/models/cycle.py`:

```python
class VarianceType(models.TextChoices):
    SHORTAGE = "shortage", "Shortage"
    SURPLUS = "surplus", "Surplus"
    MATCH = "match", "Match"

class VarianceResolution(models.TextChoices):
    ACCEPTED = "accepted", "Accepted (Adjustment Created)"
    INVESTIGATING = "investigating", "Under Investigation"
    REJECTED = "rejected", "Rejected (No Change)"

class InventoryVariance(TimeStampedModel):
    cycle = models.ForeignKey("inventory.InventoryCycle", on_delete=models.CASCADE, related_name="variances")
    count_line = models.OneToOneField("inventory.CycleCountLine", on_delete=models.CASCADE, related_name="variance_record")
    product = models.ForeignKey("inventory.Product", on_delete=models.PROTECT)
    location = models.ForeignKey("inventory.StockLocation", on_delete=models.PROTECT)
    variance_type = models.CharField(choices=VarianceType.choices)
    system_quantity = models.IntegerField()
    physical_quantity = models.IntegerField()
    variance_quantity = models.IntegerField()
    resolution = models.CharField(choices=VarianceResolution.choices, null=True, blank=True)
    adjustment_movement = models.ForeignKey("inventory.StockMovement", null=True, blank=True, on_delete=models.SET_NULL)
    resolved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="variances_resolved")
    resolved_at = models.DateTimeField(null=True, blank=True)
    root_cause = models.TextField(blank=True)
```

**Acceptance criteria:**
- [ ] `InventoryVariance` model with migration
- [ ] Linked to `CycleCountLine` (1:1) for traceability
- [ ] `resolution` tracks how each variance was handled
- [ ] `adjustment_movement` links to the corrective `StockMovement` if accepted
- [ ] Unit tests for variance type detection

---

### T-20: Cycle Counting Service

**Layer:** `[SERVICE]`
**Depends on:** T-17, T-18, T-19
**Priority:** MEDIUM
**Estimated effort:** Large (6–8 hours)

**Scope:**

Create `inventory/services/cycle.py`:

```python
class CycleCountService:
    def start_cycle(self, *, name, location=None, scheduled_date, started_by) -> InventoryCycle:
        """Create cycle and pre-populate CycleCountLines with system quantities."""

    def record_count(self, cycle, *, product, location, counted_quantity, counted_by, notes="") -> CycleCountLine:
        """Record a physical count for one product at one location."""

    def complete_cycle(self, cycle) -> None:
        """Mark cycle as COMPLETED. No more counts accepted."""

    def reconcile_cycle(self, cycle, *, resolved_by, resolutions) -> list[InventoryVariance]:
        """Process all variances: ACCEPTED creates adjustment movements, INVESTIGATING flags for review."""

    def get_variance_summary(self, cycle) -> dict:
        """Return counts of shortages, surpluses, and matches."""
```

**Key logic:**
- `start_cycle` snapshots current `StockRecord.quantity` into `CycleCountLine.system_quantity` for all products at the target location
- `reconcile_cycle` creates `StockMovement(movement_type="adjustment")` for each accepted variance
- If T-03 is merged: audit log entries for cycle start, completion, and reconciliation

**Acceptance criteria:**
- [ ] `CycleCountService` with all methods
- [ ] Snapshot isolation: system quantities captured at cycle start
- [ ] Reconciliation creates correct adjustment movements
- [ ] Status transitions enforced (can't record counts on COMPLETED cycle)
- [ ] Unit tests for each method
- [ ] Integration test: full cycle workflow (schedule -> start -> count -> complete -> reconcile)

**Files to modify:**
- `inventory/services/cycle.py` (new)

**Closes gap for:** Cycle Counting Workflow (MEDIUM severity gap from analysis)
**Enables:** T-21 (API), T-33 (reports)

---

### T-21: Cycle Counting API Endpoints

**Layer:** `[API]`
**Depends on:** T-17, T-20
**Priority:** MEDIUM
**Estimated effort:** Medium (4–5 hours)

**Scope:**

1. **InventoryCycleSerializer**, **CycleCountLineSerializer**, **InventoryVarianceSerializer**
2. **InventoryCycleViewSet:**
   - `POST /api/v1/cycles/` — schedule a cycle
   - `GET /api/v1/cycles/` — list cycles (filterable by status, location)
   - `GET /api/v1/cycles/{id}/` — detail with lines
   - `POST /api/v1/cycles/{id}/start/` — start the cycle
   - `POST /api/v1/cycles/{id}/lines/` — record a physical count
   - `POST /api/v1/cycles/{id}/complete/` — mark complete
   - `POST /api/v1/cycles/{id}/reconcile/` — reconcile with resolutions
   - `GET /api/v1/cycles/{id}/variances/` — list variances

**Acceptance criteria:**
- [ ] ViewSet with all custom actions
- [ ] Proper status transition validation in API
- [ ] Permission: managers can create/record/complete; admins can reconcile
- [ ] OpenAPI schema updated
- [ ] API tests

**Files to modify:**
- `api/serializers/cycle.py` (new)
- `api/views/cycle.py` (new)
- `api/urls.py`

---

### T-22: Cycle Counting Tests

**Layer:** `[TEST]`
**Depends on:** T-20, T-21
**Priority:** MEDIUM
**Estimated effort:** Medium (4 hours)

**Scope:**

Full test coverage for the cycle counting feature:
- Model tests (InventoryCycle, CycleCountLine, InventoryVariance)
- Service tests (full workflow, edge cases, concurrent cycles)
- API tests (all endpoints, permissions, error cases)
- Integration test: cycle count that leads to stock adjustment matches updated StockRecord

---

### T-23: Warehouse Capacity Model and Enforcement

**Layer:** `[MODEL]` `[SERVICE]`
**Depends on:** None
**Priority:** MEDIUM
**Estimated effort:** Medium (4–5 hours)

**Problem:** `StockLocation` has no capacity limits. Stock can be received into a location indefinitely, which doesn't reflect physical warehouse constraints.

**Scope:**

1. Add fields to `StockLocation`:

```python
max_capacity = models.PositiveIntegerField(
    null=True, blank=True,
    help_text="Maximum stock units this location can hold. Null = unlimited.",
)
```

2. Add method to `StockLocation`:

```python
@property
def current_utilization(self):
    return self.stock_records.aggregate(total=Sum("quantity"))["total"] or 0

@property
def remaining_capacity(self):
    if self.max_capacity is None:
        return None
    return self.max_capacity - self.current_utilization

def can_accept(self, quantity):
    if self.max_capacity is None:
        return True
    return self.current_utilization + quantity <= self.max_capacity
```

3. Update `StockService._process_receive()` and `_process_transfer()` to check `location.can_accept(quantity)` before incrementing.

4. Update `StockLocationSerializer` to include `max_capacity`, `current_utilization`, `remaining_capacity`.

**Acceptance criteria:**
- [ ] `max_capacity` field on `StockLocation` with migration (nullable for backward compat)
- [ ] Validation in `StockService` prevents exceeding capacity
- [ ] If T-01 is merged: raise custom `LocationCapacityExceededError`
- [ ] API exposes capacity info
- [ ] Existing locations unaffected (null = unlimited)
- [ ] Unit tests for capacity enforcement
- [ ] Wagtail panel updated to include capacity field

**Files to modify:**
- `inventory/models/stock.py`
- `inventory/services/stock.py`
- `api/serializers/inventory.py`

**Closes gap for:** Warehouse Capacity Limits (MEDIUM severity gap from analysis)

---

### T-24: Bulk Stock Operations Service

**Layer:** `[SERVICE]`
**Depends on:** None
**Priority:** MEDIUM
**Estimated effort:** Medium (5–6 hours)

**Problem:** The system only supports single-item operations. Warehouse staff performing inventory audits, warehouse-wide transfers, or bulk price updates must process items one at a time.

**Scope:**

Create `inventory/services/bulk.py`:

```python
class BulkOperationResult:
    success_count: int
    failure_count: int
    errors: list[dict]

class BulkStockService:
    def bulk_transfer(self, *, items, from_location, to_location, created_by) -> BulkOperationResult:
        """Transfer multiple products between locations.
        items = [{"product_id": ..., "quantity": ...}, ...]
        All-or-nothing within a single transaction."""

    def bulk_adjustment(self, *, items, location, created_by, notes="") -> BulkOperationResult:
        """Adjust multiple products at a location.
        items = [{"product_id": ..., "new_quantity": ...}, ...]"""

    def bulk_revalue(self, *, items) -> BulkOperationResult:
        """Update unit costs for multiple products.
        items = [{"product_id": ..., "new_unit_cost": ...}, ...]"""
```

**Key decisions:**
- Each bulk method wraps its operations in `transaction.atomic()` (all-or-nothing)
- Returns a `BulkOperationResult` with success/failure counts and per-item errors
- If T-03 is merged: single "bulk_operation" audit log entry with details JSON listing all items

**Acceptance criteria:**
- [ ] `BulkStockService` class with three methods
- [ ] Atomic transaction per bulk operation
- [ ] Per-item validation (skip invalid items and continue, or fail-all depending on a `fail_fast` parameter)
- [ ] Unit tests for each method, including partial failure scenarios

**Files to modify:**
- `inventory/services/bulk.py` (new)

**Enables:** T-25 (API), T-35 (async for large bulk ops)

---

### T-25: Bulk Operations API Endpoints

**Layer:** `[API]`
**Depends on:** T-24
**Priority:** MEDIUM
**Estimated effort:** Medium (3–4 hours)

**Scope:**

1. **BulkTransferSerializer**, **BulkAdjustmentSerializer**, **BulkRevalueSerializer**
2. **BulkStockOperationViewSet:**
   - `POST /api/v1/bulk-operations/transfer/`
   - `POST /api/v1/bulk-operations/adjust/`
   - `POST /api/v1/bulk-operations/revalue/`
3. Response includes `BulkOperationResult` (success count, failure count, errors)

**Acceptance criteria:**
- [ ] All three endpoints work
- [ ] Permission: managers for transfer/adjust, admins for revalue
- [ ] OpenAPI schema updated
- [ ] API tests for success and validation failure scenarios

**Files to modify:**
- `api/serializers/bulk.py` (new)
- `api/views/bulk.py` (new)
- `api/urls.py`

---

### T-26: Bulk Operations Tests

**Layer:** `[TEST]`
**Depends on:** T-24, T-25
**Priority:** MEDIUM
**Estimated effort:** Small (3 hours)

**Scope:** Unit tests for `BulkStockService`, API tests for all three endpoints, including edge cases (empty list, all items invalid, partial failures).

---

### T-27: Enforce Tenant Subscription Limits in API

**Layer:** `[API]` `[INFRA]`
**Depends on:** None
**Priority:** HIGH
**Estimated effort:** Medium (3–4 hours)

**Problem:** The `Tenant` model defines `max_products` and `max_users` with helper methods `is_within_product_limit()` and `is_within_user_limit()`, but these are never checked in the API layer. A tenant on the Free plan (100 products) can create unlimited products via the API.

**Scope:**

1. Create `tenants/enforcement.py`:

```python
class TenantLimitEnforcement:
    @staticmethod
    def check_product_limit(tenant):
        if not tenant.is_within_product_limit():
            raise TenantLimitExceededError(
                f"Product limit reached ({tenant.max_products}). "
                f"Upgrade your plan to add more products."
            )

    @staticmethod
    def check_user_limit(tenant):
        if not tenant.is_within_user_limit():
            raise TenantLimitExceededError(...)
```

2. Call `check_product_limit()` in `ProductViewSet.perform_create()`.
3. Call `check_user_limit()` in `TenantMemberViewSet` (if member creation exists).
4. Add middleware or mixin that catches `TenantLimitExceededError` and returns HTTP 403 with a clear message.

**Acceptance criteria:**
- [ ] Product creation blocked when limit reached, with clear error message
- [ ] User addition blocked when limit reached
- [ ] HTTP 403 response with `{"detail": "...", "code": "limit_exceeded"}`
- [ ] Existing products/users unaffected (limits only enforced on creation)
- [ ] Tests for limit enforcement and the error response format

**Files to modify:**
- `tenants/enforcement.py` (new)
- `api/views/inventory.py` (product limit check)
- `api/views/tenants.py` (user limit check)

**Closes gap for:** Tenant Limits Not Enforced (from analysis)

---

### T-28: Tenant-Aware Seed Data Customization

**Layer:** `[INFRA]`
**Depends on:** None
**Priority:** LOW
**Estimated effort:** Small (2–3 hours)

**Problem:** The current seeders create fixed data. When a new tenant is provisioned, there's no way to create starter inventory data (default categories, sample products, warehouse structure) specific to that tenant's industry.

**Scope:**

1. Add a `seed_template` field to `Tenant` or create seed templates as JSON fixtures.
2. Create a management command `seed_tenant --tenant=<slug> --template=<name>`.
3. Provide at least two templates: `general` (current seed data) and `empty` (categories only).

**Acceptance criteria:**
- [ ] Management command creates seed data scoped to a specific tenant
- [ ] Templates are pluggable (add new JSON files to add new templates)
- [ ] Existing `seed_database` command unchanged
- [ ] Test for seeding a new tenant

**Files to modify:**
- `inventory/seeders/` (new template files)
- `inventory/management/commands/seed_tenant.py` (new)

---

### T-29: Tenant Access Audit Trail

**Layer:** `[INFRA]`
**Depends on:** T-02, T-03
**Priority:** MEDIUM
**Estimated effort:** Small (2–3 hours)

**Problem:** When a user switches tenants via the `X-Tenant` header, there's no record of which tenant was accessed. This is a compliance concern for multi-tenant systems.

**Scope:**

1. Update `TenantMiddleware` to call `AuditService.log()` with action `TENANT_ACCESSED` when the tenant changes for a user session (or on every API request if compliance requires it).
2. Log tenant slug, user, IP address, and timestamp.
3. Add a configurable flag `AUDIT_TENANT_ACCESS = True/False` in settings to control logging verbosity.

**Acceptance criteria:**
- [ ] Tenant access logged when user switches tenants
- [ ] Configurable: can be turned off for high-traffic systems
- [ ] Test that switching tenants creates an audit log entry

**Files to modify:**
- `tenants/middleware.py`
- `the_inventory/settings/base.py` (add setting)

---

### T-30: Audit Log API and Export Endpoints

**Layer:** `[API]` `[REPORT]`
**Depends on:** T-02, T-03
**Priority:** MEDIUM
**Estimated effort:** Medium (3–4 hours)

**Scope:**

1. **ComplianceAuditLogSerializer** — read-only
2. **ComplianceAuditLogViewSet:**
   - `GET /api/v1/audit-log/` — list with filters (date range, action, product, user)
   - `GET /api/v1/audit-log/?export=csv` — CSV export
3. Permission: admins and owners only

**Acceptance criteria:**
- [ ] List endpoint with pagination and filtering
- [ ] CSV export
- [ ] Admin/owner permission only
- [ ] OpenAPI schema updated
- [ ] API tests

**Files to modify:**
- `api/serializers/audit.py` (new)
- `api/views/audit.py` (new)
- `api/urls.py`

---

### T-31: Product Expiry and Lot Reports

**Layer:** `[REPORT]`
**Depends on:** T-04, T-07
**Priority:** MEDIUM
**Estimated effort:** Medium (3–4 hours)

**Scope:**

1. Add to `InventoryReportService`:
   - `get_expiring_lots(days_ahead=30)` — lots expiring within N days
   - `get_expired_lots()` — lots past expiry date
   - `get_lot_history(product, lot_number)` — all movements for a lot

2. New report view: `/admin/reports/expiry/`
3. New API endpoint: `GET /api/v1/reports/product-expiry/?days_ahead=30`
4. CSV/PDF export

**Acceptance criteria:**
- [ ] Expiry report available in admin and API
- [ ] Filterable by days ahead, product, location
- [ ] Lot history shows full movement chain
- [ ] Tests for report service methods

**Files to modify:**
- `reports/services/inventory_reports.py`
- `reports/views.py`
- `api/views/reports.py`

---

### T-32: Reservation and Availability Reports

**Layer:** `[REPORT]`
**Depends on:** T-10, T-12
**Priority:** MEDIUM
**Estimated effort:** Small (2–3 hours)

**Scope:**

1. Add to `InventoryReportService`:
   - `get_reservation_summary()` — count by status, total reserved quantity
   - `get_availability_report()` — per product: total qty, reserved, available

2. New API endpoint: `GET /api/v1/reports/availability/`
3. Dashboard KPI: "Reserved Stock Value"

**Acceptance criteria:**
- [ ] Availability report shows accurate reserved vs available
- [ ] API endpoint with filtering and export
- [ ] Tests

---

### T-33: Variance and Cycle Count Reports

**Layer:** `[REPORT]`
**Depends on:** T-17, T-20
**Priority:** MEDIUM
**Estimated effort:** Small (2–3 hours)

**Scope:**

1. Add to `InventoryReportService`:
   - `get_variance_report(cycle_id=None)` — all variances, optionally filtered by cycle
   - `get_cycle_history()` — summary of past cycles and their reconciliation status

2. New API endpoint: `GET /api/v1/reports/variances/`

**Acceptance criteria:**
- [ ] Variance report with filtering by cycle, product, variance type
- [ ] CSV/PDF export
- [ ] Tests

---

### T-34: Dashboard Updates for Reservations and Lots

**Layer:** `[ADMIN]`
**Depends on:** T-04, T-10
**Priority:** LOW
**Estimated effort:** Medium (3–4 hours)

**Scope:**

Update existing dashboard panels and API endpoints:

1. **Stock Summary Panel:** Add "Reserved" and "Available" columns
2. **Low Stock Panel:** Use `available_quantity` instead of `quantity`
3. **New Panel:** "Expiring Lots" — lots expiring within 30 days
4. **New Panel:** "Pending Reservations" — count and value
5. **Dashboard API:** Add `/api/v1/dashboard/reservations/` and `/api/v1/dashboard/expiring-lots/`

**Acceptance criteria:**
- [ ] Dashboard shows reservation-aware stock levels
- [ ] Expiring lots panel visible when lot data exists
- [ ] API endpoints return correct data
- [ ] Graceful degradation: panels show normal data when lots/reservations not used

---

### T-35: Async Task Processing with Celery

**Layer:** `[INFRA]`
**Depends on:** None
**Priority:** LOW
**Estimated effort:** Large (6–8 hours)

**Problem:** CSV/Excel imports, PDF generation, bulk operations, and reservation expiry run synchronously. Large operations block the request.

**Scope:**

1. Add `celery` and `redis` to `requirements.txt`
2. Configure Celery in `the_inventory/celery.py`
3. Create async tasks:
   - `tasks.expire_reservations` (periodic, replaces management command from T-12)
   - `tasks.process_bulk_operation` (for large bulk ops from T-24)
   - `tasks.generate_pdf_report` (for large reports)
   - `tasks.process_import` (for large CSV/Excel imports)
4. Add job status tracking model or use Celery result backend
5. API endpoint: `GET /api/v1/jobs/{job_id}/status/`

**Acceptance criteria:**
- [x] Celery configured and documented
- [x] At least one task (reservation expiry) converted to periodic Celery task
- [x] Job status endpoint works
- [x] Fallback: system works without Celery (tasks run synchronously)

**Files to modify:**
- `requirements.txt`
- `the_inventory/celery.py` (new)
- `the_inventory/__init__.py` (Celery app loading)
- `inventory/tasks.py` (new)
- `inventory/models/job.py` (new — AsyncJob tracking model)
- `the_inventory/settings/base.py` (Celery settings)
- `api/views/jobs.py` (new — job status/list views)
- `api/serializers/jobs.py` (new)
- `api/urls.py` (job endpoints)

**Enhances:** T-12, T-24

---

### T-36: Redis Caching for Stock Records

**Layer:** `[INFRA]`
**Depends on:** None
**Priority:** LOW
**Estimated effort:** Medium (4–5 hours)

**Problem:** Stock records are the most frequently queried data (dashboards, availability checks, reports) but have no caching. Every request hits the database.

**Scope:**

1. Add `django-redis` to `requirements.txt`
2. Configure cache backend in settings
3. Cache `StockRecord` queries with smart invalidation:
   - Cache key: `stock:{tenant_id}:{product_id}:{location_id}`
   - Invalidate on: `StockService.process_movement()`, reservation changes
4. Cache dashboard summary data (5-minute TTL)

**Acceptance criteria:**
- [ ] Cache hit/miss measurable via logging
- [ ] Cache invalidated on stock changes
- [ ] Dashboard response time measurably improved
- [ ] Fallback: works without Redis (uses Django's default cache)

---

### T-37: Product Traceability (GS1) Endpoint

**Layer:** `[API]` `[REPORT]`
**Depends on:** T-04, T-07
**Priority:** LOW
**Estimated effort:** Medium (3–4 hours)

**Problem:** For regulatory compliance, some industries need to trace a product batch from receipt through storage to dispatch. No single endpoint provides this chain.

**Scope:**

New endpoint: `GET /api/v1/reports/product-traceability/?product={sku}&lot={lot_number}`

Response:
```json
{
  "product": "...",
  "lot": {
    "lot_number": "...",
    "manufacturing_date": "...",
    "expiry_date": "...",
    "supplier": "..."
  },
  "chain": [
    {"action": "received", "date": "...", "location": "...", "quantity": 100},
    {"action": "transferred", "date": "...", "from": "...", "to": "...", "quantity": 50},
    {"action": "issued", "date": "...", "location": "...", "quantity": 30, "sales_order": "..."}
  ]
}
```

**Acceptance criteria:**
- [ ] Endpoint returns full movement chain for a product + lot
- [ ] Chain ordered chronologically
- [ ] Includes all movement types
- [ ] Tests for traceability with multiple movements

---

## Dependency Graph

```
T-01 (Exceptions) ─────────────────────────────────────────┐
                                                            │
T-02 (Audit Model) ──→ T-03 (Audit Service) ──→ T-29 (Tenant Audit)
                                              ──→ T-30 (Audit API)
                                                            │
T-04 (StockLot) ──→ T-05 (MovementLot) ──┐                │
T-06 (Tracking Mode) ────────────────────┤                │
                                          ├→ T-07 (Lot-Aware Service) ──→ T-08 (Lot API) ──→ T-09 (Lot Tests)
                                          │                                                    │
                                          │                                      T-31 (Expiry Reports)
                                          │                                      T-37 (Traceability)
                                          │
T-10 (Reservation Model) ──→ T-11 (Rules)│
                          ──→ T-12 (Reservation Service) ──→ T-14 (Reservation API) ──→ T-16 (Reservation Tests)
                          ──→ T-13 (Available Qty)                                       │
                                          │                                    T-32 (Reservation Reports)
                                          ├→ T-15 (Lot + Reservation Integration)
                                                            │
T-17 (Cycle Model) ──→ T-18 (CountLine)──┤                │
                    ──→ T-19 (Variance)───┤                │
                                          ├→ T-20 (Cycle Service) ──→ T-21 (Cycle API) ──→ T-22 (Cycle Tests)
                                                                                           │
                                                                              T-33 (Variance Reports)
                                                            │
T-23 (Warehouse Capacity) ─────────────── (independent)    │
T-24 (Bulk Service) ──→ T-25 (Bulk API) ──→ T-26 (Bulk Tests)
T-27 (Tenant Limits) ──────────────────── (independent)    │
T-28 (Tenant Seeding) ────────────────── (independent)     │
T-34 (Dashboard Updates) ──────────────── (depends: T-04, T-10)
T-35 (Celery Async) ──────────────────── (independent, enhances T-12, T-24)
T-36 (Redis Caching) ─────────────────── (independent)
```

## Recommended Execution Order

Tasks can be worked on in parallel within each tier. Complete a tier before starting the next.

### Tier 1 — Foundations (can all start immediately, in parallel)
| Task | Who | Estimated |
|---|---|---|
| T-01 (Exceptions) | Backend | 1–2 hrs |
| T-02 (Audit Model) | Backend | 2–3 hrs |
| T-04 (StockLot Model) | Backend | 3–4 hrs |
| T-06 (Tracking Mode) | Backend | 1 hr |
| T-10 (Reservation Model) | Backend | 3–4 hrs |
| T-17 (Cycle Model) | Backend | 3 hrs |
| T-27 (Tenant Limits) | Backend | 3–4 hrs |

### Tier 2 — Services (after Tier 1 models are merged)
| Task | Who | Estimated |
|---|---|---|
| T-03 (Audit Service) | Backend | 3–4 hrs |
| T-05 (MovementLot) | Backend | 1–2 hrs |
| T-07 (Lot Service) | Backend | 6–8 hrs |
| T-11 (Reservation Rules) | Backend | 2 hrs |
| T-12 (Reservation Service) | Backend | 6–8 hrs |
| T-18 + T-19 (Count Models) | Backend | 4 hrs |
| T-23 (Warehouse Capacity) | Backend | 4–5 hrs |
| T-24 (Bulk Service) | Backend | 5–6 hrs |

### Tier 3 — API + Integration (after Tier 2 services)
| Task | Who | Estimated |
|---|---|---|
| T-08 (Lot API) | Backend | 4–5 hrs |
| T-13 (Available Qty) | Backend | 2–3 hrs |
| T-14 (Reservation API) | Backend | 4–5 hrs |
| T-15 (Lot + Reservation) | Backend | 4–5 hrs |
| T-20 (Cycle Service) | Backend | 6–8 hrs |
| T-25 (Bulk API) | Backend | 3–4 hrs |
| T-29 (Tenant Audit) | Backend | 2–3 hrs |
| T-30 (Audit API) | Backend | 3–4 hrs |

### Tier 4 — Tests, Reports, Polish
| Task | Who | Estimated |
|---|---|---|
| T-09 (Lot Tests) | Backend | 4–5 hrs |
| T-16 (Reservation Tests) | Backend | 4–5 hrs |
| T-21 (Cycle API) | Backend | 4–5 hrs |
| T-22 (Cycle Tests) | Backend | 4 hrs |
| T-26 (Bulk Tests) | Backend | 3 hrs |
| T-31 (Expiry Reports) | Backend | 3–4 hrs |
| T-32 (Reservation Reports) | Backend | 2–3 hrs |
| T-33 (Variance Reports) | Backend | 2–3 hrs |
| T-34 (Dashboard) | Full-stack | 3–4 hrs |
| T-37 (Traceability) | Backend | 3–4 hrs |

### Tier 5 — Infrastructure (can start anytime, independent)
| Task | Who | Estimated |
|---|---|---|
| T-28 (Tenant Seeding) | Backend | 2–3 hrs |
| T-35 (Celery) | DevOps/Backend | 6–8 hrs |
| T-36 (Redis Caching) | DevOps/Backend | 4–5 hrs |

---

## Total Estimate

| Tier | Tasks | Estimated Hours |
|---|---|---|
| Tier 1 (Foundations) | 7 tasks | 16–21 hrs |
| Tier 2 (Services) | 8 tasks | 27–35 hrs |
| Tier 3 (API + Integration) | 8 tasks | 29–37 hrs |
| Tier 4 (Tests + Reports) | 11 tasks | 35–44 hrs |
| Tier 5 (Infrastructure) | 3 tasks | 12–16 hrs |
| **Total** | **37 tasks** | **119–153 hrs** |
