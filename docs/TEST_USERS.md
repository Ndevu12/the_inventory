# Test Users - Seeding Guide

## Overview

Seeding creates two **separate** account classes (WS11):

1. **Platform operators** — `PlatformUserSeeder`: Django `is_staff` / `is_superuser` for **Wagtail** (`/admin/`) and platform API smoke tests. These users have **no** `TenantMembership`, so they **cannot** obtain tenant JWTs for the inventory SPA (`403` with `no_tenant_membership` on `/api/v1/auth/login/`).

2. **Tenant users** — `UserSeeder`: org members with `is_staff=False` and active `TenantMembership` rows covering owner, coordinator, manager, and viewer roles. They can use **Next.js + JWT** like production tenant accounts.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) (*Tenant plane vs platform plane*) for RBAC boundaries and naming.

## Credentials

### Platform (Wagtail / platform-only)

Usernames use the **`platform_*`** prefix; emails use **`@system.local`** so they are never mistaken for org mailboxes (see [ARCHITECTURE.md](docs/ARCHITECTURE.md) vocabulary).

| Username           | Password              | Email (seeded)                          | Django flags               | Tenant memberships |
|--------------------|-----------------------|-----------------------------------------|----------------------------|--------------------|
| `platform_super`   | `platform_super123`   | `platform.superoperator@system.local`   | `is_superuser`, `is_staff` | **None**           |
| `platform_staff` | `platform_staff123`   | `platform.operator@system.local`      | `is_staff` only            | **None**           |

Use these for `http://localhost:8000/admin/`. Do **not** expect tenant JWT login to succeed unless you add a membership manually.

### API impersonation (tenant API as a member)

Tenant inventory routes do not grant a “superuser bypass”: a platform operator with **no** `TenantMembership` must not use their own JWT for tenant CRUD. For scripted or emergency support, a **Django superuser** can call `POST /api/v1/auth/impersonate/start/` with `{"user_id": <pk>}` where the target is an **existing org member** (active `TenantMembership`). The response JWTs match what that member would get from login. Every start/end is audited; set `ENABLE_API_IMPERSONATION=False` to turn off token swap only (Wagtail session impersonation under `/admin/` still exists). See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) (*API impersonation*).

### Tenant (inventory SPA + `/api/v1/` as member)

Tenant seed accounts use **`@org.seed.local`** (synthetic org mailboxes). None of these usernames use **“admin”** — that wording is reserved for the **platform** plane in docs and code.

| Username          | Password          | Email (seeded)               | `TenantRole`   | Django flags | Default org membership |
|-------------------|-------------------|------------------------------|----------------|--------------|-------------------------|
| `owner`           | `owner123`        | `owner@org.seed.local`       | `owner`        | Neither      | Yes (`is_default`)      |
| `coordinator`     | `coordinator123`  | `coordinator@org.seed.local` | `coordinator`  | Neither      | No                      |
| `manager`         | `manager123`      | `manager@org.seed.local`     | `manager`      | Neither      | No                      |
| `tenant_viewer`   | `tenant_viewer123`| `viewer@org.seed.local`      | `viewer`       | Neither      | No                      |

**Dev tip:** Use `owner` or `coordinator` for governance; `manager` for inventory writes per RBAC; `tenant_viewer` for read-oriented flows.

## Quick Start

### Full seed (default tenant + platform + tenant users + inventory)

```bash
python manage.py seed_database --clear --create-default
```

### Seed only users for an existing tenant

```bash
python manage.py seed_database --models=users --tenant=acme-corp
```

(Requires that tenant `acme-corp` already exists; uses the same resolved tenant as other `--tenant` operations.)

### Login paths (two planes)

**Wagtail (platform)**

After seeding:

```
http://localhost:8000/admin/
```

Use `platform_super` / `platform_super123` (or `platform_staff` / `platform_staff123`).

**Tenant inventory API (JWT)**

```bash
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "owner", "password": "owner123"}'
```

Use a **tenant** row from the table above — not `platform_super` / `platform_staff` unless you have added memberships for them.

## User details

### Platform superuser (`platform_super`)

- **Password:** `platform_super123`
- **Email:** `platform.superoperator@system.local`
- **Purpose:** Wagtail, break-glass Django admin, platform API tests
- **Memberships:** none by design (SPA JWT will reject until you add one)

### Platform staff (`platform_staff`)

- **Password:** `platform_staff123`
- **Email:** `platform.operator@system.local`
- **Purpose:** Staff-only Wagtail permission scenarios (`is_superuser=False`)

### Tenant owner (`owner`)

- **Password:** `owner123`
- **Email:** `owner@org.seed.local` (display name: Elena Martinez)
- **Role:** `TenantRole.OWNER`, default membership for the seeded tenant

### Tenant coordinator (`coordinator`)

- **Password:** `coordinator123`
- **Email:** `coordinator@org.seed.local` (display name: Jordan Lee)
- **Role:** `TenantRole.COORDINATOR` (tenant governance per RBAC helpers)

### Tenant manager (`manager`)

- **Password:** `manager123`
- **Email:** `manager@org.seed.local` (display name: Sam Nguyen)
- **Role:** `TenantRole.MANAGER`

### Tenant viewer (`tenant_viewer`)

- **Password:** `tenant_viewer123`
- **Email:** `viewer@org.seed.local` (display name: Riley Chen)
- **Role:** `TenantRole.VIEWER`

## How it works

1. **TenantSeeder** creates or loads the target tenant.
2. **PlatformUserSeeder** ensures `platform_super` and `platform_staff` exist **without** `TenantMembership`.
3. **UserSeeder** ensures `owner`, `coordinator`, `manager`, and `tenant_viewer` exist with `is_staff=False` and links them to the tenant.

Runs are **idempotent** (`get_or_create`). Older databases may still have a legacy `admin` user or orphaned memberships from previous seeds — remove stray `TenantMembership` rows for platform accounts if you want a clean split.

## Multi-tenant

```bash
python manage.py seed_database --clear --create-default
python manage.py createtenant --name="ACME Corp" --slug="acme-corp"
python manage.py seed_database --tenant=acme-corp
```

Platform users are global; tenant seeders attach **tenant** users + memberships to the slug you pass in.

## Programmatic usage

### In tests

Prefer helpers in `tests/fixtures/factories.py`:

- `create_platform_superuser` / `create_platform_staff_user` — no membership
- `create_tenant_user(tenant, role=TenantRole.MANAGER, …)` — membership + `is_staff=False`
- `create_admin_user` — alias defaulting to `platform_super` / `@system.local` (platform-plane)

Example:

```python
from django.test import TestCase
from django.contrib.auth import get_user_model
from seeders import SeederManager
from tenants.models import Tenant, TenantMembership, TenantRole

User = get_user_model()


class MyTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        tenant = Tenant.objects.create(
            name="Test Tenant",
            slug="test-tenant",
            is_active=True,
        )
        SeederManager(verbose=False, clear_data=True).seed(tenant=tenant)
        cls.tenant = tenant

    def test_platform_operator_has_no_membership(self):
        platform_super = User.objects.get(username="platform_super")
        self.assertTrue(platform_super.is_superuser)
        self.assertFalse(
            TenantMembership.objects.filter(user=platform_super, tenant=self.tenant).exists(),
        )

    def test_tenant_owner(self):
        owner = User.objects.get(username="owner")
        self.assertFalse(owner.is_staff)
        m = TenantMembership.objects.get(user=owner, tenant=self.tenant)
        self.assertEqual(m.role, TenantRole.OWNER)
```

### In scripts

```python
from django.contrib.auth import get_user_model
from tenants.models import Tenant, TenantMembership, TenantRole
from seeders import SeederManager

User = get_user_model()

tenant = Tenant.objects.get(slug="default")
SeederManager(verbose=True).seed(tenant=tenant)

owner = User.objects.get(username="owner")
membership = TenantMembership.objects.get(user=owner, tenant=tenant)
print(f"Tenant role: {membership.role}")
```

## API authentication

### Login (`/api/v1/auth/login/`)

```bash
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "owner", "password": "owner123"}'
```

Example shape (fields may vary):

```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "username": "owner",
    "email": "owner@org.seed.local"
  },
  "tenant": { "...": "..." },
  "memberships": []
}
```

If the user has **no** active memberships, expect **403** and `"code": "no_tenant_membership"`.

## Customizing seed users

Extend `UserSeeder` in `seeders/user_seeder.py` for more tenant roles, or `PlatformUserSeeder` in `seeders/platform_user_seeder.py` for extra platform accounts. Do not attach `TenantMembership` to dedicated platform accounts in seeds unless you deliberately want combined-console personas.

## Troubleshooting

### JWT 403 for `platform_super` after seed

Expected: `platform_super` has **no** membership by design. Log in as `owner` (or another row from the tenant table), or add a membership for the platform account only if you deliberately want a dual-console user.

### Password checks

```bash
python manage.py shell
>>> from django.contrib.auth import get_user_model
>>> User = get_user_model()
>>> User.objects.get(username="owner").check_password("owner123")
True
```

### Upgrading from older seeds

If a legacy **`admin`** user still has a `TenantMembership`, delete that row. Prefer **`platform_super`** for Wagtail going forward so tenant vs platform accounts are obvious in dev.

## Related documentation

- [Seeding Guide](seeders/README.md)
- [Architecture — tenant vs platform RBAC](docs/ARCHITECTURE.md)
- [Contributing Guide](CONTRIBUTING.md)
