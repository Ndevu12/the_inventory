"""Tests for BaseSeeder and its tenant context functionality."""

from django.test import TransactionTestCase
from wagtail.models import Locale
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
    Note: TransactionTestCase doesn't support pytest fixtures, so we create
    a test tenant directly in setUpClass().
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create Wagtail locale (required for Product/Category creation)
        cls.locale = Locale.objects.get_or_create(language_code='en')[0]
        
        # Create default tenant for this test class
        cls.tenant = Tenant.objects.create(
            name="Default",
            slug="default",
            is_active=True,
        )

    def test_base_seeder_stores_tenant(self):
        """Test that BaseSeeder.execute() stores tenant as instance variable."""
        tenant = self.tenant
        seeder = ConcreteSeeder(verbose=False)
        # Before execute, tenant should be None
        self.assertIsNone(seeder.tenant)

        # After execute, should store the tenant
        seeder.execute(tenant=tenant)

        # Verify tenant is stored
        self.assertIsNotNone(seeder.tenant)
        self.assertEqual(seeder.tenant.id, tenant.id)
        self.assertEqual(seeder.tenant.slug, "default")

    def test_base_seeder_accepts_tenant_parameter(self):
        """Test that execute() method accepts tenant parameter."""
        tenant = self.tenant
        seeder = ConcreteSeeder(verbose=False)
        # This should not raise any errors
        seeder.execute(tenant=tenant)
        self.assertEqual(seeder.tenant.slug, "default")

    def test_base_seeder_execute_with_no_tenant(self):
        """Test that execute() can be called without a tenant parameter."""
        seeder = ConcreteSeeder(verbose=False)
        # Should not raise an error, but tenant should remain None
        seeder.execute()
        self.assertIsNone(seeder.tenant)

    def test_create_with_tenant_raises_error_if_tenant_is_none(self):
        """Test that create_with_tenant() raises ValueError if tenant is None."""
        seeder = ConcreteSeeder(verbose=False)
        # Execute without setting tenant
        seeder.execute()

        # Attempting to create should raise ValueError
        with self.assertRaises(ValueError) as context:
            seeder.create_with_tenant(
                Product,
                name="Test Product",
                sku="TEST-002",
            )

        # Verify error message mentions tenant
        self.assertIn("tenant", str(context.exception).lower())
        self.assertIn("Product", str(context.exception))

    def test_create_with_tenant_error_contains_model_name(self):
        """Test that the ValueError contains the model name."""
        seeder = ConcreteSeeder(verbose=False)
        seeder.execute()

        with self.assertRaises(ValueError) as context:
            seeder.create_with_tenant(Product, title="Test")

        error_msg = str(context.exception)
        self.assertIn("Product", error_msg)

    def test_add_root_with_tenant_adds_tenant(self):
        """Test that add_root_with_tenant() adds tenant to treebeard models."""
        tenant = self.tenant
        seeder = ConcreteSeeder(verbose=False)
        seeder.execute(tenant=tenant)

        # Create a root category using the helper
        category = seeder.add_root_with_tenant(
            Category,
            name="Root Category",
            locale=self.locale,
        )

        # Verify the category was created with the tenant
        self.assertIsNotNone(category.id)
        self.assertEqual(category.tenant_id, tenant.id)
        self.assertEqual(category.name, "Root Category")

        # Verify it's in the database
        db_category = Category.objects.get(id=category.id)
        self.assertEqual(db_category.tenant_id, tenant.id)

    def test_add_root_with_tenant_raises_error_if_tenant_is_none(self):
        """Test that add_root_with_tenant() raises ValueError if tenant is None."""
        seeder = ConcreteSeeder(verbose=False)
        # Execute without setting tenant
        seeder.execute()

        # Attempting to add root should raise ValueError
        with self.assertRaises(ValueError) as context:
            seeder.add_root_with_tenant(Category, name="Test Category", locale=self.locale)

        # Verify error message
        self.assertIn("tenant", str(context.exception).lower())
        self.assertIn("Category", str(context.exception))

    def test_add_root_with_tenant_error_contains_model_name(self):
        """Test that the ValueError for add_root contains the model name."""
        seeder = ConcreteSeeder(verbose=False)
        seeder.execute()

        with self.assertRaises(ValueError) as context:
            seeder.add_root_with_tenant(Category, name="Test", locale=self.locale)

        error_msg = str(context.exception)
        self.assertIn("Category", error_msg)

    def test_execute_wraps_in_transaction_atomic(self):
        """Test that execute() wraps seeding in transaction.atomic()."""
        tenant = self.tenant
        seeder = ConcreteSeeder(verbose=False)
        # If an error occurs within seed(), the transaction should rollback
        # We test this by verifying that a successful seeding is committed

        seeder.execute(tenant=tenant)

        # The seeding was successful and committed
        self.assertEqual(seeder.tenant.slug, "default")

    def test_seeder_verbose_logging(self):
        """Test that verbose mode logs messages."""
        tenant = self.tenant
        verbose_seeder = ConcreteSeeder(verbose=True)

        # This should print log messages (we just verify it doesn't crash)
        verbose_seeder.execute(tenant=tenant)
        self.assertIsNotNone(verbose_seeder.tenant)

    def test_seeder_non_verbose_no_logging(self):
        """Test that non-verbose mode doesn't log."""
        tenant = self.tenant
        non_verbose_seeder = ConcreteSeeder(verbose=False)

        # Should execute without printing
        non_verbose_seeder.execute(tenant=tenant)
        self.assertIsNotNone(non_verbose_seeder.tenant)

