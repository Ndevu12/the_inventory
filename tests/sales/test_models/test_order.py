"""Unit tests for SalesOrder, SalesOrderLine, and Dispatch models."""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from tests.fixtures.factories import create_location, create_product
from tests.fixtures.factories import create_tenant

from sales.models import SalesOrderLine, SalesOrderStatus

from ..factories import (
    create_customer,
    create_dispatch,
    create_sales_order,
    create_sales_order_line,
)


# =====================================================================
# SalesOrder
# =====================================================================


class SalesOrderCreationTests(TestCase):
    """Test SalesOrder creation and field defaults."""

    def setUp(self):
        self.tenant = create_tenant()
        self.customer = create_customer(tenant=self.tenant)

    def test_create_draft_order(self):
        so = create_sales_order(customer=self.customer, tenant=self.tenant)
        self.assertEqual(so.status, SalesOrderStatus.DRAFT)
        self.assertEqual(so.customer, self.customer)

    def test_str_representation(self):
        so = create_sales_order(
            order_number="SO-STR-001",
            customer=self.customer,
            tenant=self.tenant,
        )
        self.assertEqual(str(so), f"SO-STR-001 — {self.customer.name}")

    def test_order_number_must_be_unique(self):
        create_sales_order(
            order_number="SO-UNIQ",
            customer=self.customer,
            tenant=self.tenant,
        )
        with self.assertRaises(IntegrityError):
            create_sales_order(
                order_number="SO-UNIQ",
                customer=create_customer(code="CUST-002", tenant=self.tenant),
                tenant=self.tenant,
            )


# =====================================================================
# SalesOrderLine
# =====================================================================


class SalesOrderLineTests(TestCase):
    """Test SalesOrderLine creation and computed properties."""

    def setUp(self):
        self.tenant = create_tenant()
        self.customer = create_customer(tenant=self.tenant)
        self.so = create_sales_order(customer=self.customer, tenant=self.tenant)
        self.product = create_product(sku="SLINE-001", tenant=self.tenant)

    def test_create_line(self):
        line = create_sales_order_line(
            sales_order=self.so,
            product=self.product,
            quantity=50,
            unit_price=Decimal("15.00"),
        )
        self.assertEqual(line.quantity, 50)
        self.assertEqual(line.unit_price, Decimal("15.00"))

    def test_line_total(self):
        line = create_sales_order_line(
            sales_order=self.so,
            product=self.product,
            quantity=20,
            unit_price=Decimal("7.50"),
        )
        self.assertEqual(line.line_total, Decimal("150.00"))

    def test_str_representation(self):
        line = create_sales_order_line(
            sales_order=self.so,
            product=self.product,
            quantity=10,
            unit_price=Decimal("5.00"),
        )
        self.assertEqual(str(line), "SLINE-001 x10 @ 5.00")

    def test_unique_product_per_order(self):
        create_sales_order_line(
            sales_order=self.so,
            product=self.product,
        )
        with self.assertRaises(IntegrityError):
            create_sales_order_line(
                sales_order=self.so,
                product=self.product,
            )

    def test_total_price_across_lines(self):
        p1 = create_product(sku="STOTAL-001", tenant=self.tenant)
        p2 = create_product(sku="STOTAL-002", tenant=self.tenant)
        create_sales_order_line(
            sales_order=self.so,
            product=p1,
            quantity=10,
            unit_price=Decimal("5.00"),
        )
        create_sales_order_line(
            sales_order=self.so,
            product=p2,
            quantity=5,
            unit_price=Decimal("20.00"),
        )
        self.assertEqual(self.so.total_price, Decimal("150.00"))

    def test_tenant_copied_from_sales_order_when_omitted(self):
        line = SalesOrderLine(
            sales_order=self.so,
            product=self.product,
            quantity=2,
            unit_price=Decimal("9.99"),
        )
        line.save()
        line.refresh_from_db()
        self.assertEqual(line.tenant_id, self.so.tenant_id)

    def test_line_tenant_mismatch_raises_validation_error(self):
        other_tenant = create_tenant(name="Other", slug="other-so-line")
        with self.assertRaises(ValidationError):
            SalesOrderLine(
                sales_order=self.so,
                product=self.product,
                quantity=1,
                unit_price=Decimal("1.00"),
                tenant=other_tenant,
            ).save()

    def test_filter_lines_by_tenant(self):
        create_sales_order_line(sales_order=self.so, product=self.product)
        other_tenant = create_tenant(name="Other Co", slug="other-filter")
        other_so = create_sales_order(
            customer=create_customer(code="C-OTHER", tenant=other_tenant),
            tenant=other_tenant,
        )
        other_product = create_product(sku="OTHER-SOL", tenant=other_tenant)
        create_sales_order_line(sales_order=other_so, product=other_product)
        qs = SalesOrderLine.objects.filter(tenant=self.tenant)
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.get().sales_order_id, self.so.id)


# =====================================================================
# Dispatch
# =====================================================================


class DispatchTests(TestCase):
    """Test Dispatch creation and field defaults."""

    def test_create_dispatch(self):
        tenant = create_tenant(slug="dsp-create")
        customer = create_customer(code="CUST-DSP", tenant=tenant)
        so = create_sales_order(
            order_number="SO-DSP-001",
            customer=customer,
            status=SalesOrderStatus.CONFIRMED,
            tenant=tenant,
        )
        location = create_location(name="Shipping Area", tenant=tenant)
        dispatch = create_dispatch(
            dispatch_number="DSP-001",
            sales_order=so,
            from_location=location,
            tenant=tenant,
        )
        self.assertFalse(dispatch.is_processed)
        self.assertEqual(dispatch.sales_order, so)

    def test_str_representation(self):
        tenant = create_tenant(slug="dsp-str")
        customer = create_customer(code="CUST-DSPSTR", tenant=tenant)
        so = create_sales_order(
            order_number="SO-DSPSTR",
            customer=customer,
            status=SalesOrderStatus.CONFIRMED,
            tenant=tenant,
        )
        location = create_location(name="Dock D", tenant=tenant)
        dispatch = create_dispatch(
            dispatch_number="DSP-STR",
            sales_order=so,
            from_location=location,
            tenant=tenant,
        )
        self.assertEqual(str(dispatch), "DSP-STR — SO-DSPSTR")

    def test_dispatch_number_must_be_unique(self):
        tenant = create_tenant()
        customer = create_customer(code="CUST-DSPUNIQ", tenant=tenant)
        so = create_sales_order(
            order_number="SO-DSPUNIQ",
            customer=customer,
            status=SalesOrderStatus.CONFIRMED,
            tenant=tenant,
        )
        location = create_location(name="Dock E", tenant=tenant)
        create_dispatch(
            dispatch_number="DSP-UNIQ",
            sales_order=so,
            from_location=location,
            tenant=tenant,
        )
        with self.assertRaises(IntegrityError):
            create_dispatch(
                dispatch_number="DSP-UNIQ",
                sales_order=so,
                from_location=location,
                tenant=tenant,
            )
