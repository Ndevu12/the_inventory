"""Tests for TimeStampedModel tenant field enforcement."""

from datetime import date

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from tenants.models import Tenant
from tenants.context import set_current_tenant, get_current_tenant, clear_current_tenant
from inventory.models import (
    Category,
    CycleStatus,
    MovementType,
    Product,
    StockLocation,
    StockRecord,
    StockMovement,
    StockLot,
    InventoryCycle,
    ReservationRule,
    StockReservation,
)


class TimeStampedModelNonNullableTenantTestCase(TestCase):
    """Tests for TimeStampedModel tenant field non-nullable enforcement.
    
    Verifies that:
    1. The tenant field is non-nullable at the database level
    2. Django model validation enforces tenant requirement
    3. All TimeStampedModel subclasses enforce tenant non-nullability
    """
    
    @classmethod
    def setUpTestData(cls):
        """Create a default tenant for testing."""
        cls.default_tenant, _ = Tenant.objects.get_or_create(
            slug="default",
            defaults={
                "name": "Default",
                "is_active": True,
            }
        )
    
    def test_tenant_field_is_non_nullable(self):
        """Test that TimeStampedModel.tenant field definition is non-nullable."""
        # Check the field definition
        from inventory.models.base import TimeStampedModel
        tenant_field = TimeStampedModel._meta.get_field('tenant')
        
        # Verify null=False and blank=False
        self.assertFalse(tenant_field.null, 
                        "tenant field should have null=False")
        self.assertFalse(tenant_field.blank,
                        "tenant field should have blank=False")
    
    def test_category_requires_tenant(self):
        """Test that Category cannot be created without tenant."""
        with self.assertRaises(ValidationError):
            Category.objects.create(
                name="Test Category",
                slug="test-category",
                # Intentionally omitting tenant
            )
    
    def test_category_with_tenant_succeeds(self):
        """Test that Category creation succeeds with tenant."""
        category = Category.objects.create(
            name="Test Category",
            slug="test-category",
            tenant=self.default_tenant,
        )
        self.assertEqual(category.tenant, self.default_tenant)
    
    def test_product_requires_tenant(self):
        """Test that Product cannot be created without tenant."""
        with self.assertRaises(ValidationError):
            Product.objects.create(
                name="Test Product",
                sku="TEST-001",
                # Intentionally omitting tenant
            )
    
    def test_product_with_tenant_succeeds(self):
        """Test that Product creation succeeds with tenant."""
        product = Product.objects.create(
            name="Test Product",
            sku="TEST-001",
            tenant=self.default_tenant,
        )
        self.assertEqual(product.tenant, self.default_tenant)
    
    def test_stock_location_requires_tenant(self):
        """Test that StockLocation cannot be created without tenant."""
        with self.assertRaises(ValidationError):
            StockLocation.add_root(
                name="Test Location",
                # Intentionally omitting tenant
            )
    
    def test_stock_location_with_tenant_succeeds(self):
        """Test that StockLocation creation succeeds with tenant."""
        location = StockLocation.add_root(
            name="Test Location",
            tenant=self.default_tenant,
        )
        self.assertEqual(location.tenant, self.default_tenant)
    
    def test_stock_record_requires_tenant(self):
        """Test that StockRecord cannot be created without tenant."""
        product = Product.objects.create(
            name="Test Product",
            sku="TEST-002",
            tenant=self.default_tenant,
        )
        location = StockLocation.add_root(
            name="Test Location",
            tenant=self.default_tenant,
        )
        
        with self.assertRaises(ValidationError):
            StockRecord.objects.create(
                product=product,
                location=location,
                quantity=0,
                # Intentionally omitting tenant
            )
    
    def test_stock_record_with_tenant_succeeds(self):
        """Test that StockRecord creation succeeds with tenant."""
        product = Product.objects.create(
            name="Test Product",
            sku="TEST-003",
            tenant=self.default_tenant,
        )
        location = StockLocation.add_root(
            name="Test Location",
            tenant=self.default_tenant,
        )
        
        record = StockRecord.objects.create(
            product=product,
            location=location,
            quantity=100,
            tenant=self.default_tenant,
        )
        self.assertEqual(record.tenant, self.default_tenant)
    
    def test_stock_movement_requires_tenant(self):
        """Test that StockMovement cannot be created without tenant."""
        product = Product.objects.create(
            name="Test Product",
            sku="TEST-004",
            tenant=self.default_tenant,
        )
        location = StockLocation.add_root(
            name="Test Location",
            tenant=self.default_tenant,
        )
        
        with self.assertRaises(ValidationError):
            StockMovement.objects.create(
                product=product,
                movement_type=MovementType.ADJUSTMENT,
                quantity=10,
                to_location=location,
                # Intentionally omitting tenant
            )
    
    def test_stock_movement_with_tenant_succeeds(self):
        """Test that StockMovement creation succeeds with tenant."""
        product = Product.objects.create(
            name="Test Product",
            sku="TEST-005",
            tenant=self.default_tenant,
        )
        location = StockLocation.add_root(
            name="Test Location",
            tenant=self.default_tenant,
        )
        
        movement = StockMovement.objects.create(
            product=product,
            movement_type=MovementType.ADJUSTMENT,
            quantity=10,
            to_location=location,
            tenant=self.default_tenant,
        )
        self.assertEqual(movement.tenant, self.default_tenant)
    
    def test_inventory_cycle_requires_tenant(self):
        """Test that InventoryCycle cannot be created without tenant."""
        with self.assertRaises(ValidationError):
            InventoryCycle.objects.create(
                name="Test Cycle",
                status=CycleStatus.SCHEDULED,
                scheduled_date=date.today(),
                # Intentionally omitting tenant
            )
    
    def test_inventory_cycle_with_tenant_succeeds(self):
        """Test that InventoryCycle creation succeeds with tenant."""
        cycle = InventoryCycle.objects.create(
            name="Test Cycle",
            status=CycleStatus.SCHEDULED,
            scheduled_date=date.today(),
            tenant=self.default_tenant,
        )
        self.assertEqual(cycle.tenant, self.default_tenant)
    
    def test_no_orphaned_data_after_migration(self):
        """Test that no data exists without a tenant (migration TS-06 verified)."""
        # This test verifies the end result of migration TS-06
        # All existing data should have a tenant now
        
        # Get counts of NULL tenant entries across all models
        models_to_check = [
            ('Category', Category),
            ('Product', Product),
            ('StockLocation', StockLocation),
            ('StockRecord', StockRecord),
            ('StockMovement', StockMovement),
            ('StockLot', StockLot),
            ('InventoryCycle', InventoryCycle),
            ('ReservationRule', ReservationRule),
            ('StockReservation', StockReservation),
        ]
        
        orphaned_data_found = False
        for model_name, model in models_to_check:
            null_count = model.objects.filter(tenant__isnull=True).count()
            if null_count > 0:
                orphaned_data_found = True
                self.fail(f"Found {null_count} orphaned {model_name} instances "
                        "without tenant (migration TS-06 may not have run)")
        
        self.assertFalse(orphaned_data_found, 
                        "All models should have tenant after migration TS-06")
    
    def test_tenant_field_cascade_delete(self):
        """Test that deleting a tenant cascades to related models."""
        # Create test data linked to a tenant
        test_tenant = Tenant.objects.create(
            name="Test Tenant",
            slug="test-tenant",
            is_active=True,
        )
        
        category = Category.objects.create(
            name="Test Category",
            slug="test-cat",
            tenant=test_tenant,
        )
        
        # Verify the category exists
        self.assertTrue(Category.objects.filter(id=category.id).exists())
        
        # Delete the tenant — should cascade to category
        test_tenant.delete()
        
        # Verify the category was deleted
        self.assertFalse(Category.objects.filter(id=category.id).exists())


class TimeStampedModelSaveValidationTestCase(TestCase):
    """Tests for TimeStampedModel save() validation."""

    @classmethod
    def setUpTestData(cls):
        """Create a default tenant for testing."""
        cls.default_tenant, _ = Tenant.objects.get_or_create(
            slug="default",
            defaults={
                "name": "Default",
                "is_active": True,
            }
        )

    def test_save_raises_validation_error_without_tenant(self):
        """Test that save() raises ValidationError if tenant is None."""
        product = Product(
            name="Test Product",
            sku="TEST-SAVE-001",
            tenant=None,  # Explicitly set to None
        )
        
        with self.assertRaises(ValidationError) as cm:
            product.save()
        
        self.assertIn("tenant", str(cm.exception).lower())

    def test_save_succeeds_with_tenant(self):
        """Test that save() succeeds when tenant is set."""
        product = Product(
            name="Test Product",
            sku="TEST-SAVE-002",
            tenant=self.default_tenant,
        )
        
        # Should not raise
        product.save()
        self.assertEqual(product.tenant, self.default_tenant)
        self.assertTrue(Product.objects.filter(id=product.id).exists())

    def test_save_validation_error_message(self):
        """Test that ValidationError message is informative."""
        category = Category(
            name="Test Category",
            slug="test-cat-save",
            tenant=None,
        )
        
        with self.assertRaises(ValidationError) as cm:
            category.save()
        
        error_message = str(cm.exception)
        self.assertIn("Category", error_message)
        self.assertIn("tenant", error_message.lower())


class TenantAwareManagerTestCase(TestCase):
    """Tests for TenantAwareManager and TenantAwareQuerySet."""

    @classmethod
    def setUpTestData(cls):
        """Create test tenants and data."""
        cls.tenant_a, _ = Tenant.objects.get_or_create(
            slug="tenant-a",
            defaults={
                "name": "Tenant A",
                "is_active": True,
            }
        )
        cls.tenant_b, _ = Tenant.objects.get_or_create(
            slug="tenant-b",
            defaults={
                "name": "Tenant B",
                "is_active": True,
            }
        )
        
        # Create products for each tenant
        cls.product_a1 = Product.objects.create(
            name="Product A1",
            sku="SKU-A1",
            tenant=cls.tenant_a,
        )
        cls.product_a2 = Product.objects.create(
            name="Product A2",
            sku="SKU-A2",
            tenant=cls.tenant_a,
        )
        cls.product_b1 = Product.objects.create(
            name="Product B1",
            sku="SKU-B1",
            tenant=cls.tenant_b,
        )

    def tearDown(self):
        """Clear tenant context after each test."""
        clear_current_tenant()

    def test_filter_by_current_tenant_returns_correct_records(self):
        """Test that filter_by_current_tenant() returns only current tenant's data."""
        set_current_tenant(self.tenant_a)
        
        products = Product.objects.filter_by_current_tenant()
        
        self.assertEqual(products.count(), 2)
        self.assertIn(self.product_a1, products)
        self.assertIn(self.product_a2, products)
        self.assertNotIn(self.product_b1, products)

    def test_filter_by_current_tenant_with_different_tenant(self):
        """Test that filter_by_current_tenant() switches correctly between tenants."""
        set_current_tenant(self.tenant_b)
        
        products = Product.objects.filter_by_current_tenant()
        
        self.assertEqual(products.count(), 1)
        self.assertIn(self.product_b1, products)
        self.assertNotIn(self.product_a1, products)

    def test_filter_by_current_tenant_returns_empty_when_no_tenant_set(self):
        """Test that filter_by_current_tenant() returns empty if no tenant is currently set."""
        # Ensure no tenant is set
        clear_current_tenant()
        self.assertIsNone(get_current_tenant())
        
        products = Product.objects.filter_by_current_tenant()
        
        self.assertEqual(products.count(), 0)

    def test_filter_by_current_tenant_chaining(self):
        """Test that filter_by_current_tenant() result can be chained with other filters."""
        set_current_tenant(self.tenant_a)
        
        # Chain with additional filter
        products = Product.objects.filter_by_current_tenant().filter(
            sku__endswith="1"
        )
        
        self.assertEqual(products.count(), 1)
        self.assertEqual(products.first().sku, "SKU-A1")

    def test_filter_by_current_tenant_with_multiple_models(self):
        """Test that filter_by_current_tenant() works across different models."""
        # Create categories for each tenant
        cat_a = Category.objects.create(
            name="Category A",
            slug="cat-a",
            tenant=self.tenant_a,
        )
        Category.objects.create(
            name="Category B",
            slug="cat-b",
            tenant=self.tenant_b,
        )
        
        set_current_tenant(self.tenant_a)
        
        products = Product.objects.filter_by_current_tenant()
        categories = Category.objects.filter_by_current_tenant()
        
        self.assertEqual(products.count(), 2)
        self.assertEqual(categories.count(), 1)
        self.assertIn(cat_a, categories)

    def test_manager_get_queryset_returns_tenant_aware(self):
        """Test that the manager returns a ProductQuerySet."""
        queryset = Product.objects.all()
        
        from inventory.models.product import ProductQuerySet
        self.assertIsInstance(queryset, ProductQuerySet)

    def test_filter_by_current_tenant_preserves_filtering(self):
        """Test that filter_by_current_tenant() works with other query methods."""
        set_current_tenant(self.tenant_a)
        
        # Test with count()
        count = Product.objects.filter_by_current_tenant().count()
        self.assertEqual(count, 2)
        
        # Test with exists()
        exists = Product.objects.filter_by_current_tenant().exists()
        self.assertTrue(exists)
        
        # Test with first()
        first = Product.objects.filter_by_current_tenant().first()
        self.assertIn(first, [self.product_a1, self.product_a2])


