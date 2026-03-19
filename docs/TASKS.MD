# Project Tasks

> Tasks are independent unless noted in the **Depends On** column.
> Frontend paths are relative to `frontend/src/`.


## System Admin Features (SA-*)

Platform admin capabilities for system-level oversight. Each SA task is independent
and can be implemented in parallel unless noted in **Depends On**.

---

### SA-01 — Platform user management

**Priority:** HIGH

**Problem:**
Platform admins have no central place to manage users across tenants. User creation
happens via tenant invitations or `createtenant`; there is no UI to list all users,
reset passwords, suspend accounts, or assign users to tenants from a platform view.

**Scope:**

| Capability | Description |
| ---------- | ----------- |
| List users | Paginated table of all `User` records across tenants, with search and filters |
| Create user | Form to create a user (email, username) and optionally assign to tenant(s) |
| Edit user | Change email, username, is_active; reset password |
| Suspend/delete | Set `is_active=False` or soft-delete; preserve for audit |
| Assign to tenant | Add/remove TenantMembership records from user detail view |

**Acceptance Criteria:**

- [ ] Wagtail ModelViewSet or Django admin view (platform-only) for User model
- [ ] List view with filters (is_active, tenant, search by email/username)
- [ ] Create user form with optional tenant assignment
- [ ] Edit user form with password reset action
- [ ] Permissions restricted to platform superusers/staff
- [ ] No tenant context required — operates on all users

**Files to Create/Modify:**
- `tenants/wagtail_views.py` or `tenants/viewsets.py` — User management viewset
- `api/serializers/users.py` — Platform user serializers (if exposing via API)
- `api/urls.py` — Platform admin API routes
- Frontend: `frontend/src/app/(dashboard)/settings/users/page.tsx` *(new)*
- Frontend: `frontend/src/features/settings/api/users-api.ts` *(new)*

**Implementation Notes:**
- Can use Wagtail's `ModelViewSet` for `auth.User` or restore Django admin User registration for superusers only (see SA-08).

---

### SA-02 — Tenant oversight and support

**Priority:** HIGH

**Problem:**
System admins cannot override tenant limits, force-deactivate a tenant, or view
usage stats. Support and compliance scenarios require these capabilities.

**Scope:**

| Capability | Description |
| ---------- | ----------- |
| Override limits | Temporarily increase `max_users` or `max_products` for a tenant |
| Force-deactivate | Set `tenant.is_active = False` to block access (compliance, non-payment) |
| Usage stats | Display `user_count()`, `product_count()` and compare to limits |
| Reactivate | Restore `is_active=True` for suspended tenants |

**Acceptance Criteria:**

- [ ] Tenant snippet/edit form includes override controls (or separate admin action)
- [ ] `Force deactivate` and `Reactivate` actions available in tenant list/detail
- [ ] Usage stats (users, products vs limits) visible in tenant list or detail
- [ ] Audit log entry when limits are overridden or tenant is deactivated
- [ ] Only platform superusers can perform these actions

**Files to Modify:**
- `tenants/models.py` — Ensure `user_count`, `product_count`, `is_within_*_limit` exist
- `tenants/snippets.py` — Extend TenantSnippetViewSet with custom actions
- `tenants/wagtail_views.py` — Custom action views for deactivate/reactivate
- Frontend: Tenant settings pages to show usage and override UI (if API-driven)

**Implementation Notes:**
- Backend can be done purely in Wagtail; frontend integration optional if platform admin stays in Wagtail UI.

---

### SA-03 — Impersonate / view-as tenant

**Priority:** MEDIUM

**Problem:**
Support and debugging require viewing the app as a specific tenant or user. There
is no impersonation or view-as-tenant capability.

**Scope:**

| Capability | Description |
| ---------- | ----------- |
| Impersonate user | Log in as another user (or set a session flag) to reproduce issues |
| View as tenant | Switch tenant context without changing logged-in user |
| Exit impersonation | Clear impersonation and return to own session |

**Acceptance Criteria:**

- [ ] Platform superuser can select a user and "Impersonate" from user list/detail
- [ ] Session stores `impersonating_user_id` or equivalent; views use that identity
- [ ] Clear "Exit impersonation" control visible when impersonating
- [ ] Impersonation actions are logged in audit log
- [ ] Tenant switcher (if present) respects impersonation context

**Files to Create/Modify:**
- `tenants/middleware.py` — Impersonation middleware
- `tenants/context.py` — Extend `get_current_tenant` / user resolution
- `api/views/auth.py` — Impersonation start/end endpoints
- `tenants/wagtail_views.py` — Impersonation action buttons
- Frontend: Impersonation UI in user menu or settings

**Implementation Notes:**
- Requires careful security: only superusers, audit everything, time-limited sessions optional.

---

### SA-04 — Platform-wide audit log with export 

**Priority:** HIGH

**Problem:**
There may be tenant-scoped audit logging, but no platform-wide view of who did
what across all tenants. Compliance and support need a unified audit trail with
export (CSV/Excel).

**Scope:**

| Capability | Description |
| ---------- | ----------- |
| Platform audit view | List all audit entries across tenants (or aggregate from tenant logs) |
| Filters | By user, tenant, action type, date range, object type |
| Export | CSV and/or Excel download of filtered results |
| Retention | Document retention policy (e.g., 90 days, 1 year) |

**Acceptance Criteria:**

- [ ] Platform admin can access audit log view (Wagtail or frontend)
- [ ] Filters: user, tenant, action, date range
- [ ] Export to CSV and optionally Excel
- [ ] Pagination for large result sets
- [ ] Audit entries include: timestamp, user, tenant, action, object type, object id, details
- [ ] Only platform superusers can access platform audit view

**Files to Create/Modify:**
- `audit/` or `tenants/` — Platform audit model or query layer
- `api/views/audit.py` — Platform audit list + export endpoints
- `api/urls.py` — Audit routes
- Frontend: `frontend/src/app/(dashboard)/audit-log/page.tsx` — May already exist; extend for platform scope
- Frontend: Export button wired to platform audit API

**Implementation Notes:**
- If audit is currently tenant-scoped, add platform-level aggregation or a shared `AuditLog` model that records tenant_id.

---

### SA-05 — Tenant invitation dashboard

**Priority:** MEDIUM

**Problem:**
Platform admins cannot see pending, accepted, or expired invitations across
tenants. Useful for support and compliance.

**Scope:**

| Capability | Description |
| ---------- | ----------- |
| List invitations | All TenantInvitation records with status, tenant, email, role, dates |
| Filters | By status (pending, accepted, expired, cancelled), tenant, date range |
| Cancel invitation | Set status to cancelled |
| Resend | Regenerate token and extend expiry (optional) |

**Acceptance Criteria:**

- [ ] Platform admin view listing all TenantInvitation records
- [ ] Filters: status, tenant, created_at range
- [ ] Columns: email, tenant, role, status, created_at, expires_at, invited_by
- [ ] Action to cancel a pending invitation
- [ ] Optional: resend invitation (new token, extended expiry)
- [ ] Only platform superusers can access

**Files to Create/Modify:**
- `tenants/wagtail_views.py` or snippet — TenantInvitation list view
- `api/views/invitations.py` — Platform invitation list + cancel/resend
- `api/urls.py` — Invitation routes
- Frontend: `frontend/src/app/(dashboard)/settings/invitations/page.tsx` *(new)*
- Frontend: `frontend/src/features/settings/api/invitations-api.ts` *(new)*

**Implementation Notes:**
- Can be a Wagtail ModelViewSet for TenantInvitation or a custom list view.

---

### SA-06 — Billing and subscription UI

**Priority:** MEDIUM

**Problem:**
Tenant subscription plan and status can be edited in the Tenant snippet, but there
is no dedicated UI for billing workflows (change plan, view usage vs limits,
suspend for non-payment).

**Scope:**

| Capability | Description |
| ---------- | ----------- |
| Change plan | Update `subscription_plan` and `subscription_status` from a billing view |
| Usage vs limits | Table or cards showing each tenant's users/products vs max_users/max_products |
| Suspend/reactivate | Quick actions for non-payment (ties into SA-02 tenant deactivation) |
| Billing notes | Optional field or separate model for billing-related notes |

**Acceptance Criteria:**

- [ ] Billing/subscription view in platform admin
- [ ] List tenants with plan, status, usage (users, products), limits
- [ ] Quick actions: Change plan, Suspend, Reactivate
- [ ] Optional: billing notes per tenant
- [ ] Integrates with existing Tenant model fields
- [ ] Only platform superusers can access

**Files to Create/Modify:**
- `tenants/wagtail_views.py` — Billing dashboard view
- `api/views/tenants.py` — Billing-related endpoints (plan change, usage)
- Frontend: `frontend/src/app/(dashboard)/settings/billing/page.tsx` *(new)*
- Frontend: `frontend/src/features/settings/api/billing-api.ts` *(new)*

**Implementation Notes:**
- Overlaps with SA-02 (usage stats, suspend); can share backend logic.

---

### SA-07 — Tenant data export

**Priority:** LOW

**Problem:**
No way to export a tenant's data for backup, migration, or handover. Platform
admins need this for support and compliance.

**Scope:**

| Capability | Description |
| ---------- | ----------- |
| Export tenant | Generate ZIP/JSON of core tenant data (products, locations, stock, orders, etc.) |
| Scope options | Full export vs. date-range or entity-type filters |
| Format | JSON (machine-readable) and/or CSV for key entities |
| Async | For large tenants, run export as background job and download when ready |

**Acceptance Criteria:**

- [ ] "Export tenant data" action on tenant detail/list
- [ ] Export includes: products, categories, locations, stock records, movements, POs, GRNs, sales orders, dispatches (as applicable)
- [ ] Optional: filter by date range or entity type
- [ ] Output: ZIP containing JSON/CSV files
- [ ] For tenants above size threshold, use Celery task and notify when ready
- [ ] Only platform superusers can trigger export
- [ ] Export action logged in audit

**Files to Create/Modify:**
- `tenants/management/commands/export_tenant.py` — CLI export (can be invoked by view)
- `tenants/services.py` — Export logic (serialize tenant data)
- `api/views/tenants.py` — Export trigger + download endpoint
- Frontend: Export button on tenant detail page

**Implementation Notes:**
- Start with synchronous export for small tenants; add async later if needed.

---

### SA-08 — Django admin fallback for superusers

**Priority:** MEDIUM

**Problem:**
All platform admin was consolidated in Wagtail; Django admin was redirected away.
Some operations (auth.User, Groups, Permissions, migrations, raw DB) still need
Django admin. Superusers have no way to access it.

**Scope:**

| Capability | Description |
| ---------- | ----------- |
| Restore django-admin | Make `/django-admin/` available again (or `/admin/django/`) |
| Access control | Only users with `is_superuser=True` can access |
| Minimal surface | Register only: User, Group, or other system models as needed |
| Documentation | Document when to use Django admin vs. Wagtail |

**Acceptance Criteria:**

- [x] URL `/django-admin/` (or equivalent) is reachable
- [x] Middleware or view decorator restricts access to `is_superuser`
- [x] Non-superusers receive 403 or redirect to Wagtail admin
- [x] Only necessary models registered (User, Group, etc.); tenant-scoped models remain unregistered
- [x] Docs/TASKS.MD or README explains when to use each admin

**When to use Django admin vs Wagtail**

| Use Django admin (`/django-admin/`) | Use Wagtail admin (`/admin/`) |
| ----------------------------------- | ----------------------------- |
| Manage auth.User, Groups, Permissions | Manage tenants, products, inventory, procurement, sales |
| System-level operations (migrations, raw DB) | Content editing, pages, documents, images |
| Superusers only | Staff and tenant admins |

Django admin is restricted to `is_superuser=True` and exposes only User and Group.
Tenant-scoped models (Tenant, TenantMembership, products, etc.) stay in Wagtail.

**Files to Modify:**
- `the_inventory/urls.py` — Add django-admin route back (conditional or always, with auth)
- `tenants/admin.py` — Optionally register User (if not using Wagtail for users)
- `the_inventory/settings/base.py` — No change; use existing admin
- New middleware: `tenants/middleware.py` — `DjangoAdminSuperuserOnlyMiddleware` (optional)

**Implementation Notes:**
- Implemented: custom `SuperuserOnlyAdminSite` in `tenants/django_admin_site.py` with `has_permission` and `login` overrides. User and Group registered in `tenants/admin.py`.

---

### SA-09 — Tenant creation UI in Wagtail

**Priority:** MEDIUM

**Problem:**
Tenants are created only via `createtenant` management command. Platform admins
need a UI to create tenants without CLI access.

**Scope:**

| Capability | Description |
| ---------- | ----------- |
| Create tenant form | Wagtail add view for Tenant with required fields (name, slug) |
| Set owner | Select or create user as tenant owner with role=OWNER |
| Set initial limits | max_users, max_products from form |
| Branding | Optional branding fields in create form |
| Post-create | Redirect to edit view; optionally send invitation email to owner |

**Acceptance Criteria:**

- [ ] "Add tenant" action in Wagtail Snippets → Tenants
- [ ] Create form includes: name, slug, owner (user picker), max_users, max_products
- [ ] Owner user is created or selected; TenantMembership created with role=OWNER
- [ ] If owner is new user: set password or send invitation
- [ ] Post-save redirect to tenant edit with Members inline
- [ ] Reuses logic from `createtenant` where possible (service layer)

**Files to Create/Modify:**
- `tenants/services.py` — `create_tenant_with_owner()` — shared with command and view
- `tenants/snippets.py` — Extend TenantSnippetViewSet create flow
- `tenants/wagtail_forms.py` — Custom create form with owner field
- `tenants/management/commands/createtenant.py` — Refactor to use service
- `tenants/models.py` — Ensure Tenant create validation matches

**Implementation Notes:**
- Extract `createtenant` logic into a service so both CLI and UI use it.

---

## Dependency Graph

```

SA-01 ──────────────────────────────────────────┐
SA-02 ──────────────────────────────────────────┤
SA-03 ──────────────────────────────────────────┤  (all independent, can run in parallel)
SA-04 ──────────────────────────────────────────┤
SA-05 ──────────────────────────────────────────┤
SA-06 ──────────────────────────────────────────┤
SA-07 ──────────────────────────────────────────┤
SA-08 ──────────────────────────────────────────┤
SA-09 ──────────────────────────────────────────┘
```

---

## Recommended Execution Order

### Sprint 1 — Single-Responsibility Fixes (HIGH)

Run **FX-01**, **FX-02**, **FX-03**, **FX-04** in parallel. These are the most
impactful architectural fixes and have zero dependencies.

### Sprint 2 — Structural Cleanup (MEDIUM)

1. Run **FX-05** and **FX-06** in parallel (folder restructures).
2. After FX-06 completes, run **FX-07** and **FX-09** in parallel.
3. Run **FX-08** independently (can overlap with any of the above).

### Sprint 3 — Consistency & Polish (LOW)

Run **FX-10** through **FX-15** in any order. All are independent and small in scope.

### Sprint — System Admin (SA-*)

All SA tasks are independent and can be run in parallel. Suggested order by priority:

| Phase | Tasks | Notes |
| ----- | ----- | ----- |
| Phase 1 (HIGH) | SA-01, SA-02, SA-04 | User management, tenant oversight, audit log |
| Phase 2 (MEDIUM) | SA-03, SA-05, SA-06, SA-08, SA-09 | Impersonation, invitations, billing, Django fallback, tenant creation UI |
| Phase 3 (LOW) | SA-07 | Tenant data export |

SA-02 and SA-06 share logic (usage stats, suspend); implement together or sequentially if preferred.
