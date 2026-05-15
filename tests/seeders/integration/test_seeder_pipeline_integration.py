"""Integration tests for SeederManager full pipeline and TenantSeeder.

Tests validate:
- TenantSeeder creates queryable tenants with full integration
- SeederManager orchestrates complete seeding pipeline
- Full pipeline creates tenant-scoped data across all models
- Data is properly persisted and retrievable
"""

from django.test import TestCase, TransactionTestCase

from tenants.models import Tenant
from seeders.tenant_seeder import TenantSeeder
from seeders.seeder_manager import SeederManager
from inventory.models import (
    Category,
    Product,
    StockLocation,
    StockRecord,
    StockMovement,
)


class TenantSeederIntegrationTestCase(TestCase):
    """Integration tests for TenantSeeder with other components."""

    def setUp(self):
        """Clean up before each test."""
        Tenant.objects.filter(slug="default").delete()

    def tearDown(self):
        """Clean up after each test."""
        Tenant.objects.filter(slug="default").delete()

    def test_tenant_seeder_creates_queryable_tenant(self):
        """Test that the created tenant is queryable and accessible."""
        seeder = TenantSeeder(verbose=False)
        tenant = seeder.execute()

        # Verify we can query for it
        found_tenant = Tenant.objects.get(slug="default")
        self.assertEqual(found_tenant.id, tenant.id)

        # Verify we can filter by name
        named_tenants = Tenant.objects.filter(name="Default")
        self.assertEqual(named_tenants.count(), 1)


class SeederManagerTenantTestCase(TransactionTestCase):
    """Tests for SeederManager tenant orchestration and full pipeline."""

    def setUp(self):
        """Set up test fixtures."""
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

    def test_seeder_manager_creates_default_tenant(self):
        """Test: SeederManager creates default tenant if none provided."""
        manager = SeederManager(verbose=False)
        result = manager.seed()

        # Verify result contains tenant
        self.assertIn("tenant", result)
        self.assertIsNotNone(result["tenant"])
        self.assertEqual(result["tenant"].slug, "default")

        # Verify default tenant exists in database
        default_tenant = Tenant.objects.get(slug="default")
        self.assertIsNotNone(default_tenant)

    def test_seeder_manager_uses_provided_tenant(self):
        """Test: SeederManager uses provided tenant instead of creating new one."""
        # Create a specific tenant
        custom_tenant = Tenant.objects.create(name="Custom", slug="custom")

        manager = SeederManager(verbose=False)
        result = manager.seed(tenant=custom_tenant)

        # Verify result uses the provided tenant
        self.assertEqual(result["tenant"].id, custom_tenant.id)

        # Verify only one tenant exists
        self.assertEqual(Tenant.objects.count(), 1)

    def test_seeder_manager_full_pipeline_creates_tenant_scoped_data(self):
        """Test: SeederManager full pipeline creates all data scoped to tenant."""
        tenant = Tenant.objects.create(name="Test", slug="test")

        manager = SeederManager(verbose=False)
        manager.seed(tenant=tenant)

        # Verify data was created
        self.assertGreater(Category.objects.count(), 0)
        self.assertGreater(Product.objects.count(), 0)
        self.assertGreater(StockLocation.objects.count(), 0)
        self.assertGreater(StockRecord.objects.count(), 0)
        self.assertGreater(StockMovement.objects.count(), 0)

        # Verify all data belongs to the provided tenant
        for category in Category.objects.all():
            self.assertEqual(category.tenant_id, tenant.id)
        for product in Product.objects.all():
            self.assertEqual(product.tenant_id, tenant.id)
        for location in StockLocation.objects.all():
            self.assertEqual(location.tenant_id, tenant.id)
        for record in StockRecord.objects.all():
            self.assertEqual(record.tenant_id, tenant.id)
        for movement in StockMovement.objects.all():
            self.assertEqual(movement.tenant_id, tenant.id)

    def test_seeder_manager_runs_tenant_seeder_first(self):
        """Test: SeederManager runs TenantSeeder first in the pipeline."""
        Tenant.objects.all().delete()

        manager = SeederManager(verbose=False)
        result = manager.seed()

        # Verify default tenant was created by TenantSeeder
        tenant = result["tenant"]
        self.assertEqual(tenant.slug, "default")
        self.assertEqual(tenant.name, "Default")

    def test_seeder_manager_full_pipeline_idempotent_with_default_tenant(self):
        """Test: SeederManager can be run multiple times with default tenant."""
        # First run
        manager1 = SeederManager(verbose=False)
        result1 = manager1.seed()
        tenant1 = result1["tenant"]

        # Second run with same default tenant
        manager2 = SeederManager(verbose=False)
        result2 = manager2.seed()
        tenant2 = result2["tenant"]

        # Both should use the same tenant
        self.assertEqual(tenant1.id, tenant2.id)
        self.assertEqual(tenant1.slug, "default")
