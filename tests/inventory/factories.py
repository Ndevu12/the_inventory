"""Shared test data factories for the inventory app."""

from decimal import Decimal
import uuid

from django.contrib.auth import get_user_model

from inventory.models import (
    AllocationStrategy,
    Category,
    CycleCountLine,
    CycleStatus,
    InventoryCycle,
    InventoryVariance,
    MovementType,
    Product,
    ReservationRule,
    ReservationStatus,
    StockLocation,
    StockLot,
    StockMovement,
    StockRecord,
    StockReservation,
    UnitOfMeasure,
    Warehouse,
)
from tenants.context import get_current_tenant, set_current_tenant
from tenants.models import Tenant

User = get_user_model()


def _ensure_tenant(tenant):
    """Honor explicit *tenant*, else thread-local from a prior factory call, else a new tenant."""
    if tenant is not None:
        return tenant
    current = get_current_tenant()
    if current is not None:
        return current
    created = create_tenant()
    set_current_tenant(created)
    return created

# Used so ``create_product(category=None)`` can omit a category; default is to auto-create one.
_DEFAULT_PRODUCT_CATEGORY = object()


def create_user(*, username="testuser", password="testpass123", **kwargs):
    """Create and return a Django user (prefer tenant membership for API access)."""
    defaults = {
        "username": username,
        "password": password,
        "is_staff": False,
    }
    defaults.update(kwargs)
    password = defaults.pop("password")
    user = User.objects.create_user(password=password, **defaults)
    return user


def create_admin_user(*, username="platform_super", password="platform_super123", **kwargs):
    """Create and return a Django superuser (platform plane; not a tenant role)."""
    defaults = {
        "username": username,
        "password": password,
        "email": "platform.super@system.local",
    }
    defaults.update(kwargs)
    password = defaults.pop("password")
    user = User.objects.create_superuser(password=password, **defaults)
    return user


def create_tenant(*, name=None, slug=None, **kwargs):
    """Create and return a Tenant with unique slug."""
    unique_id = str(uuid.uuid4())[:8]
    if name is None:
        name = f"Test Corp {unique_id}"
    if slug is None:
        slug = f"test-corp-{unique_id}"
    
    defaults = {
        "name": name,
        "slug": slug,
        "is_active": True,
    }
    defaults.update(kwargs)
    return Tenant.objects.create(**defaults)


def create_category(*, name="Test Category", slug=None, tenant=None, **kwargs):
    """Create and return a root Category node."""
    if slug is None:
        slug = f"cat-{str(uuid.uuid4())[:8]}"
    tenant = _ensure_tenant(tenant)

    defaults = {
        "name": name,
        "slug": slug,
        "is_active": True,
        "tenant": tenant,
    }
    defaults.update(kwargs)
    return Category.add_root(**defaults)


def create_product(
    *,
    sku=None,
    name="Test Product",
    category=_DEFAULT_PRODUCT_CATEGORY,
    tenant=None,
    **kwargs,
):
    """Create and return a Product with sensible defaults."""
    if sku is None:
        sku = f"SKU-{str(uuid.uuid4())[:8]}"

    if category is _DEFAULT_PRODUCT_CATEGORY:
        tenant = _ensure_tenant(tenant)
        category = create_category(tenant=tenant)
    else:
        if tenant is None:
            tenant = category.tenant if category is not None else _ensure_tenant(None)

    defaults = {
        "sku": sku,
        "name": name,
        "category": category,
        "unit_of_measure": UnitOfMeasure.PIECES,
        "unit_cost": Decimal("10.00"),
        "reorder_point": 5,
        "is_active": True,
        "tenant": tenant,
    }
    defaults.update(kwargs)
    return Product.objects.create(**defaults)


def create_warehouse(*, name="Chicago DC", tenant=None, **kwargs):
    """Create a tenant-scoped Warehouse. Pair with :func:`create_location` for DC trees."""
    tenant = _ensure_tenant(tenant)
    defaults = {
        "name": name,
        "description": "",
        "is_active": True,
        "tenant": tenant,
    }
    defaults.update(kwargs)
    return Warehouse.objects.create(**defaults)


def create_location(*, name="Main Warehouse", tenant=None, **kwargs):
    """Create and return a root StockLocation node.

    Pass ``warehouse=`` for a DC-linked root, or ``warehouse=None`` for retail-only.
    """
    tenant = _ensure_tenant(tenant)
    defaults = {
        "name": name,
        "is_active": True,
        "tenant": tenant,
    }
    defaults.update(kwargs)
    return StockLocation.add_root(**defaults)


def create_child_location(parent, *, name, **kwargs):
    """Add a StockLocation child under *parent*; warehouse is inherited from the parent."""
    defaults = {
        "name": name,
        "is_active": True,
        "tenant": parent.tenant,
    }
    defaults.update(kwargs)
    return parent.add_child(**defaults)


def create_stock_record(*, product, location, quantity=0, **kwargs):
    """Create and return a StockRecord."""
    defaults = {
        "product": product,
        "location": location,
        "quantity": quantity,
    }
    if hasattr(product, 'tenant') and product.tenant:
        defaults["tenant"] = product.tenant
    defaults.update(kwargs)
    return StockRecord.objects.create(**defaults)


def create_stock_lot(
    *,
    product,
    lot_number=None,
    quantity_received=100,
    quantity_remaining=100,
    received_date=None,
    **kwargs,
):
    """Create and return a StockLot with sensible defaults."""
    from datetime import date

    if lot_number is None:
        lot_number = f"LOT-{str(uuid.uuid4())[:8]}"

    defaults = {
        "product": product,
        "lot_number": lot_number,
        "quantity_received": quantity_received,
        "quantity_remaining": quantity_remaining,
        "received_date": received_date or date.today(),
        "tenant": product.tenant,
    }
    defaults.update(kwargs)
    return StockLot.objects.create(**defaults)


def create_reservation(
    *,
    product,
    location,
    quantity=10,
    status=ReservationStatus.PENDING,
    stock_lot=None,
    **kwargs,
):
    """Create and return a StockReservation with sensible defaults."""
    defaults = {
        "product": product,
        "location": location,
        "quantity": quantity,
        "status": status,
        "stock_lot": stock_lot,
    }
    defaults.update(kwargs)
    if defaults.get("tenant") is None:
        defaults["tenant"] = (
            getattr(product, "tenant", None) or getattr(location, "tenant", None)
        )
    if defaults.get("tenant") is None:
        defaults["tenant"] = _ensure_tenant(None)
    return StockReservation.objects.create(**defaults)


def create_reservation_rule(*, name="Default Rule", tenant=None, **kwargs):
    """Create and return a ReservationRule with sensible defaults."""
    tenant = _ensure_tenant(tenant)
    defaults = {
        "name": name,
        "auto_reserve_on_order": False,
        "reservation_expiry_hours": 72,
        "allocation_strategy": AllocationStrategy.FIFO,
        "is_active": True,
        "tenant": tenant,
    }
    defaults.update(kwargs)
    return ReservationRule.objects.create(**defaults)


def create_inventory_cycle(
    *,
    name="Q1 Cycle Count",
    scheduled_date=None,
    status=CycleStatus.SCHEDULED,
    location=None,
    **kwargs,
):
    """Create and return an InventoryCycle with sensible defaults."""
    from datetime import date

    defaults = {
        "name": name,
        "scheduled_date": scheduled_date or date.today(),
        "status": status,
        "location": location,
    }
    defaults.update(kwargs)
    if defaults.get("tenant") is None and location is not None:
        defaults["tenant"] = location.tenant
    if defaults.get("tenant") is None:
        defaults["tenant"] = _ensure_tenant(None)
    return InventoryCycle.objects.create(**defaults)


def create_cycle_count_line(
    *,
    cycle,
    product,
    location,
    system_quantity=100,
    counted_quantity=None,
    **kwargs,
):
    """Create and return a CycleCountLine with sensible defaults."""
    defaults = {
        "cycle": cycle,
        "product": product,
        "location": location,
        "system_quantity": system_quantity,
        "counted_quantity": counted_quantity,
    }
    defaults.update(kwargs)
    if defaults.get("tenant") is None:
        t = getattr(cycle, "tenant", None) or getattr(product, "tenant", None)
        t = t or getattr(location, "tenant", None)
        defaults["tenant"] = t or _ensure_tenant(None)
    return CycleCountLine.objects.create(**defaults)


def create_stock_movement(
    *,
    product,
    movement_type=MovementType.RECEIVE,
    quantity=10,
    from_location=None,
    to_location=None,
    **kwargs,
):
    """Create and return a StockMovement (bypasses service layer)."""
    defaults = {
        "product": product,
        "movement_type": movement_type,
        "quantity": quantity,
        "from_location": from_location,
        "to_location": to_location,
    }
    defaults.update(kwargs)
    if defaults.get("tenant") is None:
        defaults["tenant"] = getattr(product, "tenant", None) or _ensure_tenant(
            None,
        )
    return StockMovement.objects.create(**defaults)


def create_inventory_variance(
    *,
    cycle,
    count_line,
    product,
    location,
    system_quantity,
    physical_quantity,
    variance_type=None,
    **kwargs,
):
    """Create and return an InventoryVariance with auto-detected type."""
    if variance_type is None:
        variance_type = InventoryVariance.detect_variance_type(
            system_quantity, physical_quantity
        )
    defaults = {
        "cycle": cycle,
        "count_line": count_line,
        "product": product,
        "location": location,
        "system_quantity": system_quantity,
        "physical_quantity": physical_quantity,
        "variance_type": variance_type,
        "variance_quantity": physical_quantity - system_quantity,
    }
    defaults.update(kwargs)
    if defaults.get("tenant") is None:
        defaults["tenant"] = getattr(cycle, "tenant", None) or _ensure_tenant(
            None,
        )
    return InventoryVariance.objects.create(**defaults)
