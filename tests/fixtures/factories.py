"""Shared test factories for all tests."""

from decimal import Decimal
from datetime import date
import uuid

from django.contrib.auth import get_user_model
from inventory.models import (
    Category, Product, StockLocation, StockRecord, StockMovement, StockLot,
    StockReservation, ReservationRule, InventoryCycle, CycleCountLine,
    InventoryVariance, MovementType, UnitOfMeasure, AllocationStrategy,
    CycleStatus, ReservationStatus,
)
from tenants.models import Tenant, TenantMembership, TenantRole
from tenants.context import set_current_tenant
from procurement.models import PurchaseOrder, Supplier
from sales.models import SalesOrder, Customer

User = get_user_model()


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


def create_user(username=None, password="testpass123", **kwargs):
    """Create a test user. Username defaults to a unique value per call."""
    if username is None:
        username = f"user_{uuid.uuid4().hex[:12]}"
    defaults = {
        "username": username,
        "email": f"{username}@test.com",
        "is_staff": True,
    }
    defaults.update(kwargs)
    user = User.objects.create_user(password=password, **defaults)
    return user


def create_admin_user(username=None, password="admin123", **kwargs):
    """Create a test superuser. Username defaults to a unique value per call."""
    if username is None:
        username = f"admin_{uuid.uuid4().hex[:12]}"
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
    
    defaults = {"name": name, "slug": slug, "is_active": True}
    if tenant:
        defaults["tenant"] = tenant
    defaults.update(kwargs)
    return Category.add_root(**defaults)


def create_product(sku=None, name="Test Product", category=None, tenant=None, **kwargs):
    """Create a product."""
    if sku is None:
        sku = f"SKU-{str(uuid.uuid4())[:8]}"
    
    if category is None and tenant:
        category = create_category(tenant=tenant)
    
    defaults = {
        "sku": sku,
        "name": name,
        "category": category,
        "unit_of_measure": UnitOfMeasure.PIECES,
        "unit_cost": Decimal("10.00"),
        "reorder_point": 5,
        "is_active": True,
    }
    if tenant:
        defaults["tenant"] = tenant
    defaults.update(kwargs)
    return Product.objects.create(**defaults)


def create_location(name="Main Warehouse", tenant=None, **kwargs):
    """Create a root stock location."""
    defaults = {"name": name, "is_active": True}
    if tenant:
        defaults["tenant"] = tenant
    defaults.update(kwargs)
    return StockLocation.add_root(**defaults)


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
    defaults = {
        "name": name,
        "auto_reserve_on_order": False,
        "reservation_expiry_hours": 72,
        "allocation_strategy": AllocationStrategy.FIFO,
        "is_active": True,
    }
    if tenant:
        defaults["tenant"] = tenant
    defaults.update(kwargs)
    return ReservationRule.objects.create(**defaults)


def create_inventory_cycle(name="Q1 Cycle Count", scheduled_date=None,
                          status=CycleStatus.SCHEDULED, location=None, tenant=None, **kwargs):
    """Create an inventory cycle."""
    defaults = {
        "name": name,
        "scheduled_date": scheduled_date or date.today(),
        "status": status,
        "location": location,
    }
    if tenant:
        defaults["tenant"] = tenant
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
    
    defaults = {"name": name, "code": code, "is_active": True}
    if tenant:
        defaults["tenant"] = tenant
    defaults.update(kwargs)
    return Supplier.objects.create(**defaults)


def create_purchase_order(supplier=None, po_number=None, tenant=None, **kwargs):
    """Create a purchase order."""
    if po_number is None:
        po_number = f"PO-{str(uuid.uuid4())[:8]}"
    
    if supplier is None and tenant:
        supplier = create_supplier(tenant=tenant)
    
    defaults = {"po_number": po_number, "supplier": supplier, "status": "draft"}
    if tenant:
        defaults["tenant"] = tenant
    defaults.update(kwargs)
    return PurchaseOrder.objects.create(**defaults)


def create_customer(name="Test Customer", code=None, tenant=None, **kwargs):
    """Create a customer."""
    if code is None:
        code = f"CUST-{str(uuid.uuid4())[:8]}"
    
    defaults = {"name": name, "code": code, "is_active": True}
    if tenant:
        defaults["tenant"] = tenant
    defaults.update(kwargs)
    return Customer.objects.create(**defaults)


def create_sales_order(customer=None, so_number=None, tenant=None, **kwargs):
    """Create a sales order."""
    if so_number is None:
        so_number = f"SO-{str(uuid.uuid4())[:8]}"
    
    if customer is None and tenant:
        customer = create_customer(tenant=tenant)
    
    defaults = {"so_number": so_number, "customer": customer, "status": "draft"}
    if tenant:
        defaults["tenant"] = tenant
    defaults.update(kwargs)
    return SalesOrder.objects.create(**defaults)
