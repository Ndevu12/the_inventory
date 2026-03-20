"""Pytest configuration and shared fixtures for all tests."""

import pytest
from django.contrib.auth import get_user_model
from tenants.models import Tenant, TenantMembership, TenantRole
from tenants.context import set_current_tenant, clear_current_tenant
from tests.fixtures.factories import create_tenant as factory_create_tenant

User = get_user_model()


@pytest.fixture(autouse=True)
def clear_tenant_context():
    """Clear tenant context before and after each test."""
    clear_current_tenant()
    yield
    clear_current_tenant()


@pytest.fixture
def tenant():
    """Create a test tenant."""
    t = factory_create_tenant()
    set_current_tenant(t)
    return t


@pytest.fixture
def admin_user(tenant):
    """Create an admin user for the test tenant."""
    user = User.objects.create_user(
        username="admin",
        email="admin@test.com",
        password="admin123",
        is_staff=True,
        is_superuser=True,
    )
    TenantMembership.objects.create(
        tenant=tenant,
        user=user,
        role=TenantRole.ADMIN,
        is_active=True,
        is_default=True,
    )
    return user


@pytest.fixture
def staff_user(tenant):
    """Create a staff user for the test tenant."""
    user = User.objects.create_user(
        username="staff",
        email="staff@test.com",
        password="staff123",
        is_staff=True,
    )
    TenantMembership.objects.create(
        tenant=tenant,
        user=user,
        role=TenantRole.EDITOR,
        is_active=True,
    )
    return user


@pytest.fixture
def regular_user(tenant):
    """Create a regular user for the test tenant."""
    user = User.objects.create_user(
        username="user",
        email="user@test.com",
        password="user123",
        is_staff=False,
    )
    TenantMembership.objects.create(
        tenant=tenant,
        user=user,
        role=TenantRole.VIEWER,
        is_active=True,
    )
    return user


@pytest.fixture
def multiple_tenants():
    """Create multiple test tenants."""
    return {
        "tenant1": factory_create_tenant(),
        "tenant2": factory_create_tenant(),
        "tenant3": factory_create_tenant(),
    }
