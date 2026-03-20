"""Unit tests for the Customer model."""

from django.db import IntegrityError
from django.test import TestCase

from sales.models import Customer
from tests.fixtures.factories import create_tenant

from ..factories import create_customer


class CustomerCreationTests(TestCase):
    """Test Customer creation and field defaults."""

    def test_create_customer_with_defaults(self):
        customer = create_customer()
        self.assertEqual(customer.code, "CUST-001")
        self.assertEqual(customer.name, "Test Customer")
        self.assertTrue(customer.is_active)

    def test_str_representation(self):
        customer = create_customer(code="CUST-100", name="Acme Inc")
        self.assertEqual(str(customer), "CUST-100 — Acme Inc")

    def test_default_is_active(self):
        customer = Customer.objects.create(code="CUST-DEF", name="Default Co")
        self.assertTrue(customer.is_active)


class CustomerConstraintTests(TestCase):
    """Test Customer uniqueness and constraint enforcement."""

    def setUp(self):
        self.tenant = create_tenant()

    def test_code_must_be_unique(self):
        create_customer(code="UNIQUE-001", tenant=self.tenant)
        with self.assertRaises(IntegrityError):
            create_customer(code="UNIQUE-001", name="Duplicate", tenant=self.tenant)

    def test_soft_delete_preserves_record(self):
        customer = create_customer(code="CUST-SOFT")
        customer.is_active = False
        customer.save()
        self.assertTrue(
            Customer.objects.filter(code="CUST-SOFT", is_active=False).exists()
        )
