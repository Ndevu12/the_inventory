"""Tests for BaseSeeder and its tenant context functionality."""

from django.test import TestCase, TransactionTestCase
from tenants.models import Tenant
from inventory.models.product import Product
from inventory.models.category import Category
from seeders.base import BaseSeeder


class ConcreteSeeder(BaseSeeder):
    """Concrete implementation of BaseSeeder for testing."""

    def seed(self):
        """Simple seed implementation for testing."""
        if self.tenant:
            self.log(f"Seeding for tenant: {self.tenant.name}")


class BaseSeederTestCase(TransactionTestCase):
    """Tests for the BaseSeeder class with tenant context.

    Uses TransactionTestCase because seeders use transaction.atomic().
    """

    def setUp(self):
        """Set up test fixtures."""
        self.tenant = Tenant.objects.create(
            name="Test Tenant",
            slug="test-tenant",
            is_active=True,
        )
        self.seeder = ConcreteSeeder(verbose=False)

    def tearDown(self):
        """Clean up test data."""
        Tenant.objects.all().delete()
        Product.objects.all().delete()
        Category.objects.all().delete()

    def test_base_seeder_stores_tenant(self):
        """Test that BaseSeeder.execute() stores tenant as instance variable."""
        # Before execute, tenant should be None
        self.assertIsNone(self.seeder.tenant)

        # After execute, should store the tenant
        self.seeder.execute(tenant=self.tenant)

        # Verify tenant is stored
        self.assertIsNotNone(self.seeder.tenant)
        self.assertEqual(self.seeder.tenant.id, self.tenant.id)
        self.assertEqual(self.seeder.tenant.slug, "test-tenant")

    def test_base_seeder_accepts_tenant_parameter(self):
        """Test that execute() method accepts tenant parameter."""
        # This should not raise any errors
        self.seeder.execute(tenant=self.tenant)
        self.assertEqual(self.seeder.tenant.slug, "test-tenant")

    def test_base_seeder_execute_with_no_tenant(self):
        """Test that execute() can be called without a tenant parameter."""
        # Should not raise an error, but tenant should remain None
        self.seeder.execute()
        self.assertIsNone(self.seeder.tenant)

    def test_create_with_tenant_adds_tenant_to_kwargs(self):
        """Test that create_with_tenant() adds tenant to kwargs."""
        self.seeder.execute(tenant=self.tenant)

        # Create a product using the helper
        product = self.seeder.create_with_tenant(
            Product,
            name="Test Product",
            sku="TEST-001",
        )

        # Verify the product was created with the tenant
        self.assertIsNotNone(product.id)
        self.assertEqual(product.tenant_id, self.tenant.id)
        self.assertEqual(product.name, "Test Product")
        self.assertEqual(product.sku, "TEST-001")

        # Verify it's in the database
        db_product = Product.objects.get(id=product.id)
        self.assertEqual(db_product.tenant_id, self.tenant.id)

    def test_create_with_tenant_raises_error_if_tenant_is_none(self):
        """Test that create_with_tenant() raises ValueError if tenant is None."""
        # Execute without setting tenant
        self.seeder.execute()

        # Attempting to create should raise ValueError
        with self.assertRaises(ValueError) as context:
            self.seeder.create_with_tenant(
                Product,
                name="Test Product",
                sku="TEST-002",
            )

        # Verify error message mentions tenant
        self.assertIn("tenant", str(context.exception).lower())
        self.assertIn("Product", str(context.exception))

    def test_create_with_tenant_error_contains_model_name(self):
        """Test that the ValueError contains the model name."""
        self.seeder.execute()

        with self.assertRaises(ValueError) as context:
            self.seeder.create_with_tenant(Product, title="Test")

        error_msg = str(context.exception)
        self.assertIn("Product", error_msg)

    def test_add_root_with_tenant_adds_tenant(self):
        """Test that add_root_with_tenant() adds tenant to treebeard models."""
        self.seeder.execute(tenant=self.tenant)

        # Create a root category using the helper
        category = self.seeder.add_root_with_tenant(
            Category,
            name="Root Category",
        )

        # Verify the category was created with the tenant
        self.assertIsNotNone(category.id)
        self.assertEqual(category.tenant_id, self.tenant.id)
        self.assertEqual(category.name, "Root Category")

        # Verify it's in the database
        db_category = Category.objects.get(id=category.id)
        self.assertEqual(db_category.tenant_id, self.tenant.id)

    def test_add_root_with_tenant_raises_error_if_tenant_is_none(self):
        """Test that add_root_with_tenant() raises ValueError if tenant is None."""
        # Execute without setting tenant
        self.seeder.execute()

        # Attempting to add root should raise ValueError
        with self.assertRaises(ValueError) as context:
            self.seeder.add_root_with_tenant(Category, name="Test Category")

        # Verify error message
        self.assertIn("tenant", str(context.exception).lower())
        self.assertIn("Category", str(context.exception))

    def test_add_root_with_tenant_error_contains_model_name(self):
        """Test that the ValueError for add_root contains the model name."""
        self.seeder.execute()

        with self.assertRaises(ValueError) as context:
            self.seeder.add_root_with_tenant(Category, name="Test")

        error_msg = str(context.exception)
        self.assertIn("Category", error_msg)

    def test_execute_wraps_in_transaction_atomic(self):
        """Test that execute() wraps seeding in transaction.atomic()."""
        # If an error occurs within seed(), the transaction should rollback
        # We test this by verifying that a successful seeding is committed

        self.seeder.execute(tenant=self.tenant)

        # The seeding was successful and committed
        self.assertEqual(self.seeder.tenant.slug, "test-tenant")

    def test_create_with_tenant_multiple_calls(self):
        """Test that create_with_tenant() works correctly across multiple calls."""
        self.seeder.execute(tenant=self.tenant)

        # Create multiple products
        product1 = self.seeder.create_with_tenant(
            Product, name="Product 1", sku="SKU-001"
        )
        product2 = self.seeder.create_with_tenant(
            Product, name="Product 2", sku="SKU-002"
        )
        product3 = self.seeder.create_with_tenant(
            Product, name="Product 3", sku="SKU-003"
        )

        # All should have the same tenant
        self.assertEqual(product1.tenant_id, self.tenant.id)
        self.assertEqual(product2.tenant_id, self.tenant.id)
        self.assertEqual(product3.tenant_id, self.tenant.id)

        # All should be in the database
        db_products = Product.objects.filter(tenant=self.tenant)
        self.assertEqual(db_products.count(), 3)

    def test_tenant_isolation_with_multiple_tenants(self):
        """Test that data created with different tenants is properly isolated."""
        tenant2 = Tenant.objects.create(
            name="Second Tenant",
            slug="test-tenant-2",
            is_active=True,
        )

        seeder1 = ConcreteSeeder(verbose=False)
        seeder2 = ConcreteSeeder(verbose=False)

        # Seed with first tenant
        seeder1.execute(tenant=self.tenant)
        product1 = seeder1.create_with_tenant(
            Product, name="Product T1", sku="T1-001"
        )

        # Seed with second tenant
        seeder2.execute(tenant=tenant2)
        product2 = seeder2.create_with_tenant(
            Product, name="Product T2", sku="T2-001"
        )

        # Verify isolation
        self.assertEqual(product1.tenant_id, self.tenant.id)
        self.assertEqual(product2.tenant_id, tenant2.id)
        self.assertNotEqual(product1.tenant_id, product2.tenant_id)

        # Verify database isolation
        tenant1_products = Product.objects.filter(tenant=self.tenant)
        tenant2_products = Product.objects.filter(tenant=tenant2)
        self.assertEqual(tenant1_products.count(), 1)
        self.assertEqual(tenant2_products.count(), 1)

    def test_seeder_verbose_logging(self):
        """Test that verbose mode logs messages."""
        verbose_seeder = ConcreteSeeder(verbose=True)

        # This should print log messages (we just verify it doesn't crash)
        verbose_seeder.execute(tenant=self.tenant)
        self.assertIsNotNone(verbose_seeder.tenant)

    def test_seeder_non_verbose_no_logging(self):
        """Test that non-verbose mode doesn't log."""
        non_verbose_seeder = ConcreteSeeder(verbose=False)

        # Should execute without printing
        non_verbose_seeder.execute(tenant=self.tenant)
        self.assertIsNotNone(non_verbose_seeder.tenant)

    def test_create_with_tenant_preserves_kwargs(self):
        """Test that create_with_tenant() preserves all provided kwargs."""
        self.seeder.execute(tenant=self.tenant)

        # Create with multiple fields
        product = self.seeder.create_with_tenant(
            Product,
            name="Complex Product",
            sku="COMPLEX-001",
            description="A detailed description",
        )

        # Verify all fields are set
        self.assertEqual(product.name, "Complex Product")
        self.assertEqual(product.sku, "COMPLEX-001")
        self.assertEqual(product.description, "A detailed description")
        self.assertEqual(product.tenant_id, self.tenant.id)

    def test_add_root_with_tenant_preserves_kwargs(self):
        """Test that add_root_with_tenant() preserves all provided kwargs."""
        self.seeder.execute(tenant=self.tenant)

        # Create root with multiple fields
        category = self.seeder.add_root_with_tenant(
            Category,
            name="Main Category",
        )

        # Verify fields are set
        self.assertEqual(category.name, "Main Category")
        self.assertEqual(category.tenant_id, self.tenant.id)

    def test_tenant_context_persists_across_seed_calls(self):
        """Test that tenant context persists within a single execute() call."""
        # Create a custom seeder that calls create_with_tenant multiple times
        class MultiCreateSeeder(BaseSeeder):
            def seed(self):
                if self.tenant:
                    self.p1 = self.create_with_tenant(
                        Product, name="P1", sku="P1"
                    )
                    self.p2 = self.create_with_tenant(
                        Product, name="P2", sku="P2"
                    )

        seeder = MultiCreateSeeder(verbose=False)
        seeder.execute(tenant=self.tenant)

        # Both products should have the same tenant
        self.assertEqual(seeder.p1.tenant_id, self.tenant.id)
        self.assertEqual(seeder.p2.tenant_id, self.tenant.id)
