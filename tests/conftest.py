"""Pytest configuration and shared fixtures for all tests."""

import pytest
from django.contrib.auth import get_user_model
from tenants.models import Tenant, TenantMembership, TenantRole

User = get_user_model()


@pytest.fixture
def tenant():
    """Create a test tenant."""
    return Tenant.objects.create(
        name="Test Tenant",
        slug="test-tenant",
        is_active=True,
    )


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
        "tenant1": Tenant.objects.create(
            name="Tenant 1",
            slug="tenant-1",
            is_active=True,
        ),
        "tenant2": Tenant.objects.create(
            name="Tenant 2",
            slug="tenant-2",
            is_active=True,
        ),
        "tenant3": Tenant.objects.create(
            name="Tenant 3",
            slug="tenant-3",
            is_active=True,
        ),
    }
