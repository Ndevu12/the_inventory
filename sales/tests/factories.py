"""Shared test data factories for the sales app."""

from datetime import date
from decimal import Decimal

from inventory.tests.factories import create_location, create_product

from sales.models import (
    Customer,
    Dispatch,
    SalesOrder,
    SalesOrderLine,
    SalesOrderStatus,
)


def create_customer(*, code="CUST-001", name="Test Customer", **kwargs):
    """Create and return a Customer with sensible defaults."""
    defaults = {
        "code": code,
        "name": name,
        "contact_name": "Jane Smith",
        "email": "jane@customer.com",
        "phone": "+9876543210",
        "is_active": True,
    }
    defaults.update(kwargs)
    return Customer.objects.create(**defaults)


def create_sales_order(
    *,
    order_number="SO-2026-001",
    customer=None,
    status=SalesOrderStatus.DRAFT,
    **kwargs,
):
    """Create and return a SalesOrder with sensible defaults."""
    if customer is None:
        customer = create_customer()
    defaults = {
        "order_number": order_number,
        "customer": customer,
        "status": status,
        "order_date": date.today(),
    }
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
        product = create_product()
    if unit_price is None:
        unit_price = product.unit_cost * 2 if product.unit_cost else Decimal("20.00")
    defaults = {
        "sales_order": sales_order,
        "product": product,
        "quantity": quantity,
        "unit_price": unit_price,
    }
    defaults.update(kwargs)
    return SalesOrderLine.objects.create(**defaults)


def create_dispatch(
    *,
    dispatch_number="DSP-2026-001",
    sales_order=None,
    from_location=None,
    **kwargs,
):
    """Create and return a Dispatch."""
    if sales_order is None:
        sales_order = create_sales_order(status=SalesOrderStatus.CONFIRMED)
    if from_location is None:
        from_location = create_location(name="Shipping Dock")
    defaults = {
        "dispatch_number": dispatch_number,
        "sales_order": sales_order,
        "dispatch_date": date.today(),
        "from_location": from_location,
    }
    defaults.update(kwargs)
    return Dispatch.objects.create(**defaults)
