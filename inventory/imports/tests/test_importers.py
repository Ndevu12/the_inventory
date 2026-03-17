"""Tests for data importer classes."""

from django.test import TestCase

from inventory.imports.importers import (
    CustomerImporter,
    ProductImporter,
    SupplierImporter,
)
from inventory.models import Product
from procurement.models import Supplier
from sales.models import Customer
from tenants.tests.factories import create_tenant, create_user


class ImporterTestBase(TestCase):
    """Shared setUp providing a tenant and user."""

    def setUp(self):
        self.tenant = create_tenant()
        self.user = create_user(is_staff=True)


class ProductImporterTests(ImporterTestBase):

    def test_product_importer_success(self):
        rows = [
            {"sku": "IMP-001", "name": "Widget", "unit_cost": "10.00", "reorder_point": "5"},
            {"sku": "IMP-002", "name": "Gadget", "unit_cost": "20.00", "reorder_point": "3"},
        ]
        importer = ProductImporter(rows=rows, tenant=self.tenant, user=self.user)
        result = importer.run()

        self.assertTrue(result.success)
        self.assertEqual(result.created_count, 2)
        self.assertEqual(result.errors, [])
        self.assertEqual(Product.objects.filter(tenant=self.tenant).count(), 2)

    def test_product_importer_missing_required_field(self):
        rows = [
            {"sku": "", "name": "No SKU Product", "unit_cost": "10.00"},
        ]
        importer = ProductImporter(rows=rows, tenant=self.tenant, user=self.user)
        result = importer.run()

        self.assertFalse(result.success)
        self.assertTrue(len(result.errors) > 0)
        field_names = [e["field"] for e in result.errors]
        self.assertIn("sku", field_names)
        self.assertEqual(Product.objects.filter(tenant=self.tenant).count(), 0)

    def test_product_importer_invalid_decimal(self):
        rows = [
            {"sku": "BAD-001", "name": "Bad Cost", "unit_cost": "not_a_number"},
        ]
        importer = ProductImporter(rows=rows, tenant=self.tenant, user=self.user)
        result = importer.run()

        self.assertFalse(result.success)
        self.assertTrue(len(result.errors) > 0)
        field_names = [e["field"] for e in result.errors]
        self.assertIn("unit_cost", field_names)
        self.assertEqual(Product.objects.filter(tenant=self.tenant).count(), 0)

    def test_product_importer_missing_columns(self):
        rows = [
            {"name": "No SKU Column"},
        ]
        importer = ProductImporter(rows=rows, tenant=self.tenant, user=self.user)
        result = importer.run()

        self.assertFalse(result.success)
        self.assertTrue(len(result.errors) > 0)
        self.assertIn("Missing required columns", result.errors[0]["message"])

    def test_product_importer_empty_rows(self):
        importer = ProductImporter(rows=[], tenant=self.tenant, user=self.user)
        result = importer.run()

        self.assertFalse(result.success)
        self.assertTrue(len(result.errors) > 0)
        self.assertIn("No data rows", result.errors[0]["message"])


class SupplierImporterTests(ImporterTestBase):

    def test_supplier_importer_success(self):
        rows = [
            {"code": "SUP-001", "name": "Acme Corp", "email": "acme@example.com"},
            {"code": "SUP-002", "name": "Globex Inc", "phone": "555-0100"},
        ]
        importer = SupplierImporter(rows=rows, tenant=self.tenant, user=self.user)
        result = importer.run()

        self.assertTrue(result.success)
        self.assertEqual(result.created_count, 2)
        self.assertEqual(Supplier.objects.filter(tenant=self.tenant).count(), 2)


class CustomerImporterTests(ImporterTestBase):

    def test_customer_importer_success(self):
        rows = [
            {"code": "CUST-001", "name": "John Doe", "email": "john@example.com"},
            {"code": "CUST-002", "name": "Jane Smith", "phone": "555-0200"},
        ]
        importer = CustomerImporter(rows=rows, tenant=self.tenant, user=self.user)
        result = importer.run()

        self.assertTrue(result.success)
        self.assertEqual(result.created_count, 2)
        self.assertEqual(Customer.objects.filter(tenant=self.tenant).count(), 2)


class ImporterTenantTests(ImporterTestBase):

    def test_importer_sets_tenant(self):
        rows = [
            {"sku": "TEN-001", "name": "Tenant Product", "unit_cost": "15.00"},
        ]
        importer = ProductImporter(rows=rows, tenant=self.tenant, user=self.user)
        result = importer.run()

        self.assertTrue(result.success)
        product = Product.objects.get(sku="TEN-001")
        self.assertEqual(product.tenant, self.tenant)
        self.assertEqual(product.created_by, self.user)
