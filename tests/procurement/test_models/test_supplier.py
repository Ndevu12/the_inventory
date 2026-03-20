"""Unit tests for the Supplier model."""

from django.db import IntegrityError
from django.test import TestCase

from procurement.models import PaymentTerms, Supplier
from tests.fixtures.factories import create_tenant

from ..factories import create_supplier


class SupplierCreationTests(TestCase):
    """Test Supplier creation and field defaults."""

    def test_create_supplier_with_defaults(self):
        supplier = create_supplier()
        self.assertEqual(supplier.code, "SUP-001")
        self.assertEqual(supplier.name, "Test Supplier")
        self.assertTrue(supplier.is_active)

    def test_str_representation(self):
        supplier = create_supplier(code="SUP-100", name="Acme Corp")
        self.assertEqual(str(supplier), "SUP-100 — Acme Corp")

    def test_default_payment_terms(self):
        supplier = create_supplier(code="SUP-PT")
        self.assertEqual(supplier.payment_terms, PaymentTerms.NET_30)

    def test_lead_time_days_default(self):
        supplier = Supplier.objects.create(code="SUP-LT", name="Lead Time Co")
        self.assertEqual(supplier.lead_time_days, 0)


class SupplierConstraintTests(TestCase):
    """Test Supplier uniqueness and constraint enforcement."""

    def setUp(self):
        self.tenant = create_tenant()

    def test_code_must_be_unique(self):
        create_supplier(code="UNIQUE-001", tenant=self.tenant)
        with self.assertRaises(IntegrityError):
            create_supplier(code="UNIQUE-001", name="Duplicate", tenant=self.tenant)

    def test_soft_delete_preserves_record(self):
        supplier = create_supplier(code="SUP-SOFT")
        supplier.is_active = False
        supplier.save()
        self.assertTrue(
            Supplier.objects.filter(code="SUP-SOFT", is_active=False).exists()
        )
