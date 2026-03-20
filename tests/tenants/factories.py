"""Lightweight test helpers for creating tenants objects."""

from django.contrib.auth import get_user_model

from tenants.models import (
    SubscriptionPlan,
    SubscriptionStatus,
    Tenant,
    TenantMembership,
    TenantRole,
)

User = get_user_model()

_counter = 0


def _next_id():
    global _counter
    _counter += 1
    return _counter


def create_tenant(*, slug=None, name=None, **kwargs):
    n = _next_id()
    defaults = {
        "slug": slug or f"tenant-{n}",
        "name": name or f"Tenant {n}",
        "is_active": True,
        "subscription_plan": SubscriptionPlan.FREE,
        "subscription_status": SubscriptionStatus.ACTIVE,
        "max_users": 10,
        "max_products": 100,
    }
    defaults.update(kwargs)
    return Tenant.objects.create(**defaults)


def create_user(*, username=None, password="testpass123", **kwargs):
    n = _next_id()
    defaults = {
        "username": username or f"user-{n}",
        "email": f"user-{n}@example.com",
    }
    defaults.update(kwargs)
    user = User.objects.create_user(password=password, **defaults)
    return user


def create_membership(*, tenant, user, role=TenantRole.VIEWER, **kwargs):
    defaults = {
        "tenant": tenant,
        "user": user,
        "role": role,
        "is_active": True,
        "is_default": False,
    }
    defaults.update(kwargs)
    return TenantMembership.objects.create(**defaults)
