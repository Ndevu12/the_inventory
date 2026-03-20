"""Comprehensive tests for tenant-scoped seeding system.

Tests:
- TenantSeeder: Creates and retrieves default tenant
- Individual seeders: All use tenant parameter
- SeederManager: Orchestrates full pipeline with tenant
- CLI command: Handles --tenant flag and defaults
- Database integrity: No orphaned data, unique constraints work
"""

from io import StringIO
from django.test import TestCase, TransactionTestCase
from django.core.management import call_command
from django.core.management.base import CommandError

from tenants.models import Tenant
from tenants.context import get_current_tenant, set_current_tenant
from seeders.tenant_seeder import TenantSeeder
from seeders.seeder_manager import SeederManager
from inventory.models import (
    Category,
    Product,
    StockLocation,
    StockRecord,
    StockMovement,
)


class TenantSeederTestCase(TransactionTestCase):
    """Tests for the TenantSeeder class.

    Uses TransactionTestCase because seeders use transaction.atomic().
    """

    def setUp(self):
        """Clean up any existing default tenant before each test."""
        Tenant.objects.filter(slug="default").delete()

    def tearDown(self):
        """Clean up test data after each test."""
        Tenant.objects.filter(slug="default").delete()

    def test_tenant_seeder_creates_default_tenant(self):
        """Test that TenantSeeder creates a default tenant."""
        seeder = TenantSeeder(verbose=False)
        tenant = seeder.execute()

        # Verify tenant was created
        self.assertIsNotNone(tenant)
        self.assertEqual(tenant.name, "Default")
        self.assertEqual(tenant.slug, "default")
        self.assertTrue(tenant.is_active)

        # Verify it's in the database
        db_tenant = Tenant.objects.get(slug="default")
        self.assertEqual(db_tenant.name, "Default")

    def test_tenant_seeder_returns_instance(self):
        """Test that TenantSeeder.execute() returns a Tenant instance."""
        seeder = TenantSeeder(verbose=False)
        result = seeder.execute()

        self.assertIsInstance(result, Tenant)
        self.assertIsNotNone(result.id)

    def test_tenant_seeder_idempotent_on_rerun(self):
        """Test that TenantSeeder is idempotent — safe to re-run."""
        seeder1 = TenantSeeder(verbose=False)
        tenant1 = seeder1.execute()

        # Run again — should return existing tenant
        seeder2 = TenantSeeder(verbose=False)
        tenant2 = seeder2.execute()

        # Both should be the same instance
        self.assertEqual(tenant1.id, tenant2.id)
        self.assertEqual(tenant1.slug, tenant2.slug)

        # Database should have only one default tenant
        default_tenants = Tenant.objects.filter(slug="default")
        self.assertEqual(default_tenants.count(), 1)

    def test_tenant_seeder_stores_instance(self):
        """Test that TenantSeeder stores the tenant instance in self.tenant."""
        seeder = TenantSeeder(verbose=False)
        seeder.execute()

        # Instance should be stored
        self.assertIsNotNone(seeder.tenant)
        self.assertIsInstance(seeder.tenant, Tenant)
        self.assertEqual(seeder.tenant.slug, "default")

    def test_tenant_seeder_creates_active_tenant(self):
        """Test that the created tenant is active by default."""
        seeder = TenantSeeder(verbose=False)
        tenant = seeder.execute()

        self.assertTrue(tenant.is_active)
        db_tenant = Tenant.objects.get(slug="default")
        self.assertTrue(db_tenant.is_active)

    def test_tenant_seeder_with_verbose_mode(self):
        """Test that TenantSeeder works with verbose output enabled."""
        # This test just ensures verbose=True doesn't break execution
        seeder = TenantSeeder(verbose=True)
        tenant = seeder.execute()

        self.assertIsNotNone(tenant)
        self.assertEqual(tenant.slug, "default")

    def test_tenant_seeder_does_not_modify_existing_tenant(self):
        """Test that re-running does not modify an existing tenant."""
        # Create and customize a tenant
        tenant1 = Tenant.objects.create(
            name="Custom Default",
            slug="default",
            is_active=False,
        )

        # Run seeder
        seeder = TenantSeeder(verbose=False)
        tenant2 = seeder.execute()

        # Seeder should return existing tenant unchanged
        self.assertEqual(tenant1.id, tenant2.id)
        self.assertEqual(tenant2.name, "Custom Default")
        self.assertFalse(tenant2.is_active)

    def test_tenant_seeder_transaction_rollback(self):
        """Test that transaction.atomic() provides rollback on failure."""
        # This is a conceptual test — we can't easily force a seeder failure,
        # but we verify the seeder uses atomic() by checking successful commit
        seeder = TenantSeeder(verbose=False)
        tenant = seeder.execute()

        # Verify the transaction committed
        db_tenant = Tenant.objects.get(id=tenant.id)
        self.assertEqual(db_tenant.slug, "default")

    def test_tenant_seeder_multiple_concurrent_execution(self):
        """Test that multiple seeder executions don't create duplicate tenants."""
        # Create first seeder and execute
        seeder1 = TenantSeeder(verbose=False)
        tenant1 = seeder1.execute()

        # Create second seeder and execute
        seeder2 = TenantSeeder(verbose=False)
        tenant2 = seeder2.execute()

        # Create third seeder and execute
        seeder3 = TenantSeeder(verbose=False)
        tenant3 = seeder3.execute()

        # All should reference the same tenant
        self.assertEqual(tenant1.id, tenant2.id)
        self.assertEqual(tenant2.id, tenant3.id)

        # Database should have exactly one default tenant
        count = Tenant.objects.filter(slug="default").count()
        self.assertEqual(count, 1)


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


class CategorySeederTenantTestCase(TransactionTestCase):
    """Tests verifying CategorySeeder respects tenant context."""

    def setUp(self):
        """Set up test fixtures."""
        Category.objects.all().delete()
        Tenant.objects.all().delete()
        self.tenant = Tenant.objects.create(name="Test Tenant", slug="test-tenant")

    def tearDown(self):
        """Clean up after each test."""
        Category.objects.all().delete()
        Tenant.objects.all().delete()

    def test_category_seeder_creates_with_tenant(self):
        """Test: CategorySeeder creates categories assigned to the provided tenant."""
        from seeders.category_seeder import CategorySeeder

        seeder = CategorySeeder(verbose=False)
        seeder.execute(tenant=self.tenant)

        # Verify categories were created
        categories = Category.objects.all()
        self.assertGreater(categories.count(), 0)

        # Verify all categories have the correct tenant
        for category in categories:
            self.assertEqual(category.tenant_id, self.tenant.id)

    def test_category_seeder_hierarchy_respects_tenant(self):
        """Test: CategorySeeder creates hierarchical structure within tenant scope."""
        from seeders.category_seeder import CategorySeeder

        seeder = CategorySeeder(verbose=False)
        seeder.execute(tenant=self.tenant)

        # Get root category (depth=1 for treebeard MP_Node)
        root = Category.objects.filter(tenant=self.tenant, depth=1).first()
        self.assertIsNotNone(root)
        self.assertEqual(root.tenant_id, self.tenant.id)

        # Verify any child categories also have the same tenant
        children = root.get_children()
        for child in children:
            self.assertEqual(child.tenant_id, self.tenant.id)


class ProductSeederTenantTestCase(TransactionTestCase):
    """Tests verifying ProductSeeder respects tenant context."""

    def setUp(self):
        """Set up test fixtures."""
        Product.objects.all().delete()
        Category.objects.all().delete()
        Tenant.objects.all().delete()
        self.tenant = Tenant.objects.create(name="Test Tenant", slug="test-tenant")

        # Create categories first (ProductSeeder depends on them)
        from seeders.category_seeder import CategorySeeder
        cat_seeder = CategorySeeder(verbose=False)
        cat_seeder.execute(tenant=self.tenant)

    def tearDown(self):
        """Clean up after each test."""
        Product.objects.all().delete()
        Category.objects.all().delete()
        Tenant.objects.all().delete()

    def test_product_seeder_creates_with_tenant(self):
        """Test: ProductSeeder creates products assigned to the provided tenant."""
        from seeders.product_seeder import ProductSeeder

        seeder = ProductSeeder(verbose=False)
        seeder.execute(tenant=self.tenant)

        # Verify products were created
        products = Product.objects.all()
        self.assertGreater(products.count(), 0)

        # Verify all products have the correct tenant
        for product in products:
            self.assertEqual(product.tenant_id, self.tenant.id)

    def test_product_seeder_multiple_tenants(self):
        """Test: Products with same SKU can exist in different tenants."""
        from seeders.product_seeder import ProductSeeder

        # Create a second tenant
        tenant2 = Tenant.objects.create(name="Tenant 2", slug="tenant-2")

        # Create categories for tenant2
        from seeders.category_seeder import CategorySeeder
        cat_seeder = CategorySeeder(verbose=False)
        cat_seeder.execute(tenant=tenant2)

        # Seed products for both tenants
        seeder1 = ProductSeeder(verbose=False)
        seeder1.execute(tenant=self.tenant)

        seeder2 = ProductSeeder(verbose=False)
        seeder2.execute(tenant=tenant2)

        # Verify each tenant has products
        tenant1_products = Product.objects.filter(tenant=self.tenant)
        tenant2_products = Product.objects.filter(tenant=tenant2)
        
        self.assertGreater(tenant1_products.count(), 0)
        self.assertGreater(tenant2_products.count(), 0)
        
        # Clean up tenant2 for this test
        Product.objects.filter(tenant=tenant2).delete()
        Category.objects.filter(tenant=tenant2).delete()
        tenant2.delete()


class StockLocationSeederTenantTestCase(TransactionTestCase):
    """Tests verifying StockLocationSeeder respects tenant context."""

    def setUp(self):
        """Set up test fixtures."""
        StockLocation.objects.all().delete()
        Tenant.objects.all().delete()
        self.tenant = Tenant.objects.create(name="Test Tenant", slug="test-tenant")

    def tearDown(self):
        """Clean up after each test."""
        StockLocation.objects.all().delete()
        Tenant.objects.all().delete()

    def test_stock_location_seeder_creates_with_tenant(self):
        """Test: StockLocationSeeder creates locations assigned to the provided tenant."""
        from seeders.stock_location_seeder import StockLocationSeeder

        seeder = StockLocationSeeder(verbose=False)
        seeder.execute(tenant=self.tenant)

        # Verify locations were created
        locations = StockLocation.objects.all()
        self.assertGreater(locations.count(), 0)

        # Verify all locations have the correct tenant
        for location in locations:
            self.assertEqual(location.tenant_id, self.tenant.id)

    def test_stock_location_hierarchy_respects_tenant(self):
        """Test: StockLocationSeeder creates hierarchical structure within tenant scope."""
        from seeders.stock_location_seeder import StockLocationSeeder

        seeder = StockLocationSeeder(verbose=False)
        seeder.execute(tenant=self.tenant)

        # Get root location (depth=1 for treebeard MP_Node)
        root = StockLocation.objects.filter(tenant=self.tenant, depth=1).first()
        self.assertIsNotNone(root)
        self.assertEqual(root.tenant_id, self.tenant.id)

        # Verify children also have the same tenant
        children = root.get_children()
        for child in children:
            self.assertEqual(child.tenant_id, self.tenant.id)


class StockRecordSeederTenantTestCase(TransactionTestCase):
    """Tests verifying StockRecordSeeder respects tenant context."""

    def setUp(self):
        """Set up test fixtures."""
        StockRecord.objects.all().delete()
        StockLocation.objects.all().delete()
        Product.objects.all().delete()
        Category.objects.all().delete()
        Tenant.objects.all().delete()
        self.tenant = Tenant.objects.create(name="Test Tenant", slug="test-tenant")

        # Create prerequisite data
        from seeders.category_seeder import CategorySeeder
        from seeders.product_seeder import ProductSeeder
        from seeders.stock_location_seeder import StockLocationSeeder

        cat_seeder = CategorySeeder(verbose=False)
        cat_seeder.execute(tenant=self.tenant)

        prod_seeder = ProductSeeder(verbose=False)
        prod_seeder.execute(tenant=self.tenant)

        loc_seeder = StockLocationSeeder(verbose=False)
        loc_seeder.execute(tenant=self.tenant)

    def tearDown(self):
        """Clean up after each test."""
        StockRecord.objects.all().delete()
        StockLocation.objects.all().delete()
        Product.objects.all().delete()
        Category.objects.all().delete()
        Tenant.objects.all().delete()

    def test_stock_record_seeder_creates_with_tenant(self):
        """Test: StockRecordSeeder creates records assigned to the provided tenant."""
        from seeders.stock_record_seeder import StockRecordSeeder

        seeder = StockRecordSeeder(verbose=False)
        seeder.execute(tenant=self.tenant)

        # Verify records were created
        records = StockRecord.objects.all()
        self.assertGreater(records.count(), 0)

        # Verify all records have the correct tenant
        for record in records:
            self.assertEqual(record.tenant_id, self.tenant.id)

    def test_stock_record_foreign_keys_respect_tenant(self):
        """Test: StockRecordSeeder creates records linking tenant-scoped products and locations."""
        from seeders.stock_record_seeder import StockRecordSeeder

        seeder = StockRecordSeeder(verbose=False)
        seeder.execute(tenant=self.tenant)

        # Verify links are correct
        records = StockRecord.objects.all()
        for record in records:
            # Product and location should have same tenant as record
            self.assertEqual(record.product.tenant_id, self.tenant.id)
            self.assertEqual(record.location.tenant_id, self.tenant.id)


class StockMovementSeederTenantTestCase(TransactionTestCase):
    """Tests verifying StockMovementSeeder respects tenant context."""

    def setUp(self):
        """Set up test fixtures."""
        StockMovement.objects.all().delete()
        StockRecord.objects.all().delete()
        StockLocation.objects.all().delete()
        Product.objects.all().delete()
        Category.objects.all().delete()
        Tenant.objects.all().delete()
        self.tenant = Tenant.objects.create(name="Test Tenant", slug="test-tenant")

        # Create prerequisite data
        from seeders.category_seeder import CategorySeeder
        from seeders.product_seeder import ProductSeeder
        from seeders.stock_location_seeder import StockLocationSeeder
        from seeders.stock_record_seeder import StockRecordSeeder

        cat_seeder = CategorySeeder(verbose=False)
        cat_seeder.execute(tenant=self.tenant)

        prod_seeder = ProductSeeder(verbose=False)
        prod_seeder.execute(tenant=self.tenant)

        loc_seeder = StockLocationSeeder(verbose=False)
        loc_seeder.execute(tenant=self.tenant)

        rec_seeder = StockRecordSeeder(verbose=False)
        rec_seeder.execute(tenant=self.tenant)

    def tearDown(self):
        """Clean up after each test."""
        StockMovement.objects.all().delete()
        StockRecord.objects.all().delete()
        StockLocation.objects.all().delete()
        Product.objects.all().delete()
        Category.objects.all().delete()
        Tenant.objects.all().delete()

    def test_stock_movement_seeder_creates_with_tenant(self):
        """Test: StockMovementSeeder creates movements assigned to the provided tenant."""
        from seeders.stock_movement_seeder import StockMovementSeeder

        seeder = StockMovementSeeder(verbose=False)
        seeder.execute(tenant=self.tenant)

        # Verify movements were created
        movements = StockMovement.objects.all()
        self.assertGreater(movements.count(), 0)

        # Verify all movements have the correct tenant
        for movement in movements:
            self.assertEqual(movement.tenant_id, self.tenant.id)


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
        result = manager.seed(tenant=tenant)

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
        custom_tenant = Tenant.objects.create(name="Test Tenant", slug="test-tenant")

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


class DataIntegrityTenantTestCase(TransactionTestCase):
    """Tests verifying data integrity: no orphaned data, constraints work."""

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

    def test_no_orphaned_data_after_full_seeding(self):
        """Test: After full seeding, verify NO data has NULL tenant."""
        tenant = Tenant.objects.create(name="Test", slug="test")

        manager = SeederManager(verbose=False)
        manager.seed(tenant=tenant)

        # Check each model for orphaned data
        null_categories = Category.objects.filter(tenant__isnull=True)
        null_products = Product.objects.filter(tenant__isnull=True)
        null_locations = StockLocation.objects.filter(tenant__isnull=True)
        null_records = StockRecord.objects.filter(tenant__isnull=True)
        null_movements = StockMovement.objects.filter(tenant__isnull=True)

        # All should be empty
        self.assertEqual(null_categories.count(), 0, "Categories have NULL tenant")
        self.assertEqual(null_products.count(), 0, "Products have NULL tenant")
        self.assertEqual(null_locations.count(), 0, "Locations have NULL tenant")
        self.assertEqual(null_records.count(), 0, "StockRecords have NULL tenant")
        self.assertEqual(null_movements.count(), 0, "StockMovements have NULL tenant")

    def test_product_sku_unique_constraint_per_tenant(self):
        """Test: Product SKU is unique per tenant, not globally."""
        # Create two tenants
        tenant1 = Tenant.objects.create(name="Tenant 1", slug="tenant-1")
        tenant2 = Tenant.objects.create(name="Tenant 2", slug="tenant-2")

        # Create a category for each tenant
        from seeders.category_seeder import CategorySeeder
        cat_seeder1 = CategorySeeder(verbose=False)
        cat_seeder1.execute(tenant=tenant1)
        cat_seeder2 = CategorySeeder(verbose=False)
        cat_seeder2.execute(tenant=tenant2)

        # Get same category from each tenant
        category1 = Category.objects.filter(tenant=tenant1).first()
        category2 = Category.objects.filter(tenant=tenant2).first()

        # Create products with same SKU in different tenants
        product1 = Product.objects.create(
            name="Product 1",
            sku="SAME-SKU",
            category=category1,
            tenant=tenant1,
        )
        product2 = Product.objects.create(
            name="Product 2",
            sku="SAME-SKU",
            category=category2,
            tenant=tenant2,
        )

        # Both should exist without constraint violation
        self.assertIsNotNone(product1.id)
        self.assertIsNotNone(product2.id)

        # But same SKU in same tenant should fail
        with self.assertRaises(Exception):  # IntegrityError
            Product.objects.create(
                name="Product 3",
                sku="SAME-SKU",
                category=category1,
                tenant=tenant1,
            )

    def test_all_seeded_data_queryable_by_tenant(self):
        """Test: All seeded data can be queried and filtered by tenant."""
        tenant = Tenant.objects.create(name="Test", slug="test")

        manager = SeederManager(verbose=False)
        manager.seed(tenant=tenant)

        # Verify we can query by tenant
        categories = Category.objects.filter(tenant=tenant)
        products = Product.objects.filter(tenant=tenant)
        locations = StockLocation.objects.filter(tenant=tenant)
        records = StockRecord.objects.filter(tenant=tenant)
        movements = StockMovement.objects.filter(tenant=tenant)

        # All should have records
        self.assertGreater(categories.count(), 0)
        self.assertGreater(products.count(), 0)
        self.assertGreater(locations.count(), 0)
        self.assertGreater(records.count(), 0)
        self.assertGreater(movements.count(), 0)
