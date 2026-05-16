"""Integration tests for seed_database CLI command with tenant handling.

Tests validate:
- CLI command properly creates/reuses tenants
- --tenant flag routes seeding to specific tenant
- --create-default flag creates default tenant
- Command output shows tenant information
- Error handling for invalid tenants
"""

from io import StringIO
from django.test import TransactionTestCase
from django.core.management import call_command
from django.core.management.base import CommandError

from tenants.models import Tenant
from inventory.models import (
    Category,
    Product,
    StockLocation,
    StockRecord,
    StockMovement,
)


class SeedCommandTenantTestCase(TransactionTestCase):
    """Tests for seed_database CLI command with tenant handling."""

    def setUp(self):
        """Set up test fixtures."""
        self.stdout = StringIO()
        self.stderr = StringIO()
        StockMovement.objects.all().delete()
        StockRecord.objects.all().delete()
        StockLocation.objects.all().delete()
        Product.objects.all().delete()
        Category.objects.all().delete()
        Tenant.objects.all().delete()

    def tearDown(self):
        """Clean up after each test."""
        StockMovement.objects.all().delete()
        StockRecord.objects.all().delete()
        StockLocation.objects.all().delete()
        Product.objects.all().delete()
        Category.objects.all().delete()
        Tenant.objects.all().delete()

    def test_seed_command_creates_default_tenant_with_flag(self):
        """Test: seed_database creates Default tenant when --create-default is set."""
        self.assertFalse(Tenant.objects.filter(slug="default").exists())

        call_command(
            "seed_database",
            "--create-default",
            "--quiet",
            stdout=self.stdout,
            stderr=self.stderr,
        )

        # Verify default tenant was created
        tenant = Tenant.objects.get(slug="default")
        self.assertEqual(tenant.name, "Default")
        self.assertTrue(tenant.is_active)

    def test_seed_command_reuses_existing_default_tenant(self):
        """Test: seed_database reuses existing Default tenant without creating new one."""
        # Create default tenant
        default_tenant = Tenant.objects.create(name="Default", slug="default")

        # Run seed command
        call_command(
            "seed_database",
            "--quiet",
            stdout=self.stdout,
            stderr=self.stderr,
        )

        # Verify only one default tenant exists and it's the same one
        self.assertEqual(Tenant.objects.filter(slug="default").count(), 1)
        self.assertEqual(Tenant.objects.get(slug="default").id, default_tenant.id)

    def test_seed_command_seeds_specific_tenant(self):
        """Test: seed_database seeds into specific tenant when --tenant is provided."""
        # Create a specific tenant
        custom_tenant = Tenant.objects.create(name="Acme Corp", slug="acme")

        # Seed into specific tenant
        call_command(
            "seed_database",
            "--tenant",
            "acme",
            "--quiet",
            stdout=self.stdout,
            stderr=self.stderr,
        )

        # Verify data was created for that tenant
        self.assertGreater(Category.objects.filter(tenant=custom_tenant).count(), 0)
        self.assertGreater(Product.objects.filter(tenant=custom_tenant).count(), 0)

    def test_seed_command_fails_with_missing_nonexistent_tenant(self):
        """Test: seed_database fails if --tenant refers to non-existent tenant."""
        with self.assertRaises(CommandError) as cm:
            call_command(
                "seed_database",
                "--tenant",
                "nonexistent",
                "--quiet",
                stdout=self.stdout,
                stderr=self.stderr,
            )

        self.assertIn("not found", str(cm.exception).lower())

    def test_seed_command_output_shows_tenant_info(self):
        """Test: seed_database output includes tenant information."""
        Tenant.objects.create(name="Test Tenant", slug="test-tenant")

        call_command(
            "seed_database",
            "--tenant",
            "test-tenant",
            stdout=self.stdout,
            stderr=self.stderr,
        )

        output = self.stdout.getvalue()
        self.assertIn("Test Tenant", output)
        self.assertIn("test-tenant", output)
