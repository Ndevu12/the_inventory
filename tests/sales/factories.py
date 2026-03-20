"""Shared test data factories for the sales app."""

from datetime import date
from decimal import Decimal
import uuid

from tests.fixtures.factories import create_location, create_product

from sales.models import (
    Customer,
    Dispatch,
    SalesOrder,
    SalesOrderLine,
    SalesOrderStatus,
)


def create_customer(*, code=None, name="Test Customer", tenant=None, **kwargs):
    """Create and return a Customer with sensible defaults."""
    if code is None:
        code = f"CUST-{str(uuid.uuid4())[:8]}"
    
    defaults = {
        "code": code,
        "name": name,
        "contact_name": "Jane Smith",
        "email": "jane@customer.com",
        "phone": "+9876543210",
        "is_active": True,
    }
    if tenant:
        defaults["tenant"] = tenant
    defaults.update(kwargs)
    return Customer.objects.create(**defaults)


def create_sales_order(
    *,
    order_number=None,
    customer=None,
    status=SalesOrderStatus.DRAFT,
    tenant=None,
    **kwargs,
):
    """Create and return a SalesOrder with sensible defaults."""
    if order_number is None:
        order_number = f"SO-{str(uuid.uuid4())[:8]}"
    
    if customer is None:
        customer = create_customer(tenant=tenant)
    defaults = {
        "order_number": order_number,
        "customer": customer,
        "status": status,
        "order_date": date.today(),
    }
    if tenant:
        defaults["tenant"] = tenant
    defaults.update(kwargs)
    return SalesOrder.objects.create(**defaults)


def create_sales_order_line(
    *,
    sales_order,
    product=None,
    quantity=10,
    unit_price=None,
    **kwargs,
):
    """Create and return a SalesOrderLine."""
    if product is None:
        product = create_product(tenant=sales_order.tenant)
    if unit_price is None:
        unit_price = product.unit_cost * 2 if product.unit_cost else Decimal("20.00")
    defaults = {
        "sales_order": sales_order,
        "product": product,
        "quantity": quantity,
        "unit_price": unit_price,
    }
    if hasattr(sales_order, 'tenant') and sales_order.tenant:
        defaults["tenant"] = sales_order.tenant
    defaults.update(kwargs)
    return SalesOrderLine.objects.create(**defaults)


def create_dispatch(
    *,
    dispatch_number=None,
    sales_order=None,
    from_location=None,
    tenant=None,
    **kwargs,
):
    """Create and return a Dispatch."""
    if dispatch_number is None:
        dispatch_number = f"DSP-{str(uuid.uuid4())[:8]}"
    
    if sales_order is None:
        sales_order = create_sales_order(status=SalesOrderStatus.CONFIRMED, tenant=tenant)
    if from_location is None:
        from_location = create_location(name="Shipping Dock", tenant=tenant)
    defaults = {
        "dispatch_number": dispatch_number,
        "sales_order": sales_order,
        "dispatch_date": date.today(),
        "from_location": from_location,
    }
    if tenant:
        defaults["tenant"] = tenant
    defaults.update(kwargs)
    return Dispatch.objects.create(**defaults)
