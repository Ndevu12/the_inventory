"""Shared test data factories for the procurement app."""

from datetime import date
from decimal import Decimal

from tests.fixtures.factories import create_location, create_product

from procurement.models import (
    GoodsReceivedNote,
    PaymentTerms,
    PurchaseOrder,
    PurchaseOrderLine,
    PurchaseOrderStatus,
    Supplier,
)


def create_supplier(*, code="SUP-001", name="Test Supplier", **kwargs):
    """Create and return a Supplier with sensible defaults."""
    defaults = {
        "code": code,
        "name": name,
        "contact_name": "John Doe",
        "email": "john@supplier.com",
        "phone": "+1234567890",
        "lead_time_days": 7,
        "payment_terms": PaymentTerms.NET_30,
        "is_active": True,
    }
    defaults.update(kwargs)
    return Supplier.objects.create(**defaults)


def create_purchase_order(
    *,
    order_number="PO-2026-001",
    supplier=None,
    status=PurchaseOrderStatus.DRAFT,
    **kwargs,
):
    """Create and return a PurchaseOrder with sensible defaults."""
    if supplier is None:
        supplier = create_supplier()
    defaults = {
        "order_number": order_number,
        "supplier": supplier,
        "status": status,
        "order_date": date.today(),
    }
    defaults.update(kwargs)
    return PurchaseOrder.objects.create(**defaults)


def create_purchase_order_line(
    *,
    purchase_order,
    product=None,
    quantity=10,
    unit_cost=None,
    **kwargs,
):
    """Create and return a PurchaseOrderLine."""
    if product is None:
        product = create_product()
    if unit_cost is None:
        unit_cost = product.unit_cost or Decimal("10.00")
    defaults = {
        "purchase_order": purchase_order,
        "product": product,
        "quantity": quantity,
        "unit_cost": unit_cost,
    }
    defaults.update(kwargs)
    return PurchaseOrderLine.objects.create(**defaults)


def create_goods_received_note(
    *,
    grn_number="GRN-2026-001",
    purchase_order=None,
    location=None,
    **kwargs,
):
    """Create and return a GoodsReceivedNote."""
    if purchase_order is None:
        purchase_order = create_purchase_order(
            status=PurchaseOrderStatus.CONFIRMED,
        )
    if location is None:
        location = create_location(name="Receiving Dock")
    defaults = {
        "grn_number": grn_number,
        "purchase_order": purchase_order,
        "received_date": date.today(),
        "location": location,
    }
    defaults.update(kwargs)
    return GoodsReceivedNote.objects.create(**defaults)
