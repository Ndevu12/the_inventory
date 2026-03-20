# Test Users - Seeding Guide

## Overview

The project now includes a **UserSeeder** that automatically creates test users during database seeding. These users are linked to the default tenant with appropriate roles for testing different permission levels.

## Test User Credentials

| Username | Password | Role | Type | Access Level |
|----------|----------|------|------|--------------|
| `admin` | `admin123` | ADMIN | Superuser | Full system access |
| `manager` | `manager123` | EDITOR | Staff | Create/modify inventory |
| `user` | `user123` | VIEWER | Regular | Read-only access |

## Quick Start

### Seed with Test Users

```bash
# Create default tenant and seed all data including test users
python manage.py seed_database --clear --create-default

# Or seed only users for an existing tenant
python manage.py seed_database --models users --tenant=acme-corp
```

### Login to Admin

After seeding, visit the admin interface:

```
http://localhost:8000/admin/
```

Use any of the test user credentials above.

## User Details

### Admin User
- **Username:** `admin`
- **Password:** `admin123`
- **Email:** `admin@example.com`
- **Role:** ADMIN (Tenant Admin)
- **Permissions:** Full access to all features
- **Django Superuser:** Yes
- **Staff Status:** Yes

### Manager User
- **Username:** `manager`
- **Password:** `manager123`
- **Email:** `manager@example.com`
- **Role:** EDITOR (Tenant Editor)
- **Permissions:** Can create and modify inventory data
- **Django Superuser:** No
- **Staff Status:** Yes

### Regular User
- **Username:** `user`
- **Password:** `user123`
- **Email:** `user@example.com`
- **Role:** VIEWER (Tenant Viewer)
- **Permissions:** Read-only access to inventory data
- **Django Superuser:** No
- **Staff Status:** No

## How It Works

### Seeding Process

1. **TenantSeeder** creates/retrieves the default tenant
2. **UserSeeder** creates the three test users:
   - Creates users if they don't exist
   - Sets passwords securely
   - Reuses existing users if already present (idempotent)
3. **TenantMembership** links each user to the tenant with their role

### Idempotency

The UserSeeder is **idempotent** — you can run seeding multiple times safely:

```bash
# First run: Creates users
python manage.py seed_database --clear --create-default

# Second run: Reuses existing users (no duplicates)
python manage.py seed_database --clear --create-default
```

### Multi-Tenant Support

Each tenant can have its own set of test users:

```bash
# Seed users for Default tenant
python manage.py seed_database --clear --create-default

# Create another tenant
python manage.py createtenant --name="ACME Corp" --slug="acme-corp"

# Seed users for ACME tenant (same users, different tenant membership)
python manage.py seed_database --clear --tenant=acme-corp
```

## Programmatic Usage

### In Tests

```python
from django.test import TestCase
from django.contrib.auth import get_user_model
from inventory.seeders import SeederManager
from tenants.models import Tenant

User = get_user_model()

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
        # Seed data including users
        SeederManager(verbose=False, clear_data=True).seed(tenant=tenant)
        cls.tenant = tenant
    
    def test_with_admin_user(self):
        admin = User.objects.get(username="admin")
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_staff)
    
    def test_with_manager_user(self):
        manager = User.objects.get(username="manager")
        self.assertFalse(manager.is_superuser)
        self.assertTrue(manager.is_staff)
    
    def test_with_regular_user(self):
        user = User.objects.get(username="user")
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_staff)
```

### In Scripts

```python
from django.contrib.auth import get_user_model
from tenants.models import Tenant, TenantMembership, TenantRole
from inventory.seeders import SeederManager

User = get_user_model()

# Seed everything including users
tenant = Tenant.objects.get(slug="default")
SeederManager(verbose=True).seed(tenant=tenant)

# Access the created users
admin = User.objects.get(username="admin")
manager = User.objects.get(username="manager")
user = User.objects.get(username="user")

# Check their tenant memberships
admin_membership = TenantMembership.objects.get(user=admin, tenant=tenant)
print(f"Admin role: {admin_membership.role}")  # Output: ADMIN
```

## API Authentication

### Login Endpoint

```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

Response:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "first_name": "Admin",
    "last_name": "User"
  },
  "tenant": {
    "id": 1,
    "name": "Default",
    "slug": "default",
    "role": "ADMIN"
  }
}
```

### Using Access Token

```bash
curl -X GET http://localhost:8000/api/me/ \
  -H "Authorization: Bearer <access_token>"
```

## Customizing Test Users

To add more test users or modify existing ones, extend the UserSeeder:

```python
from inventory.seeders.user_seeder import UserSeeder
from tenants.models import TenantRole

class CustomUserSeeder(UserSeeder):
    def seed(self):
        # Call parent to create default users
        super().seed()
        
        # Add custom users
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        custom_user, created = User.objects.get_or_create(
            username="analyst",
            defaults={
                "email": "analyst@example.com",
                "first_name": "Data",
                "last_name": "Analyst",
                "is_staff": True,
            },
        )
        if created:
            custom_user.set_password("analyst123")
            custom_user.save()
            self.log(f"✓ Created analyst user: {custom_user.username}")
        
        # Add to tenant
        if self.tenant:
            self._add_user_to_tenant(custom_user, TenantRole.VIEWER)
```

## Troubleshooting

### Users Not Created

**Problem:** Seeding completes but users aren't created

**Solution:** Check that the UserSeeder is included in SeederManager:

```python
from inventory.seeders.seeder_manager import SeederManager

manager = SeederManager(verbose=True)
# Should show "📋 Seeding Users..." in output
manager.seed()
```

### Password Not Working

**Problem:** Can't login with test user credentials

**Solution:** Verify the user exists and password is set:

```bash
python manage.py shell
>>> from django.contrib.auth import get_user_model
>>> User = get_user_model()
>>> admin = User.objects.get(username="admin")
>>> admin.check_password("admin123")
True  # Should return True
```

### Users Exist But Not Linked to Tenant

**Problem:** Users exist but aren't members of the tenant

**Solution:** Manually add them:

```bash
python manage.py shell
>>> from django.contrib.auth import get_user_model
>>> from tenants.models import Tenant, TenantMembership, TenantRole
>>> User = get_user_model()
>>> tenant = Tenant.objects.get(slug="default")
>>> admin = User.objects.get(username="admin")
>>> TenantMembership.objects.get_or_create(
...     tenant=tenant,
...     user=admin,
...     defaults={"role": TenantRole.ADMIN, "is_active": True, "is_default": True}
... )
```

## Related Documentation

- [Seeding Guide](inventory/seeders/README.md) — Complete seeding documentation
- [Architecture](docs/ARCHITECTURE.md) — System design and multi-tenancy
- [Contributing Guide](CONTRIBUTING.md) — Development setup
