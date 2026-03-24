"""Django admin for tenants app.

Tenant and TenantMembership are managed via the Wagtail admin
(Tenants snippet with Members inline). They are not registered
in Django admin to consolidate platform admin in one place.

SuperuserOnlyAdminSite: Django admin exposed at /django-admin/ for superusers
only. Registers User and Group for auth operations (migrations, permissions,
raw DB). See SA-08 in docs/TASKS.MD.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.admin import GroupAdmin, UserAdmin
from django.contrib.auth.models import Group

from tenants.django_admin_site import superuser_admin_site

# Register system models on the superuser-only Django admin.
# Tenant-scoped models remain unregistered (managed via Wagtail).
User = get_user_model()
superuser_admin_site.register(Group, GroupAdmin)
superuser_admin_site.register(User, UserAdmin)
