# Project Tasks

> Tasks are independent unless noted in the **Depends On** column.
> All tasks are part of the **Tenant-Scoped Seeding Initiative** to ensure inventory data is always linked to a tenant and prevent orphaned data.

---

## Tenant-Scoped Seeding Tasks (TS-*)

Refactoring the seeder system to automatically create a default tenant and assign all seeded inventory data to it, eliminating orphaned data and enforcing multi-tenancy at the database level.

---

### TS-01 — Create tenant seeder

**Priority:** HIGH | **Depends On:** None

**Problem:**
No mechanism exists to seed a default tenant during initialization. All inventory seeders run
without tenant association, creating orphaned data with `tenant=NULL`.

**Scope:**

| Capability | Description |
| ---------- | ----------- |
| Create seeder class | New `TenantSeeder` inheriting from `BaseSeeder` |
| Default tenant | Create "Default" tenant with slug "default" if missing |
| Idempotency | Return existing tenant if already present (safe to re-run) |
| Instance return | Return tenant instance for downstream seeders to use |

**Acceptance Criteria:**

- [ ] `inventory/seeders/tenant_seeder.py` created with `TenantSeeder` class
- [ ] Inherits from `BaseSeeder` with `execute()` method
- [ ] Creates Tenant: name="Default", slug="default", is_active=True
- [ ] Handles existence check: returns existing tenant if slug="default" already exists
- [ ] Returns Tenant instance for use by other seeders
- [ ] Wrapped in `transaction.atomic()` for safety
- [ ] Tested: `test_tenant_seeder_creates_default_tenant()`, `test_tenant_seeder_returns_existing_on_rerun()`

**Files to Create:**
- `inventory/seeders/tenant_seeder.py` *(new)*

**Files to Modify:**
- `inventory/seeders/base.py` — Document tenant seeder pattern in docstring

**Implementation Notes:**
- Use `Tenant.objects.get_or_create()` with slug="default" to ensure idempotency.

---

### TS-02 — Update base seeder for tenant context

**Priority:** HIGH | **Depends On:** None

**Problem:**
`BaseSeeder` has no mechanism to pass or store tenant context. Child seeders cannot access
the tenant they should seed data into.

**Scope:**

| Capability | Description |
| ---------- | ----------- |
| Accept tenant parameter | `execute(tenant=None)` method signature |
| Store tenant | Instance variable `self.tenant` for all child seeders |
| Helper method | `create_with_tenant(model, **kwargs)` to safely assign tenant |
| Validation | Raise error if tenant is None when required |

**Acceptance Criteria:**

- [ ] `BaseSeeder.execute()` signature updated to accept `tenant` parameter
- [ ] `self.tenant` stored as instance variable in execute
- [ ] Helper method `create_with_tenant(model, **kwargs)` added
- [ ] Helper adds `tenant=self.tenant` to kwargs before calling `model.objects.create()`
- [ ] Separate helper `add_root_with_tenant(model, **kwargs)` for treebeard models (Category, StockLocation)
- [ ] Raises informative error if `self.tenant` is None in helpers
- [ ] All child seeders updated to call parent's helpers instead of direct `.create()` calls
- [ ] Tested: `test_base_seeder_stores_tenant()`, `test_create_with_tenant_helper()`

**Files to Modify:**
- `inventory/seeders/base.py` — Add tenant param, helpers, validation

**Implementation Notes:**
- Child seeders will be updated in TS-04; this task is foundational infrastructure.

---

### TS-03 — Update CLI command for tenant context and set_current_tenant

**Priority:** HIGH | **Depends On:** None

**Problem:**
The management command `seed_database` has no tenant awareness. It doesn't create or accept a tenant,
and doesn't set thread-local tenant context via `set_current_tenant()` from `tenants/context.py`.

**Scope:**

| Capability | Description |
| ---------- | ----------- |
| Add --tenant flag | Optional flag to seed for specific tenant slug (e.g., `--tenant=acme`) |
| Default behavior | Auto-create "Default" tenant if none specified and none exists |
| Set tenant context | Call `set_current_tenant(tenant)` before seeding |
| Error handling | Fail gracefully if tenant slug provided but doesn't exist |
| Output | Print tenant name and seeded data counts |

**Acceptance Criteria:**

- [ ] `inventory/management/commands/seed_database.py` updated
- [ ] Add `--tenant` optional argument to command options
- [ ] Add `--create-default` flag to force auto-create default tenant
- [ ] If no `--tenant` provided: check for "Default" tenant; if missing and `--create-default`, create it
- [ ] If `--tenant` provided: fetch by slug; raise error if not found
- [ ] Call `from tenants.context import set_current_tenant` and invoke before seeding
- [ ] Call `set_current_tenant(None)` after seeding to clear context
- [ ] Output: "Seeding into tenant: {tenant_name} (slug={slug})"
- [ ] Tested: `test_seed_command_creates_default_tenant()`, `test_seed_command_sets_context()`, `test_seed_command_uses_specified_tenant()`

**Files to Modify:**
- `inventory/management/commands/seed_database.py` — Add tenant flags, context, error handling

**Implementation Notes:**
- Reuse logic from `tenants/management/commands/createtenant.py` for tenant creation if possible.
- Ensure `set_current_tenant()` is cleared after seeding to avoid side effects.

---

### TS-04 — Refactor all seeders to use tenant parameter

**Priority:** HIGH | **Depends On:** TS-02

**Problem:**
All individual seeders (`CategorySeeder`, `ProductSeeder`, etc.) create data without tenant
association. They must be refactored to accept and use the tenant from `BaseSeeder`.

**Scope:**

| Capability | Description |
| ---------- | ----------- |
| Update category seeder | Use `add_root_with_tenant()` for Category creation |
| Update product seeder | Use `create_with_tenant()` for Product creation |
| Update location seeder | Use `add_root_with_tenant()` for StockLocation hierarchy |
| Update stock record seeder | Use `create_with_tenant()` for StockRecord creation |
| Update movement seeder | Use `create_with_tenant()` for StockMovement creation |
| Update low-stock seeder | Use `create_with_tenant()` for scenario objects |

**Acceptance Criteria:**

- [ ] `inventory/seeders/category_seeder.py` — Replace `.add_root()` with `self.add_root_with_tenant()`
- [ ] `inventory/seeders/product_seeder.py` — Replace `.create()` with `self.create_with_tenant()`
- [ ] `inventory/seeders/stock_location_seeder.py` — Replace `.add_root()` with `self.add_root_with_tenant()`
- [ ] `inventory/seeders/stock_record_seeder.py` — Replace `.create()` with `self.create_with_tenant()`
- [ ] `inventory/seeders/stock_movement_seeder.py` — Replace `.create()` with `self.create_with_tenant()`
- [ ] `inventory/seeders/low_stock_seeder.py` — Replace `.create()` with `self.create_with_tenant()`
- [ ] All seeders remove inline `tenant=None` or missing tenant assignments (if any)
- [ ] Tested: Run `manage.py seed_database` and verify all seeded objects have `tenant` populated
- [ ] Tested: Verify foreign key relationships work correctly (products link to categories, etc.)

**Files to Modify:**
- `inventory/seeders/category_seeder.py` — Replace `.add_root()` calls
- `inventory/seeders/product_seeder.py` — Replace `.create()` calls
- `inventory/seeders/stock_location_seeder.py` — Replace `.add_root()` calls
- `inventory/seeders/stock_record_seeder.py` — Replace `.create()` calls
- `inventory/seeders/stock_movement_seeder.py` — Replace `.create()` calls
- `inventory/seeders/low_stock_seeder.py` — Replace `.create()` calls

**Implementation Notes:**
- All seeders should already inherit from `BaseSeeder`, so they have access to `self.tenant`.
- This task is straightforward once TS-02 (base seeder) is complete.

---

### TS-05 — Update seeder manager to orchestrate tenant-scoped seeding

**Priority:** HIGH | **Depends On:** TS-01, TS-02, TS-04

**Problem:**
`SeederManager` doesn't handle tenant seeding. It must execute `TenantSeeder` first and pass
the tenant instance to all downstream seeders. It must also support multi-tenant seeding.

**Scope:**

| Capability | Description |
| ---------- | ----------- |
| Tenant seeder first | Run `TenantSeeder` before all other seeders |
| Capture tenant | Store returned tenant instance from `TenantSeeder.execute()` |
| Pass to children | Call `other_seeder.execute(tenant=tenant)` for all seeders |
| Support --tenant flag | Accept optional `tenant` parameter from calling code |
| Maintain order | Keep existing dependency order (Categories → Products, etc.) |

**Acceptance Criteria:**

- [ ] `inventory/seeders/seeder_manager.py` updated
- [ ] Add `TenantSeeder` import at top
- [ ] `run()` method accepts optional `tenant` parameter
- [ ] If `tenant` provided: use it; otherwise invoke `TenantSeeder().execute()` to get/create default
- [ ] Call `tenant_seeder.execute()` first in seeding order
- [ ] Pass `tenant` instance to all subsequent `seeder.execute(tenant=tenant)` calls
- [ ] Maintain existing dependency order after TenantSeeder
- [ ] Return dict with tenant and seeded counts: `{"tenant": tenant, "objects_created": {...}}`
- [ ] Tested: `test_seeder_manager_runs_tenant_seeder_first()`, `test_seeder_manager_passes_tenant()`

**Files to Modify:**
- `inventory/seeders/seeder_manager.py` — Orchestrate tenant seeding

**Implementation Notes:**
- If multi-tenant seeding is desired later (seed once per tenant), this structure supports it.

---

### TS-06 — Create Django migration to backfill and enforce non-nullable tenant

**Priority:** HIGH | **Depends On:** TS-01, TS-04

**Problem:**
Existing inventory data may have `tenant=NULL` (orphaned). The `tenant` field is currently nullable.
A migration is needed to backfill orphaned data and make the field non-nullable to prevent future orphaning.

**Scope:**

| Capability | Description |
| ---------- | ----------- |
| Backfill strategy | Assign orphaned data to "Default" tenant (or delete if deletion is policy) |
| Models affected | Category, Product, StockLocation, StockRecord, StockMovement, StockLot, StockReservation, InventoryCycle |
| Make non-nullable | Set `null=False` on `tenant` FK in `TimeStampedModel` base |
| Cascade fix (if needed) | Update `on_delete=CASCADE` in models to ensure consistency |

**Acceptance Criteria:**

- [ ] Migration file created in `inventory/migrations/` (e.g., `0XXX_backfill_and_enforce_tenant.py`)
- [ ] Migration backfills all NULL tenant entries by assigning to default tenant (or deletes if policy mandates)
- [ ] Migration sets `null=False` on tenant FK in `inventory/models/base.py`
- [ ] Migration is reversible (with rollback logic for non-nullable change)
- [ ] `python manage.py migrate` runs successfully on fresh and existing databases
- [ ] Post-migration, querying `Product.objects.filter(tenant__isnull=True)` returns 0 results
- [ ] Tested: Run migration on test database and verify no data loss

**Files to Create:**
- `inventory/migrations/XXXX_backfill_and_enforce_tenant.py` *(new)*

**Files to Modify:**
- `inventory/models/base.py` — Update `tenant` field: `null=False`

**Implementation Notes:**
- Use data migration (RunPython) if custom logic needed for backfilling.
- Consider adding a default=get_default_tenant function if backfill rejects NULL assignments.

---

### TS-07 — Make tenant field non-nullable in TimeStampedModel

**Priority:** HIGH | **Depends On:** TS-06

**Problem:**
The `tenant` field in `TimeStampedModel` allows NULL, enabling orphaned data. After migration backfill,
the model definition must enforce non-nullable.

**Scope:**

| Capability | Description |
| ---------- | ----------- |
| Update field definition | Set `null=False, blank=False` on tenant FK |
| Add default (optional) | Optionally add a default Callable to get default tenant |
| Update docstring | Clarify that tenant is now required for all inventory data |

**Acceptance Criteria:**

- [ ] `inventory/models/base.py` — `tenant` field updated to `null=False, blank=False`
- [ ] Field definition matches: `tenant = models.ForeignKey(..., null=False, blank=False, on_delete=models.CASCADE, ...)`
- [ ] Docstring updated to reflect tenant requirement
- [ ] Model tests verify non-nullable enforcement
- [ ] Tested: Attempt to create inventory object without tenant → should raise IntegrityError or ValidationError

**Files to Modify:**
- `inventory/models/base.py` — Update tenant field definition

**Implementation Notes:**
- Migration (TS-06) must complete before this code change.
- Consider adding `default=get_default_tenant` if needed for backward compatibility during testing.

---

### TS-08 — Add tenant validation and helper methods to TimeStampedModel

**Priority:** MEDIUM | **Depends On:** TS-07

**Problem:**
No validation or helpers exist to ensure tenant consistency or to simplify tenant-scoped queries.
Developers must manually filter by tenant in each query.

**Scope:**

| Capability | Description |
| ---------- | ----------- |
| Save validation | Override `save()` to validate tenant consistency |
| Manager methods | Add `.filter_by_current_tenant()` to convenience query |
| Tenant audit | Optionally auto-set tenant from thread-local context in edge cases |
| Docstring | Document best practices for tenant-scoped models |

**Acceptance Criteria:**

- [ ] `inventory/models/base.py` — Add `save()` override to validate tenant before save
- [ ] Add custom Manager with `filter_by_current_tenant()` method
- [ ] Override `.save()` to ensure audit fields (`created_by`) respect tenant (if applicable)
- [ ] Add docstring to `TimeStampedModel` explaining tenant requirements
- [ ] Tested: Override `save()` to check that tenant is not None
- [ ] Tested: `Product.objects.filter_by_current_tenant()` returns only current tenant's products

**Files to Modify:**
- `inventory/models/base.py` — Add validation, manager methods, docstring

**Implementation Notes:**
- `filter_by_current_tenant()` should use `get_current_tenant()` from `tenants/context.py`.
- Ensure `save()` doesn't interfere with bulk operations (disable for bulk_create if needed).

---

### TS-09 — Update seeder documentation with tenant-scoping details

**Priority:** MEDIUM | **Depends On:** TS-03, TS-05

**Problem:**
Documentation (README or existing seeder docs) doesn't explain tenant requirements or how to seed
for specific tenants. Developers won't know how to use the system.

**Scope:**

| Capability | Description |
| ---------- | ----------- |
| Update README | Add section on tenant seeding in `inventory/seeders/README.md` or central docs |
| CLI examples | Document `manage.py seed_database --tenant=<slug>` usage |
| Default behavior | Explain "Default" tenant auto-creation |
| Troubleshooting | Section for common issues (existing tenant, NULL data, etc.) |

**Acceptance Criteria:**

- [ ] `inventory/seeders/README.md` (or relevant docs) updated with tenant seeding section
- [ ] Document default behavior: "Runs seeders for 'Default' tenant if not specified"
- [ ] Example: `python manage.py seed_database` (uses Default)
- [ ] Example: `python manage.py seed_database --tenant=acme` (uses ACME tenant)
- [ ] Example: `python manage.py seed_database --clear --tenant=default` (clear and recreate)
- [ ] Troubleshooting: What to do if "Default" tenant already exists
- [ ] Clarify that all seeded data is now tenant-scoped (no orphaned data)
- [ ] Link to `tenants/models.py` for Tenant model overview

**Files to Create/Modify:**
- `inventory/seeders/README.md` — Add tenant section *(or central docs)*
- `docs/ARCHITECTURE.md` — Optional: add multi-tenancy seeding section

**Implementation Notes:**
- Can reference existing architecture docs if they cover multi-tenancy.

---

### TS-10 — Write comprehensive tests for tenant-scoped seeding

**Priority:** HIGH | **Depends On:** TS-01 through TS-08

**Problem:**
No tests verify that seeders respect tenant context or that orphaned data is prevented.
Tests ensure system reliability and prevent regressions.

**Scope:**

| Capability | Description |
| ---------- | ----------- |
| Unit tests | Test each seeder individually with tenant parameter |
| Integration tests | Run full seeding pipeline and verify tenant assignment |
| CLI tests | Test management command with --tenant flag and defaults |
| Database tests | Verify no NULL tenants exist after seeding |
| Constraint tests | Verify unique constraints work with non-nullable tenant |

**Acceptance Criteria:**

- [ ] `inventory/tests/test_seeder_tenant.py` created *(or expanded existing)*
- [ ] `test_tenant_seeder_creates_default()` — TenantSeeder creates Default tenant
- [ ] `test_tenant_seeder_idempotent()` — Re-running returns existing tenant
- [ ] `test_category_seeder_uses_tenant()` — Categories assigned to tenant
- [ ] `test_product_seeder_uses_tenant()` — Products assigned to tenant
- [ ] `test_stock_location_seeder_uses_tenant()` — Locations assigned to tenant
- [ ] `test_stock_record_seeder_uses_tenant()` — Records assigned to tenant
- [ ] `test_stock_movement_seeder_uses_tenant()` — Movements assigned to tenant
- [ ] `test_seeder_manager_full_pipeline()` — Run all seeders via manager
- [ ] `test_seed_command_creates_default_tenant()` — CLI auto-creates Default
- [ ] `test_seed_command_specified_tenant()` — CLI uses --tenant flag
- [ ] `test_seed_command_no_orphaned_data()` — Query Product.objects.filter(tenant__isnull=True) == 0
- [ ] `test_product_unique_constraint_per_tenant()` — SKU unique per tenant enforced
- [ ] All tests pass: `python manage.py test inventory.tests.test_seeder_tenant`

**Files to Create:**
- `inventory/tests/test_seeder_tenant.py` *(new)*

**Files to Modify:**
- `inventory/tests/test_seeder_*.py` — Integrate tenant tests into existing seeder tests (optional)

**Implementation Notes:**
- Use Django's `TransactionTestCase` for tests involving `transaction.atomic()`.
- Mock `set_current_tenant()` and `get_current_tenant()` if testing in isolation.

---

### TS-11 — Verify no regressions in existing systems

**Priority:** MEDIUM | **Depends On:** TS-04, TS-06, TS-07

**Problem:**
Changes to seeders and models might break existing workflows (API serialization, views, exports).
Regression testing ensures the system still works end-to-end.

**Scope:**

| Capability | Description |
| ---------- | ----------- |
| API endpoints | Verify product, category, stock APIs still return correct data |
| Serializers | Check serializers handle tenant FK correctly |
| Views | Ensure inventory views still render and filter by tenant |
| Exports | CSV/PDF exports include tenant context |
| Audit logging | Ensure audit logs track tenant changes |

**Acceptance Criteria:**

- [ ] Run API test suite: `python manage.py test api.tests`
- [ ] All product/category/stock record endpoints return 200, data is tenant-scoped
- [ ] Serializers render tenant field or include it in output
- [ ] Inventory views (UI) still filter and display data correctly
- [ ] Any exports (reports, CSV) include/reference tenant
- [ ] Audit logs record seeding actions with tenant context
- [ ] No new error logs in `python manage.py` or API responses

**Files to Verify (no changes expected):**
- `api/serializers/inventory.py` — Verify tenant in schema
- `api/views/inventory.py` — Verify tenant filtering
- `inventory/views.py` — UI views still work
- `audit/models.py` — Audit logging includes tenant

**Implementation Notes:**
- Run full test suite: `python manage.py test` to catch any regressions.
- Manual testing recommended for UI workflows.

---

## Dependency Graph

```
TS-01 (TenantSeeder) ──────────────┐
                                    ├──→ TS-05 (SeederManager) ──→ TS-10 (Tests)
TS-02 (BaseSeeder) ──────→ TS-04 ─┤                           ┌──→ TS-11 (Regression)
                           (Refactor)─┤
TS-03 (CLI Command) ──────────────┤
                                    ├──→ TS-05 (SeederManager)

TS-06 (Migration) ──────────────────→ TS-07 (Non-Nullable) ──→ TS-08 (Validation) ──→ TS-10 (Tests)

TS-09 (Documentation) ──→ can run anytime after TS-03, TS-05
TS-11 (Regression) ──────→ run last, after all code is done
```

---

## Recommended Execution Order

### Phase 1 — Foundation (Tasks 1-3)

Run **TS-01**, **TS-02**, **TS-03** in parallel. These are foundational changes with no interdependencies.

- TS-01: Create TenantSeeder class
- TS-02: Update BaseSeeder for tenant context
- TS-03: Update CLI command with --tenant flag

### Phase 2 — Refactoring (Tasks 4-5)

After Phase 1, run **TS-04**, **TS-05** in parallel. TS-04 is prerequisite for TS-05 to integrate.

- TS-04: Refactor all 6 individual seeders
- TS-05: Update SeederManager to orchestrate

### Phase 3 — Database & Model (Tasks 6-8)

After Phase 2, run **TS-06**, **TS-07**, **TS-08** sequentially to avoid conflicts.

- TS-06: Migration to backfill and enforce non-nullable
- TS-07: Update model definition
- TS-08: Add validation and helpers

### Phase 4 — Testing & Documentation (Tasks 9-11)

Run after Phase 3 completes, in any order.

- TS-09: Update documentation
- TS-10: Comprehensive tests
- TS-11: Regression testing (run last)
