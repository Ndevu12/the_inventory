"""Shared test data factories for the procurement app."""

from datetime import date
from decimal import Decimal
import uuid

from tests.fixtures.factories import create_location, create_product, create_tenant

from procurement.models import (
    GoodsReceivedNote,
    PaymentTerms,
    PurchaseOrder,
    PurchaseOrderLine,
    PurchaseOrderStatus,
    Supplier,
)


def create_supplier(*, code=None, name="Test Supplier", tenant=None, **kwargs):
    """Create and return a Supplier with sensible defaults."""
    if code is None:
        code = f"SUP-{str(uuid.uuid4())[:8]}"
    if tenant is None:
        tenant = create_tenant()

    defaults = {
        "code": code,
        "name": name,
        "contact_name": "John Doe",
        "email": "john@supplier.com",
        "phone": "+1234567890",
        "lead_time_days": 7,
        "payment_terms": PaymentTerms.NET_30,
        "is_active": True,
        "tenant": tenant,
    }
    defaults.update(kwargs)
    return Supplier.objects.create(**defaults)


def create_purchase_order(
    *,
    order_number=None,
    supplier=None,
    status=PurchaseOrderStatus.DRAFT,
    tenant=None,
    **kwargs,
):
    """Create and return a PurchaseOrder with sensible defaults."""
    if order_number is None:
        order_number = f"PO-{str(uuid.uuid4())[:8]}"
    
    if supplier is None:
        supplier = create_supplier(tenant=tenant)
    if tenant is None:
        tenant = supplier.tenant
    defaults = {
        "order_number": order_number,
        "supplier": supplier,
        "status": status,
        "order_date": date.today(),
        "tenant": tenant,
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
        product = create_product(tenant=purchase_order.tenant)
    if unit_cost is None:
        unit_cost = product.unit_cost or Decimal("10.00")
    defaults = {
        "purchase_order": purchase_order,
        "product": product,
        "quantity": quantity,
        "unit_cost": unit_cost,
    }
    defaults["tenant"] = purchase_order.tenant
    defaults.update(kwargs)
    return PurchaseOrderLine.objects.create(**defaults)


def create_goods_received_note(
    *,
    grn_number=None,
    purchase_order=None,
    location=None,
    tenant=None,
    **kwargs,
):
    """Create and return a GoodsReceivedNote."""
    if grn_number is None:
        grn_number = f"GRN-{str(uuid.uuid4())[:8]}"
    
    if purchase_order is None:
        purchase_order = create_purchase_order(
            status=PurchaseOrderStatus.CONFIRMED,
            tenant=tenant,
        )
    if tenant is None:
        tenant = purchase_order.tenant
    if location is None:
        location = create_location(name="Receiving Dock", tenant=tenant)
    defaults = {
        "grn_number": grn_number,
        "purchase_order": purchase_order,
        "received_date": date.today(),
        "location": location,
        "tenant": tenant,
    }
    defaults.update(kwargs)
    return GoodsReceivedNote.objects.create(**defaults)
