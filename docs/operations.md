# Operations Guide

This guide is for platform operators and administrators who manage **The Inventory** deployment.

---

## Table of Contents

- [Platform Overview](#platform-overview)
- [Tenant Management](#tenant-management)
- [User Management](#user-management)
- [Monitoring](#monitoring)
- [Maintenance](#maintenance)
- [Troubleshooting](#troubleshooting)

---

## Platform Overview

**The Inventory** is a multi-tenant SaaS platform. As an operator, you manage:

- **Tenants** — Organizations using the platform
- **Users** — People with access to tenants
- **Roles** — Permissions within tenants
- **System Health** — Monitoring and alerts

### Admin Interfaces

- **Wagtail Admin** — `/admin/` (for platform staff)
- **Django Admin** — `/django-admin/` (low-level access)
- **API** — `/api/v1/` (programmatic access)

---

## Tenant Management

### Create a Tenant

**Via Wagtail Admin:**

1. Go to `/admin/`
2. Navigate to **Tenants** → **Tenants**
3. Click **Add Tenant**
4. Fill in:
   - **Name** — Organization name
   - **Slug** — URL-friendly identifier
   - **Active** — Enable/disable tenant
   - **Branding** — Logo, colors, etc.
5. Click **Save**

**Via API:**

```bash
curl -X POST http://localhost:8000/api/v1/tenants/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Acme Corp",
    "slug": "acme-corp",
    "is_active": true
  }'
```

### List Tenants

**Via Wagtail Admin:**
1. Go to `/admin/`
2. Navigate to **Tenants** → **Tenants**

**Via API:**

```bash
curl http://localhost:8000/api/v1/tenants/ \
  -H "Authorization: Bearer <token>"
```

### Update Tenant

**Via Wagtail Admin:**
1. Go to `/admin/` → **Tenants** → **Tenants**
2. Click tenant name
3. Edit fields
4. Click **Save**

**Via API:**

```bash
curl -X PATCH http://localhost:8000/api/v1/tenants/{id}/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "New Name"}'
```

### Deactivate Tenant

To temporarily disable a tenant:

```bash
curl -X PATCH http://localhost:8000/api/v1/tenants/{id}/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"is_active": false}'
```

---

## User Management

### Create User

**Via Wagtail Admin:**

1. Go to `/admin/`
2. Navigate to **Users** → **Users**
3. Click **Add User**
4. Fill in:
   - **Username** — Unique identifier
   - **Email** — User email
   - **Password** — Set password
   - **Staff Status** — For admin access
   - **Superuser Status** — For platform admin
5. Click **Save**

**Via Django Admin:**

```bash
python manage.py createsuperuser
```

### Assign User to Tenant

**Via Wagtail Admin:**

1. Go to `/admin/`
2. Navigate to **Tenants** → **Tenant Memberships**
3. Click **Add Membership**
4. Select:
   - **User** — User to add
   - **Tenant** — Organization
   - **Role** — Owner, Coordinator, Manager, or Viewer
5. Click **Save**

**Via API:**

```bash
curl -X POST http://localhost:8000/api/v1/tenants/memberships/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "user": 1,
    "tenant": 1,
    "role": "manager"
  }'
```

### User Roles

| Role | Permissions |
|------|-------------|
| **Owner** | Full access, manage members, billing |
| **Coordinator** | Manage inventory, orders, reports |
| **Manager** | View and manage inventory |
| **Viewer** | Read-only access |

### Reset User Password

**Via Wagtail Admin:**

1. Go to `/admin/` → **Users** → **Users**
2. Click user
3. Click **Change Password**
4. Enter new password
5. Click **Save**

**Via Django Admin:**

```bash
python manage.py changepassword username
```

### Deactivate User

**Via Wagtail Admin:**

1. Go to `/admin/` → **Users** → **Users**
2. Click user
3. Uncheck **Active**
4. Click **Save**

---

## Monitoring

### System Health

Check system status:

```bash
# Django health check
curl http://localhost:8000/api/v1/

# Database connection
python manage.py dbshell

# Cache connection
python manage.py shell
>>> from django.core.cache import cache
>>> cache.set('test', 'value')
>>> cache.get('test')
```

### Database Monitoring

**Check active connections:**

```bash
psql postgresql://user:pass@host/inventory

SELECT * FROM pg_stat_activity;
```

**Check slow queries:**

```sql
SELECT query, calls, mean_time FROM pg_stat_statements 
ORDER BY mean_time DESC LIMIT 10;
```

**Check table sizes:**

```sql
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) 
FROM pg_tables 
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Application Logs

**View logs:**

```bash
# Render
# Via Render dashboard → Logs tab

# Docker
docker logs container_name

# Kubernetes
kubectl logs -f deployment/inventory-api
```

### Alerts to Set Up

Configure alerts for:
- **High error rate** — >5% of requests failing
- **High response time** — >1 second average
- **Database connection pool exhaustion**
- **Out of memory** — >90% memory usage
- **Disk space low** — <10% free space
- **Backup failure** — Backup didn't complete

---

## Maintenance

### Database Backups

**Manual backup:**

```bash
pg_dump postgresql://user:pass@host/inventory > backup.sql
gzip backup.sql
```

**Automated backup (cron):**

```bash
# Daily backup at 2 AM
0 2 * * * pg_dump postgresql://user:pass@host/inventory | gzip > /backups/inventory_$(date +\%Y\%m\%d).sql.gz
```

### Restore from Backup

```bash
gunzip backup.sql.gz
psql postgresql://user:pass@host/inventory < backup.sql
```

### Database Maintenance

**Vacuum (cleanup):**

```bash
psql postgresql://user:pass@host/inventory -c "VACUUM ANALYZE;"
```

**Reindex (optimize):**

```bash
psql postgresql://user:pass@host/inventory -c "REINDEX DATABASE inventory;"
```

### Update Dependencies

```bash
# Check for updates
pip list --outdated

# Update specific package
pip install --upgrade package_name

# Update all
pip install --upgrade -r requirements.txt
```

### Clear Cache

```bash
python manage.py shell
>>> from django.core.cache import cache
>>> cache.clear()
```

### Collect Static Files

```bash
python manage.py collectstatic --noinput
```

---

## Troubleshooting

### High Database Load

**Symptoms:** Slow queries, high CPU usage

**Solutions:**
1. Check for slow queries: `SELECT * FROM pg_stat_statements ORDER BY mean_time DESC`
2. Add indexes to frequently queried columns
3. Optimize queries using `select_related()` and `prefetch_related()`
4. Increase database resources (CPU, RAM)

### Out of Memory

**Symptoms:** Application crashes, "MemoryError"

**Solutions:**
1. Check memory usage: `free -h`
2. Increase server memory
3. Reduce cache TTL
4. Optimize large queries

### Slow API Responses

**Symptoms:** API endpoints taking >1 second

**Solutions:**
1. Check database query performance
2. Enable caching for frequently accessed data
3. Add database indexes
4. Increase server resources

### Backup Failure

**Symptoms:** Backup job fails or doesn't complete

**Solutions:**
1. Check disk space: `df -h`
2. Verify database connection
3. Check backup script permissions
4. Review backup logs

### User Can't Login

**Symptoms:** "Invalid credentials" or "No tenant membership"

**Solutions:**
1. Verify user exists: Check Wagtail admin
2. Verify user is active: Check "Active" checkbox
3. Verify user has tenant membership: Check Tenant Memberships
4. Reset password if needed

### API Returns 500 Error

**Symptoms:** "Internal Server Error"

**Solutions:**
1. Check application logs
2. Check database connection
3. Check for recent code changes
4. Restart application

---

## Common Tasks

### Bulk Import Users

```python
# management/commands/import_users.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import csv

User = get_user_model()

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str)

    def handle(self, *args, **options):
        with open(options['csv_file']) as f:
            reader = csv.DictReader(f)
            for row in reader:
                User.objects.create_user(
                    username=row['username'],
                    email=row['email'],
                    password=row['password']
                )
```

Run with:
```bash
python manage.py import_users users.csv
```

### Generate API Token

```bash
python manage.py shell
>>> from rest_framework.authtoken.models import Token
>>> from django.contrib.auth import get_user_model
>>> User = get_user_model()
>>> user = User.objects.get(username='username')
>>> token = Token.objects.create(user=user)
>>> print(token.key)
```

### Export Tenant Data

```bash
# Export products
python manage.py dumpdata inventory.product --indent 2 > products.json

# Export all data
python manage.py dumpdata > full_backup.json
```

---

## Next Steps

- **Deployment:** See [Deployment Guide](deployment.md)
- **Monitoring:** Set up logging and alerts
- **Backups:** Configure automated backups
- **Security:** Review security settings

---

## Need Help?

- 📖 Check [FAQ](faq.md)
- 🐛 See [Troubleshooting Guide](troubleshooting.md)
- 💬 Open an [Issue on GitHub](https://github.com/Ndevu12/the_inventory/issues)
