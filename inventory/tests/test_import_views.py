"""Tests for the DataImportView."""

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from wagtail.test.utils import WagtailTestUtils

from inventory.models import Product


class DataImportViewTests(WagtailTestUtils, TestCase):
    """Tests for the CSV/Excel data import view."""

    def setUp(self):
        self.user = self.login()
        self.url = reverse("inventory_import")

    def test_import_view_get(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Import Data")

    def test_import_csv_products(self):
        csv_content = "sku,name,unit_cost\nIMP-001,Widget,10.00\nIMP-002,Gadget,20.00"
        f = SimpleUploadedFile(
            "products.csv",
            csv_content.encode("utf-8"),
            content_type="text/csv",
        )
        response = self.client.post(self.url, {"data_type": "products", "file": f})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Product.objects.filter(sku__in=["IMP-001", "IMP-002"]).count(), 2)

    def test_import_invalid_file_type(self):
        f = SimpleUploadedFile(
            "data.txt",
            b"sku,name\nX-1,Bad",
            content_type="text/plain",
        )
        response = self.client.post(self.url, {"data_type": "products", "file": f})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Unsupported file format")
        self.assertEqual(Product.objects.count(), 0)

    def test_import_requires_login(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_import_csv_with_validation_error(self):
        csv_content = "sku,name,unit_cost\n,Missing SKU,10.00"
        f = SimpleUploadedFile(
            "bad_products.csv",
            csv_content.encode("utf-8"),
            content_type="text/csv",
        )
        response = self.client.post(self.url, {"data_type": "products", "file": f})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Product.objects.count(), 0)
