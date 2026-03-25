# Shared REST API contract — auth user flags & compliance audit list

This document is the **cross-track contract** for parallel work on platform UX and audit visibility (`/api/v1/` + Next.js). All changes here are **additive**: no breaking renames of existing fields unless separately agreed.

---

## 1. User payload — `is_superuser` (and optionally `is_staff`)

| Item | Specification |
| --- | --- |
| **Fields** | Read-only booleans: `is_superuser`; optionally also `is_staff` for parity with Django. |
| **Where they appear** | Nested user object from **`UserSerializer`** (`src/api/serializers/auth.py`), including **`POST /api/v1/auth/login/`** and **`GET/PATCH /api/v1/auth/me/`** (via **`MeResponseSerializer`** / same serializer chain). |
| **Semantics** | Expose Django flags only for **client UX** (e.g. show platform audit nav, avoid probing 403 on every navigation). **No change to permissions:** most platform routes enforce **`IsPlatformSuperuser`**; the **`PlatformAuditLogViewSet`** additionally allows **Wagtail admin** users (**``wagtailadmin.access_admin``**), matching the Wagtail audit snippet. Tenant inventory routes still require **active `TenantMembership`** and must not treat these flags as “god mode” on tenant-scoped data. |

Implementers: add fields to **`UserSerializer`** only; keep them **`read_only=True`** in serializers.

---

## 2. Compliance audit list rows — `summary` and `event_scope`

| Item | Specification |
| --- | --- |
| **Serializers** | **`ComplianceAuditLogSerializer`** and **`PlatformAuditLogSerializer`** (`src/api/serializers/audit.py`). |
| **Fields** | **`summary`** — optional read-only string; short human-readable line derived from `action` + `details` (best-effort; fallback e.g. action display label). **`event_scope`** — read-only string enum (see below). |
| **Implementation** | **`SerializerMethodField`** (or equivalent) computed from existing model fields — **no database migration** on `ComplianceAuditLog`. |
| **`event_scope` values** | **`operational`** — normal tenant inventory / day-to-day operations. **`platform`** — governance / platform-attributed events (impersonation, tenant lifecycle, limits, exports, etc.). Exact **`AuditAction` → scope** mapping is a product decision; start from actions not emitted by routine inventory services. |
| **OpenAPI** | When filters or enums are documented from code, keep **`summary`** and **`event_scope`** in schema so frontend and exporters stay aligned. |

---

## 3. Tenant compliance audit list — operational scope only

Applies to **`ComplianceAuditLogViewSet`** (`src/api/views/audit.py`) — the **tenant-scoped** audit list/detail/export (JWT, current tenant).

| Behavior | Specification |
| --- | --- |
| **Platform rows** | Responses **always** **exclude** rows whose computed **`event_scope`** is **`platform`** (same definition as in §2). List, CSV export, and **retrieve by id** must not expose platform-scoped entries on this endpoint — tenant roles use operational inventory history only. |
| **Legacy query params** | **`include_platform_events`** / **`include_platform`** (and any truthy alias) are **ignored** for this viewset; they must **not** widen results. Prefer omitting them from OpenAPI for this path; document the ignore behavior in the viewset docstring if clients might still send them. |
| **Platform list** | **`PlatformAuditLogViewSet`** lists the full trail across tenants for **superusers** or **`wagtailadmin.access_admin`** ( **`IsPlatformAuditAPIAccess`** ); existing **`tenant`** filter remains. |

Rationale: tenant coordinators must not toggle in a flood of platform/session mechanics; platform-scoped auditing belongs in system tooling (superuser REST / Wagtail), not tenant-app query flags.

---

## 4. References in codebase

| Area | Location |
| --- | --- |
| Auth serializers | `src/api/serializers/auth.py` |
| Audit serializers | `src/api/serializers/audit.py` |
| Audit viewsets | `src/api/views/audit.py` |
| Optional display helpers | e.g. `inventory/audit_display.py` — `event_scope_for_action(action)`, `build_audit_summary(entry)` |
| Tests | extend `tests/api/test_audit_api.py` (tenant operational-only filter, ignored `include_platform_events`, platform list, JSON keys) |
