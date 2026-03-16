"""Unit tests for StockLocation, StockRecord, and StockMovement models."""

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from inventory.models import (
    MovementType,
    StockLocation,
    StockMovement,
)

from ..factories import create_location, create_product, create_stock_record


# =====================================================================
# StockLocation
# =====================================================================


class StockLocationCreationTests(TestCase):
    """Test StockLocation creation and defaults."""

    def test_create_root_location(self):
        location = create_location(name="Main Warehouse")
        self.assertEqual(location.name, "Main Warehouse")
        self.assertTrue(location.is_active)
        self.assertEqual(location.description, "")

    def test_create_inactive_location(self):
        location = create_location(name="Closed", is_active=False)
        self.assertFalse(location.is_active)

    def test_str_returns_name(self):
        location = create_location(name="Shelf A1")
        self.assertEqual(str(location), "Shelf A1")


class StockLocationTreeTests(TestCase):
    """Test treebeard hierarchy on StockLocation."""

    def test_add_child_location(self):
        warehouse = create_location(name="Warehouse")
        aisle = warehouse.add_child(name="Aisle A")
        self.assertEqual(aisle.get_parent().pk, warehouse.pk)

    def test_nested_location_depth(self):
        warehouse = create_location(name="Warehouse")
        aisle = warehouse.add_child(name="Aisle B")
        shelf = aisle.add_child(name="Shelf 3")
        _bin = shelf.add_child(name="Bin 12")
        self.assertEqual(_bin.get_depth(), 4)

    def test_root_has_no_parent(self):
        root = create_location(name="Root Location")
        self.assertIsNone(root.get_parent())


class StockLocationSaveOverrideTests(TestCase):
    """Test save() override for treebeard MP_Node creation."""

    def test_save_creates_root_node_with_depth(self):
        """Direct save() on new instance should create a root node via add_root()."""
        location = StockLocation(name="Direct Save", description="Test")
        location.save()
        self.assertEqual(location.depth, 1)
        self.assertIsNotNone(location.path)
        self.assertEqual(location.numchild, 0)

    def test_save_multiple_root_nodes(self):
        """Multiple save() calls should create distinct root nodes, not duplicates."""
        loc1 = StockLocation(name="Warehouse A", description="")
        loc1.save()
        loc2 = StockLocation(name="Warehouse B", description="")
        loc2.save()
        self.assertEqual(loc1.depth, 1)
        self.assertEqual(loc2.depth, 1)
        self.assertNotEqual(loc1.pk, loc2.pk)
        self.assertEqual(StockLocation.objects.count(), 2)

    def test_update_existing_location_via_save(self):
        """Updating an existing location via save() should not create a duplicate."""
        location = create_location(name="Original")
        original_pk = location.pk
        location.name = "Updated"
        location.save()
        self.assertEqual(location.pk, original_pk)
        self.assertEqual(location.depth, 1)
        # Verify no duplicates created
        self.assertEqual(StockLocation.objects.filter(pk=original_pk).count(), 1)


# =====================================================================
# StockRecord
# =====================================================================


class StockRecordCreationTests(TestCase):
    """Test StockRecord creation."""

    def test_create_stock_record(self):
        product = create_product(sku="SR-001")
        location = create_location(name="Location A")
        record = create_stock_record(
            product=product, location=location, quantity=100,
        )
        self.assertEqual(record.product, product)
        self.assertEqual(record.location, location)
        self.assertEqual(record.quantity, 100)

    def test_default_quantity_is_zero(self):
        product = create_product(sku="SR-002")
        location = create_location(name="Location B")
        record = create_stock_record(product=product, location=location)
        self.assertEqual(record.quantity, 0)

    def test_str_format(self):
        product = create_product(sku="SR-003", name="Widget")
        location = create_location(name="Bin 5")
        record = create_stock_record(
            product=product, location=location, quantity=42,
        )
        self.assertEqual(str(record), "SR-003 @ Bin 5: 42")


class StockRecordUniquenessTests(TestCase):
    """Test unique_together constraint on (product, location)."""

    def test_duplicate_product_location_raises_integrity_error(self):
        product = create_product(sku="UQ-001")
        location = create_location(name="Same Location")
        create_stock_record(product=product, location=location)
        with self.assertRaises(IntegrityError):
            create_stock_record(product=product, location=location)

    def test_same_product_different_location_allowed(self):
        product = create_product(sku="UQ-002")
        loc_a = create_location(name="Location A")
        loc_b = create_location(name="Location B")
        r1 = create_stock_record(product=product, location=loc_a)
        r2 = create_stock_record(product=product, location=loc_b)
        self.assertNotEqual(r1.pk, r2.pk)


class StockRecordIsLowStockPropertyTests(TestCase):
    """Test the is_low_stock computed property."""

    def test_is_low_stock_when_below_reorder_point(self):
        product = create_product(sku="LS-001", reorder_point=10)
        location = create_location(name="Warehouse")
        record = create_stock_record(
            product=product, location=location, quantity=3,
        )
        self.assertTrue(record.is_low_stock)

    def test_is_low_stock_when_at_reorder_point(self):
        product = create_product(sku="LS-002", reorder_point=10)
        location = create_location(name="Warehouse")
        record = create_stock_record(
            product=product, location=location, quantity=10,
        )
        self.assertTrue(record.is_low_stock)

    def test_not_low_stock_when_above_reorder_point(self):
        product = create_product(sku="LS-003", reorder_point=5)
        location = create_location(name="Warehouse")
        record = create_stock_record(
            product=product, location=location, quantity=50,
        )
        self.assertFalse(record.is_low_stock)

    def test_is_low_stock_with_zero_reorder_point(self):
        """When reorder_point is 0, quantity 0 is at reorder point."""
        product = create_product(sku="LS-004", reorder_point=0)
        location = create_location(name="Warehouse")
        record = create_stock_record(
            product=product, location=location, quantity=0,
        )
        self.assertTrue(record.is_low_stock)


# =====================================================================
# StockMovement
# =====================================================================


class StockMovementStrTests(TestCase):
    """Test StockMovement __str__ representation."""

    def test_str_format(self):
        product = create_product(sku="MV-001")
        location = create_location(name="Warehouse")
        movement = StockMovement(
            product=product,
            movement_type=MovementType.RECEIVE,
            quantity=50,
            to_location=location,
        )
        # Use force_insert to bypass the immutability check (pk is None)
        movement.save()
        self.assertEqual(str(movement), "receive — MV-001 x50")


class StockMovementValidationReceiveTests(TestCase):
    """Test clean() validation for RECEIVE movements."""

    def test_receive_requires_to_location(self):
        product = create_product(sku="RV-001")
        movement = StockMovement(
            product=product,
            movement_type=MovementType.RECEIVE,
            quantity=10,
            to_location=None,
        )
        with self.assertRaises(ValidationError) as ctx:
            movement.full_clean()
        self.assertIn("to_location", ctx.exception.message_dict)

    def test_receive_rejects_from_location(self):
        product = create_product(sku="RV-002")
        location = create_location(name="Warehouse")
        movement = StockMovement(
            product=product,
            movement_type=MovementType.RECEIVE,
            quantity=10,
            from_location=location,
            to_location=location,
        )
        with self.assertRaises(ValidationError) as ctx:
            movement.full_clean()
        self.assertIn("from_location", ctx.exception.message_dict)

    def test_receive_valid(self):
        product = create_product(sku="RV-003")
        location = create_location(name="Warehouse")
        movement = StockMovement(
            product=product,
            movement_type=MovementType.RECEIVE,
            quantity=10,
            to_location=location,
        )
        movement.full_clean()


class StockMovementValidationIssueTests(TestCase):
    """Test clean() validation for ISSUE movements."""

    def test_issue_requires_from_location(self):
        product = create_product(sku="IS-001")
        movement = StockMovement(
            product=product,
            movement_type=MovementType.ISSUE,
            quantity=5,
            from_location=None,
        )
        with self.assertRaises(ValidationError) as ctx:
            movement.full_clean()
        self.assertIn("from_location", ctx.exception.message_dict)

    def test_issue_rejects_to_location(self):
        product = create_product(sku="IS-002")
        location = create_location(name="Warehouse")
        movement = StockMovement(
            product=product,
            movement_type=MovementType.ISSUE,
            quantity=5,
            from_location=location,
            to_location=location,
        )
        with self.assertRaises(ValidationError) as ctx:
            movement.full_clean()
        self.assertIn("to_location", ctx.exception.message_dict)

    def test_issue_valid(self):
        product = create_product(sku="IS-003")
        location = create_location(name="Warehouse")
        movement = StockMovement(
            product=product,
            movement_type=MovementType.ISSUE,
            quantity=5,
            from_location=location,
        )
        movement.full_clean()


class StockMovementValidationTransferTests(TestCase):
    """Test clean() validation for TRANSFER movements."""

    def test_transfer_requires_from_location(self):
        product = create_product(sku="TR-001")
        location = create_location(name="Dest")
        movement = StockMovement(
            product=product,
            movement_type=MovementType.TRANSFER,
            quantity=5,
            to_location=location,
        )
        with self.assertRaises(ValidationError) as ctx:
            movement.full_clean()
        self.assertIn("from_location", ctx.exception.message_dict)

    def test_transfer_requires_to_location(self):
        product = create_product(sku="TR-002")
        location = create_location(name="Source")
        movement = StockMovement(
            product=product,
            movement_type=MovementType.TRANSFER,
            quantity=5,
            from_location=location,
        )
        with self.assertRaises(ValidationError) as ctx:
            movement.full_clean()
        self.assertIn("to_location", ctx.exception.message_dict)

    def test_transfer_rejects_same_locations(self):
        product = create_product(sku="TR-003")
        location = create_location(name="Same Place")
        movement = StockMovement(
            product=product,
            movement_type=MovementType.TRANSFER,
            quantity=5,
            from_location=location,
            to_location=location,
        )
        with self.assertRaises(ValidationError) as ctx:
            movement.full_clean()
        self.assertIn("to_location", ctx.exception.message_dict)

    def test_transfer_valid(self):
        product = create_product(sku="TR-004")
        loc_a = create_location(name="Location A")
        loc_b = create_location(name="Location B")
        movement = StockMovement(
            product=product,
            movement_type=MovementType.TRANSFER,
            quantity=5,
            from_location=loc_a,
            to_location=loc_b,
        )
        movement.full_clean()


class StockMovementValidationAdjustmentTests(TestCase):
    """Test clean() validation for ADJUSTMENT movements."""

    def test_adjustment_requires_at_least_one_location(self):
        product = create_product(sku="ADJ-001")
        movement = StockMovement(
            product=product,
            movement_type=MovementType.ADJUSTMENT,
            quantity=5,
        )
        with self.assertRaises(ValidationError) as ctx:
            movement.full_clean()
        self.assertIn("from_location", ctx.exception.message_dict)

    def test_adjustment_valid_with_from_only(self):
        product = create_product(sku="ADJ-002")
        location = create_location(name="Warehouse")
        movement = StockMovement(
            product=product,
            movement_type=MovementType.ADJUSTMENT,
            quantity=5,
            from_location=location,
        )
        movement.full_clean()

    def test_adjustment_valid_with_to_only(self):
        product = create_product(sku="ADJ-003")
        location = create_location(name="Warehouse")
        movement = StockMovement(
            product=product,
            movement_type=MovementType.ADJUSTMENT,
            quantity=5,
            to_location=location,
        )
        movement.full_clean()

    def test_adjustment_valid_with_both_locations(self):
        product = create_product(sku="ADJ-004")
        loc_a = create_location(name="Source")
        loc_b = create_location(name="Dest")
        movement = StockMovement(
            product=product,
            movement_type=MovementType.ADJUSTMENT,
            quantity=5,
            from_location=loc_a,
            to_location=loc_b,
        )
        movement.full_clean()


class StockMovementImmutabilityTests(TestCase):
    """Test that saved movements cannot be updated."""

    def test_update_raises_validation_error(self):
        product = create_product(sku="IMM-001")
        location = create_location(name="Warehouse")
        movement = StockMovement(
            product=product,
            movement_type=MovementType.RECEIVE,
            quantity=10,
            to_location=location,
        )
        movement.save()

        movement.quantity = 20
        with self.assertRaises(ValidationError) as ctx:
            movement.save()
        self.assertIn("immutable", str(ctx.exception.message))


class StockMovementFKProtectionTests(TestCase):
    """Test PROTECT behavior on FK deletion."""

    def test_cannot_delete_product_with_movements(self):
        from django.db.models import ProtectedError

        product = create_product(sku="FK-001")
        location = create_location(name="Warehouse")
        StockMovement(
            product=product,
            movement_type=MovementType.RECEIVE,
            quantity=10,
            to_location=location,
        ).save()

        with self.assertRaises(ProtectedError):
            product.delete()

    def test_cannot_delete_location_with_movements(self):
        from django.db.models import ProtectedError

        product = create_product(sku="FK-002")
        location = create_location(name="Protected Warehouse")
        StockMovement(
            product=product,
            movement_type=MovementType.RECEIVE,
            quantity=10,
            to_location=location,
        ).save()

        with self.assertRaises(ProtectedError):
            location.delete()
