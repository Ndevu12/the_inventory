"""Shared test factories for all tests."""

from decimal import Decimal
from datetime import date
import uuid

from django.contrib.auth import get_user_model
from inventory.models import (
    Category, Product, StockLocation, StockRecord, StockMovement, StockLot,
    StockReservation, ReservationRule, InventoryCycle, CycleCountLine,
    InventoryVariance, MovementType, UnitOfMeasure, AllocationStrategy,
    CycleStatus, ReservationStatus, Warehouse,
)
from tenants.models import Tenant, TenantMembership, TenantRole
from tenants.context import get_current_tenant, set_current_tenant
from procurement.models import GoodsReceivedNote, PurchaseOrder, PurchaseOrderLine, Supplier
from sales.models import Customer, Dispatch, SalesOrder, SalesOrderLine

User = get_user_model()


def _resolve_tenant(tenant):
    """Return given tenant, or fall back to thread-local tenant context."""
    if tenant is not None:
        return tenant
    return get_current_tenant()


def create_tenant(name=None, slug=None, **kwargs):
    """Create a test tenant with unique slug."""
    unique_id = str(uuid.uuid4())[:8]
    if name is None:
        name = f"Test Tenant {unique_id}"
    if slug is None:
        slug = f"test-tenant-{unique_id}"
    
    defaults = {"name": name, "slug": slug, "is_active": True}
    defaults.update(kwargs)
    tenant = Tenant.objects.create(**defaults)
    set_current_tenant(tenant)
    return tenant


def create_user(username="testuser", password="testpass123", **kwargs):
    """Create a test user."""
    defaults = {
        "username": username,
        "email": f"{username}@test.com",
        "is_staff": True,
    }
    defaults.update(kwargs)
    user = User.objects.create_user(password=password, **defaults)
    return user


def create_admin_user(username="admin", password="admin123", **kwargs):
    """Create a test superuser."""
    defaults = {
        "username": username,
        "email": f"{username}@test.com",
    }
    defaults.update(kwargs)
    user = User.objects.create_superuser(password=password, **defaults)
    return user


def create_tenant_membership(tenant, user, role=TenantRole.VIEWER, **kwargs):
    """Create a tenant membership."""
    defaults = {
        "tenant": tenant,
        "user": user,
        "role": role,
        "is_active": True,
        "is_default": False,
    }
    defaults.update(kwargs)
    return TenantMembership.objects.create(**defaults)


# Alias used across the test suite
create_membership = create_tenant_membership


def create_category(name="Test Category", slug=None, tenant=None, **kwargs):
    """Create a root category."""
    if slug is None:
        slug = f"cat-{str(uuid.uuid4())[:8]}"
    
    resolved = _resolve_tenant(tenant)
    defaults = {"name": name, "slug": slug, "is_active": True}
    if resolved:
        defaults["tenant"] = resolved
    defaults.update(kwargs)
    return Category.add_root(**defaults)


def create_product(sku=None, name="Test Product", category=None, tenant=None, locale=None, **kwargs):
    """Create a product.

    Pass ``locale`` (a :class:`wagtail.models.Locale`) when the tenant’s
    canonical catalog locale is not the DB default.
    """
    if sku is None:
        sku = f"SKU-{str(uuid.uuid4())[:8]}"
    
    resolved = _resolve_tenant(tenant)
    if category is None and resolved:
        category = create_category(tenant=resolved)
    
    defaults = {
        "sku": sku,
        "name": name,
        "category": category,
        "unit_of_measure": UnitOfMeasure.PIECES,
        "unit_cost": Decimal("10.00"),
        "reorder_point": 5,
        "is_active": True,
    }
    if resolved:
        defaults["tenant"] = resolved
    if locale is not None:
        defaults["locale"] = locale
    defaults.update(kwargs)
    return Product.objects.create(**defaults)


def create_warehouse(name="Chicago DC", tenant=None, **kwargs):
    """Create a tenant-scoped :class:`~inventory.models.Warehouse` (facility row).

    Use with :func:`create_location` passing ``warehouse=…`` for DC mode trees.
    For retail-only fixtures, omit ``warehouse`` on locations (``NULL``).
    """
    resolved = _resolve_tenant(tenant)
    defaults = {"name": name, "description": "", "is_active": True}
    if resolved:
        defaults["tenant"] = resolved
    defaults.update(kwargs)
    return Warehouse.objects.create(**defaults)


def create_location(name="Main Warehouse", tenant=None, **kwargs):
    """Create a root stock location.

    Keyword ``warehouse`` may be a :class:`~inventory.models.Warehouse` instance
    or ``None`` for a retail-only root tree.
    """
    resolved = _resolve_tenant(tenant)
    defaults = {"name": name, "is_active": True}
    if resolved:
        defaults["tenant"] = resolved
    defaults.update(kwargs)
    return StockLocation.add_root(**defaults)


def create_child_location(parent, name, **kwargs):
    """Add a :class:`~inventory.models.StockLocation` child under *parent* (treebeard).

    ``warehouse`` is usually omitted: the model inherits it from the parent on save.
    """
    defaults = {"name": name, "is_active": True, "tenant": parent.tenant}
    defaults.update(kwargs)
    return parent.add_child(**defaults)


def create_stock_record(product, location, quantity=0, **kwargs):
    """Create a stock record."""
    defaults = {
        "product": product,
        "location": location,
        "quantity": quantity,
    }
    if hasattr(product, 'tenant'):
        defaults["tenant"] = product.tenant
    defaults.update(kwargs)
    return StockRecord.objects.create(**defaults)


def create_stock_lot(product, lot_number=None, quantity_received=100,
                     quantity_remaining=100, received_date=None, **kwargs):
    """Create a stock lot."""
    if lot_number is None:
        lot_number = f"LOT-{str(uuid.uuid4())[:8]}"
    
    defaults = {
        "product": product,
        "lot_number": lot_number,
        "quantity_received": quantity_received,
        "quantity_remaining": quantity_remaining,
        "received_date": received_date or date.today(),
    }
    if hasattr(product, 'tenant'):
        defaults["tenant"] = product.tenant
    defaults.update(kwargs)
    return StockLot.objects.create(**defaults)


def create_stock_movement(product, movement_type=MovementType.RECEIVE, quantity=10,
                         from_location=None, to_location=None, **kwargs):
    """Create a stock movement."""
    defaults = {
        "product": product,
        "movement_type": movement_type,
        "quantity": quantity,
        "from_location": from_location,
        "to_location": to_location,
    }
    if hasattr(product, 'tenant'):
        defaults["tenant"] = product.tenant
    defaults.update(kwargs)
    return StockMovement.objects.create(**defaults)


def create_reservation(product, location, quantity=10, status=ReservationStatus.PENDING,
                      stock_lot=None, **kwargs):
    """Create a stock reservation."""
    defaults = {
        "product": product,
        "location": location,
        "quantity": quantity,
        "status": status,
        "stock_lot": stock_lot,
    }
    if hasattr(product, 'tenant'):
        defaults["tenant"] = product.tenant
    defaults.update(kwargs)
    return StockReservation.objects.create(**defaults)


def create_reservation_rule(name="Default Rule", tenant=None, **kwargs):
    """Create a reservation rule."""
    resolved = _resolve_tenant(tenant)
    defaults = {
        "name": name,
        "auto_reserve_on_order": False,
        "reservation_expiry_hours": 72,
        "allocation_strategy": AllocationStrategy.FIFO,
        "is_active": True,
    }
    if resolved:
        defaults["tenant"] = resolved
    defaults.update(kwargs)
    return ReservationRule.objects.create(**defaults)


def create_inventory_cycle(name="Q1 Cycle Count", scheduled_date=None,
                          status=CycleStatus.SCHEDULED, location=None, tenant=None, **kwargs):
    """Create an inventory cycle."""
    resolved = _resolve_tenant(tenant)
    defaults = {
        "name": name,
        "scheduled_date": scheduled_date or date.today(),
        "status": status,
        "location": location,
    }
    if resolved:
        defaults["tenant"] = resolved
    defaults.update(kwargs)
    return InventoryCycle.objects.create(**defaults)


def create_cycle_count_line(cycle, product, location, system_quantity=100,
                           counted_quantity=None, **kwargs):
    """Create a cycle count line."""
    defaults = {
        "cycle": cycle,
        "product": product,
        "location": location,
        "system_quantity": system_quantity,
        "counted_quantity": counted_quantity,
    }
    if hasattr(cycle, 'tenant'):
        defaults["tenant"] = cycle.tenant
    defaults.update(kwargs)
    return CycleCountLine.objects.create(**defaults)


def create_inventory_variance(cycle, count_line, product, location, system_quantity,
                             physical_quantity, variance_type=None, **kwargs):
    """Create an inventory variance."""
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
    if hasattr(cycle, 'tenant'):
        defaults["tenant"] = cycle.tenant
    defaults.update(kwargs)
    return InventoryVariance.objects.create(**defaults)


def create_supplier(name="Test Supplier", code=None, tenant=None, **kwargs):
    """Create a supplier."""
    if code is None:
        code = f"SUP-{str(uuid.uuid4())[:8]}"
    
    resolved = _resolve_tenant(tenant)
    defaults = {"name": name, "code": code, "is_active": True}
    if resolved:
        defaults["tenant"] = resolved
    defaults.update(kwargs)
    return Supplier.objects.create(**defaults)


def create_purchase_order(supplier=None, order_number=None, tenant=None, **kwargs):
    """Create a purchase order."""
    if order_number is None:
        order_number = f"PO-{str(uuid.uuid4())[:8]}"
    
    resolved = _resolve_tenant(tenant)
    if supplier is None and resolved:
        supplier = create_supplier(tenant=resolved)
    elif supplier is None:
        supplier = create_supplier()
    
    defaults = {
        "order_number": order_number,
        "supplier": supplier,
        "status": "draft",
        "order_date": date.today(),
    }
    if resolved:
        defaults["tenant"] = resolved
    defaults.update(kwargs)
    return PurchaseOrder.objects.create(**defaults)


def create_purchase_order_line(purchase_order, product, quantity=10,
                               unit_cost=Decimal("10.00"), **kwargs):
    """Create a purchase order line."""
    defaults = {
        "purchase_order": purchase_order,
        "product": product,
        "quantity": quantity,
        "unit_cost": unit_cost,
    }
    if hasattr(purchase_order, 'tenant'):
        defaults["tenant"] = purchase_order.tenant
    defaults.update(kwargs)
    return PurchaseOrderLine.objects.create(**defaults)


def create_goods_received_note(purchase_order, location, grn_number=None,
                               received_date=None, tenant=None, **kwargs):
    """Create a goods received note."""
    if grn_number is None:
        grn_number = f"GRN-{str(uuid.uuid4())[:8]}"
    
    resolved = _resolve_tenant(tenant)
    if resolved is None and hasattr(purchase_order, 'tenant'):
        resolved = purchase_order.tenant
    
    defaults = {
        "grn_number": grn_number,
        "purchase_order": purchase_order,
        "location": location,
        "received_date": received_date or date.today(),
    }
    if resolved:
        defaults["tenant"] = resolved
    defaults.update(kwargs)
    return GoodsReceivedNote.objects.create(**defaults)


def create_customer(name="Test Customer", code=None, tenant=None, **kwargs):
    """Create a customer."""
    if code is None:
        code = f"CUST-{str(uuid.uuid4())[:8]}"
    
    resolved = _resolve_tenant(tenant)
    defaults = {"name": name, "code": code, "is_active": True}
    if resolved:
        defaults["tenant"] = resolved
    defaults.update(kwargs)
    return Customer.objects.create(**defaults)


def create_sales_order(customer=None, order_number=None, tenant=None, **kwargs):
    """Create a sales order."""
    if order_number is None:
        order_number = f"SO-{str(uuid.uuid4())[:8]}"
    
    resolved = _resolve_tenant(tenant)
    if customer is None and resolved:
        customer = create_customer(tenant=resolved)
    elif customer is None:
        customer = create_customer()
    
    defaults = {
        "order_number": order_number,
        "customer": customer,
        "status": "draft",
        "order_date": date.today(),
    }
    if resolved:
        defaults["tenant"] = resolved
    defaults.update(kwargs)
    return SalesOrder.objects.create(**defaults)


def create_sales_order_line(sales_order, product, quantity=10,
                            unit_price=Decimal("15.00"), **kwargs):
    """Create a sales order line."""
    defaults = {
        "sales_order": sales_order,
        "product": product,
        "quantity": quantity,
        "unit_price": unit_price,
    }
    if hasattr(sales_order, 'tenant'):
        defaults["tenant"] = sales_order.tenant
    defaults.update(kwargs)
    return SalesOrderLine.objects.create(**defaults)


def create_dispatch(sales_order, from_location, dispatch_number=None,
                    dispatch_date=None, tenant=None, **kwargs):
    """Create a dispatch."""
    if dispatch_number is None:
        dispatch_number = f"DSP-{str(uuid.uuid4())[:8]}"
    
    resolved = _resolve_tenant(tenant)
    if resolved is None and hasattr(sales_order, 'tenant'):
        resolved = sales_order.tenant
    
    defaults = {
        "dispatch_number": dispatch_number,
        "sales_order": sales_order,
        "from_location": from_location,
        "dispatch_date": dispatch_date or date.today(),
    }
    if resolved:
        defaults["tenant"] = resolved
    defaults.update(kwargs)
    return Dispatch.objects.create(**defaults)
