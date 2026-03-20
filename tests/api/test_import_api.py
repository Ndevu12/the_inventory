"""Tests for the import API endpoint."""

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from inventory.models import Product
from procurement.models import Supplier
from tenants.models import TenantRole
from tests.fixtures.factories import create_membership, create_tenant

User = get_user_model()


class ImportAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="importuser",
            password="testpass123",
            is_staff=True,
        )
        self.tenant = create_tenant(slug="import-tenant", name="Import Tenant")
        create_membership(tenant=self.tenant, user=self.user, role=TenantRole.ADMIN)

        login_response = self.client.post(
            reverse("api-login"),
            {"username": "importuser", "password": "testpass123"},
            format="json",
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        access_token = login_response.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        self.url = reverse("api-import")

    def test_import_products_csv(self):
        csv_content = """sku,name,unit_cost
IMP-001,Imported Widget,5.99
IMP-002,Another Widget,3.50
"""
        file_obj = SimpleUploadedFile(
            "products.csv",
            csv_content.encode(),
            content_type="text/csv",
        )
        response = self.client.post(
            self.url,
            {"data_type": "products", "file": file_obj},
            format="multipart",
            HTTP_X_TENANT=self.tenant.slug,
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["created"], 2)
        self.assertTrue(Product.objects.filter(sku="IMP-001").exists())

    def test_import_suppliers_csv(self):
        csv_content = """code,name
SUP-IMP-01,Imported Supplier
"""
        file_obj = SimpleUploadedFile(
            "suppliers.csv",
            csv_content.encode(),
            content_type="text/csv",
        )
        response = self.client.post(
            self.url,
            {"data_type": "suppliers", "file": file_obj},
            format="multipart",
            HTTP_X_TENANT=self.tenant.slug,
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["created"], 1)
        self.assertTrue(Supplier.objects.filter(code="SUP-IMP-01").exists())

    def test_import_invalid_file_type(self):
        file_obj = SimpleUploadedFile(
            "data.txt",
            b"some text content",
            content_type="text/plain",
        )
        response = self.client.post(
            self.url,
            {"data_type": "products", "file": file_obj},
            format="multipart",
            HTTP_X_TENANT=self.tenant.slug,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_import_missing_columns(self):
        csv_content = """description,other
Some value,other value
"""
        file_obj = SimpleUploadedFile(
            "bad_products.csv",
            csv_content.encode(),
            content_type="text/csv",
        )
        response = self.client.post(
            self.url,
            {"data_type": "products", "file": file_obj},
            format="multipart",
            HTTP_X_TENANT=self.tenant.slug,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("errors", response.data)
        self.assertTrue(len(response.data["errors"]) > 0)

    def test_unauthenticated(self):
        csv_content = """sku,name,unit_cost
IMP-001,Imported Widget,5.99
"""
        file_obj = SimpleUploadedFile(
            "products.csv",
            csv_content.encode(),
            content_type="text/csv",
        )
        self.client.credentials()
        response = self.client.post(
            self.url,
            {"data_type": "products", "file": file_obj},
            format="multipart",
            HTTP_X_TENANT=self.tenant.slug,
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
