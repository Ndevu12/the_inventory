"""Pytest configuration and shared fixtures for all tests."""

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from tenants.models import TenantMembership, TenantRole
from tenants.context import set_current_tenant, clear_current_tenant
from tests.fixtures.factories import create_tenant as factory_create_tenant

User = get_user_model()


@pytest.fixture(autouse=True)
def clear_tenant_context():
    """Clear tenant context and LocMem cache so reused PKs cannot serve stale payloads."""
    clear_current_tenant()
    cache.clear()
    yield
    clear_current_tenant()
    cache.clear()


@pytest.fixture
def tenant():
    """Create a test tenant."""
    t = factory_create_tenant()
    set_current_tenant(t)
    return t


@pytest.fixture
def tenant_coordinator_member(tenant):
    """Tenant governance (coordinator); naming avoids ``admin`` (platform term in docs)."""
    user = User.objects.create_user(
        username="pytest_coordinator",
        email="coordinator.fixture@org.seed.local",
        password="pytest_coord_123",
        is_staff=False,
        is_superuser=False,
    )
    TenantMembership.objects.create(
        tenant=tenant,
        user=user,
        role=TenantRole.COORDINATOR,
        is_active=True,
        is_default=True,
    )
    return user


@pytest.fixture
def admin_user(tenant_coordinator_member):
    """Backward-compatible alias for :func:`tenant_coordinator_member`."""
    return tenant_coordinator_member


@pytest.fixture
def tenant_manager_member(tenant):
    """Tenant member with manager role (not Django ``is_staff``)."""
    user = User.objects.create_user(
        username="pytest_manager",
        email="manager.fixture@org.seed.local",
        password="pytest_mgr_123",
        is_staff=False,
    )
    TenantMembership.objects.create(
        tenant=tenant,
        user=user,
        role=TenantRole.MANAGER,
        is_active=True,
    )
    return user


@pytest.fixture
def staff_user(tenant_manager_member):
    """Backward-compatible alias for :func:`tenant_manager_member`."""
    return tenant_manager_member


@pytest.fixture
def tenant_viewer_member(tenant):
    """Tenant member with viewer role."""
    user = User.objects.create_user(
        username="pytest_viewer",
        email="viewer.fixture@org.seed.local",
        password="pytest_view_123",
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
def regular_user(tenant_viewer_member):
    """Backward-compatible alias for :func:`tenant_viewer_member`."""
    return tenant_viewer_member


@pytest.fixture
def multiple_tenants():
    """Create multiple test tenants."""
    return {
        "tenant1": factory_create_tenant(),
        "tenant2": factory_create_tenant(),
        "tenant3": factory_create_tenant(),
    }
