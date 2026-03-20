"""Tests for per-tenant unique constraints across domain models."""

from datetime import date

from django.db import IntegrityError
from django.test import TestCase

from inventory.models import Product
from procurement.models import PurchaseOrder, Supplier
from sales.models import Customer, SalesOrder
from tests.fixtures.factories import create_tenant


class ProductSkuConstraintTests(TestCase):
    """Product.sku must be unique per tenant."""

    def test_same_sku_different_tenants_allowed(self):
        tenant_a = create_tenant()
        tenant_b = create_tenant()
        Product.objects.create(sku="P-1", name="Product A", tenant=tenant_a)
        Product.objects.create(sku="P-1", name="Product B", tenant=tenant_b)
        self.assertEqual(Product.objects.filter(sku="P-1").count(), 2)

    def test_same_sku_same_tenant_blocked(self):
        tenant = create_tenant()
        Product.objects.create(sku="P-DUP", name="First", tenant=tenant)
        with self.assertRaises(IntegrityError):
            Product.objects.create(sku="P-DUP", name="Second", tenant=tenant)


class SupplierCodeConstraintTests(TestCase):
    """Supplier.code must be unique per tenant."""

    def test_same_code_different_tenants_allowed(self):
        tenant_a = create_tenant()
        tenant_b = create_tenant()
        Supplier.objects.create(code="SUP-1", name="Supplier A", tenant=tenant_a)
        Supplier.objects.create(code="SUP-1", name="Supplier B", tenant=tenant_b)
        self.assertEqual(Supplier.objects.filter(code="SUP-1").count(), 2)

    def test_same_code_same_tenant_blocked(self):
        tenant = create_tenant()
        Supplier.objects.create(code="SUP-DUP", name="First", tenant=tenant)
        with self.assertRaises(IntegrityError):
            Supplier.objects.create(code="SUP-DUP", name="Second", tenant=tenant)


class CustomerCodeConstraintTests(TestCase):
    """Customer.code must be unique per tenant."""

    def test_same_code_different_tenants_allowed(self):
        tenant_a = create_tenant()
        tenant_b = create_tenant()
        Customer.objects.create(code="CUST-1", name="Customer A", tenant=tenant_a)
        Customer.objects.create(code="CUST-1", name="Customer B", tenant=tenant_b)
        self.assertEqual(Customer.objects.filter(code="CUST-1").count(), 2)

    def test_same_code_same_tenant_blocked(self):
        tenant = create_tenant()
        Customer.objects.create(code="CUST-DUP", name="First", tenant=tenant)
        with self.assertRaises(IntegrityError):
            Customer.objects.create(code="CUST-DUP", name="Second", tenant=tenant)


class PurchaseOrderNumberConstraintTests(TestCase):
    """PurchaseOrder.order_number must be unique per tenant."""

    def test_same_number_different_tenants_allowed(self):
        tenant_a = create_tenant()
        tenant_b = create_tenant()
        sup_a = Supplier.objects.create(code="PO-SUP-A", name="Sup A", tenant=tenant_a)
        sup_b = Supplier.objects.create(code="PO-SUP-B", name="Sup B", tenant=tenant_b)
        PurchaseOrder.objects.create(
            order_number="PO-1", supplier=sup_a, status="draft",
            order_date=date.today(), tenant=tenant_a,
        )
        PurchaseOrder.objects.create(
            order_number="PO-1", supplier=sup_b, status="draft",
            order_date=date.today(), tenant=tenant_b,
        )
        self.assertEqual(PurchaseOrder.objects.filter(order_number="PO-1").count(), 2)

    def test_same_number_same_tenant_blocked(self):
        tenant = create_tenant()
        supplier = Supplier.objects.create(code="PO-SUP", name="Sup", tenant=tenant)
        PurchaseOrder.objects.create(
            order_number="PO-DUP", supplier=supplier, status="draft",
            order_date=date.today(), tenant=tenant,
        )
        with self.assertRaises(IntegrityError):
            PurchaseOrder.objects.create(
                order_number="PO-DUP", supplier=supplier, status="draft",
                order_date=date.today(), tenant=tenant,
            )


class SalesOrderNumberConstraintTests(TestCase):
    """SalesOrder.order_number must be unique per tenant."""

    def test_same_number_different_tenants_allowed(self):
        tenant_a = create_tenant()
        tenant_b = create_tenant()
        cust_a = Customer.objects.create(code="SO-CUST-A", name="Cust A", tenant=tenant_a)
        cust_b = Customer.objects.create(code="SO-CUST-B", name="Cust B", tenant=tenant_b)
        SalesOrder.objects.create(
            order_number="SO-1", customer=cust_a, status="draft",
            order_date=date.today(), tenant=tenant_a,
        )
        SalesOrder.objects.create(
            order_number="SO-1", customer=cust_b, status="draft",
            order_date=date.today(), tenant=tenant_b,
        )
        self.assertEqual(SalesOrder.objects.filter(order_number="SO-1").count(), 2)

    def test_same_number_same_tenant_blocked(self):
        tenant = create_tenant()
        customer = Customer.objects.create(code="SO-CUST", name="Cust", tenant=tenant)
        SalesOrder.objects.create(
            order_number="SO-DUP", customer=customer, status="draft",
            order_date=date.today(), tenant=tenant,
        )
        with self.assertRaises(IntegrityError):
            SalesOrder.objects.create(
                order_number="SO-DUP", customer=customer, status="draft",
                order_date=date.today(), tenant=tenant,
            )
