"""Integration tests verifying data integrity and constraints.

Tests validate:
- No orphaned data (NULL tenant values)
- Unique constraints enforced per tenant
- All seeded data is queryable and properly scoped
- Foreign key relationships intact
"""

from django.test import TransactionTestCase

from tenants.models import Tenant
from seeders.seeder_manager import SeederManager
from seeders.category_seeder import CategorySeeder
from inventory.models import (
    Category,
    Product,
    StockLocation,
    StockRecord,
    StockMovement,
)


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
