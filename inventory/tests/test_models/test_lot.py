"""Unit tests for the StockLot and StockMovementLot models."""

from datetime import date, timedelta

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import ProtectedError
from django.test import TestCase

from inventory.models import MovementType, StockLot, StockMovementLot

from ..factories import (
    create_location,
    create_product,
    create_stock_lot,
    create_stock_movement,
    create_tenant,
)


class StockLotCreationTests(TestCase):
    """Test StockLot creation and field defaults."""

    def setUp(self):
        self.product = create_product(sku="LOT-P001")

    def test_create_lot_with_required_fields(self):
        lot = create_stock_lot(
            product=self.product,
            lot_number="BATCH-001",
            quantity_received=50,
            quantity_remaining=50,
            received_date=date(2026, 1, 15),
        )
        self.assertEqual(lot.product, self.product)
        self.assertEqual(lot.lot_number, "BATCH-001")
        self.assertEqual(lot.quantity_received, 50)
        self.assertEqual(lot.quantity_remaining, 50)
        self.assertEqual(lot.received_date, date(2026, 1, 15))
        self.assertTrue(lot.is_active)

    def test_create_lot_with_optional_fields(self):
        lot = create_stock_lot(
            product=self.product,
            lot_number="BATCH-002",
            serial_number="SN-12345",
            manufacturing_date=date(2025, 6, 1),
            expiry_date=date(2027, 6, 1),
        )
        self.assertEqual(lot.serial_number, "SN-12345")
        self.assertEqual(lot.manufacturing_date, date(2025, 6, 1))
        self.assertEqual(lot.expiry_date, date(2027, 6, 1))

    def test_default_serial_number_is_blank(self):
        lot = create_stock_lot(product=self.product, lot_number="BATCH-003")
        self.assertEqual(lot.serial_number, "")

    def test_default_is_active_true(self):
        lot = create_stock_lot(product=self.product, lot_number="BATCH-004")
        self.assertTrue(lot.is_active)

    def test_create_inactive_lot(self):
        lot = create_stock_lot(
            product=self.product,
            lot_number="BATCH-005",
            is_active=False,
        )
        self.assertFalse(lot.is_active)

    def test_str_representation(self):
        lot = create_stock_lot(
            product=self.product,
            lot_number="BATCH-006",
        )
        self.assertEqual(str(lot), "LOT-P001 — Lot BATCH-006")

    def test_supplier_and_purchase_order_nullable(self):
        lot = create_stock_lot(product=self.product, lot_number="BATCH-007")
        self.assertIsNone(lot.supplier)
        self.assertIsNone(lot.purchase_order)


class StockLotUniquenessConstraintTests(TestCase):
    """Test the unique constraint on (tenant, product, lot_number)."""

    def setUp(self):
        self.tenant = create_tenant(name="Acme", slug="acme")
        self.product = create_product(sku="UQ-LOT-001", tenant=self.tenant)

    def test_duplicate_lot_number_same_product_same_tenant_raises(self):
        create_stock_lot(
            product=self.product,
            lot_number="DUPE-001",
            tenant=self.tenant,
        )
        with self.assertRaises(IntegrityError):
            create_stock_lot(
                product=self.product,
                lot_number="DUPE-001",
                tenant=self.tenant,
            )

    def test_same_lot_number_different_products_allowed(self):
        product_b = create_product(sku="UQ-LOT-002", tenant=self.tenant)
        lot_a = create_stock_lot(
            product=self.product,
            lot_number="SHARED-001",
            tenant=self.tenant,
        )
        lot_b = create_stock_lot(
            product=product_b,
            lot_number="SHARED-001",
            tenant=self.tenant,
        )
        self.assertNotEqual(lot_a.pk, lot_b.pk)

    def test_same_lot_number_different_tenants_allowed(self):
        tenant_b = create_tenant(name="Beta Corp", slug="beta-corp")
        product_b = create_product(sku="UQ-LOT-001", tenant=tenant_b)
        lot_a = create_stock_lot(
            product=self.product,
            lot_number="CROSS-001",
            tenant=self.tenant,
        )
        lot_b = create_stock_lot(
            product=product_b,
            lot_number="CROSS-001",
            tenant=tenant_b,
        )
        self.assertNotEqual(lot_a.pk, lot_b.pk)


class StockLotIsExpiredTests(TestCase):
    """Test the is_expired() helper method."""

    def setUp(self):
        self.product = create_product(sku="EXP-001")

    def test_expired_when_past_expiry_date(self):
        lot = create_stock_lot(
            product=self.product,
            lot_number="EXP-PAST",
            expiry_date=date.today() - timedelta(days=1),
        )
        self.assertTrue(lot.is_expired())

    def test_not_expired_when_future_expiry_date(self):
        lot = create_stock_lot(
            product=self.product,
            lot_number="EXP-FUTURE",
            expiry_date=date.today() + timedelta(days=30),
        )
        self.assertFalse(lot.is_expired())

    def test_not_expired_on_expiry_date(self):
        lot = create_stock_lot(
            product=self.product,
            lot_number="EXP-TODAY",
            expiry_date=date.today(),
        )
        self.assertFalse(lot.is_expired())

    def test_not_expired_when_no_expiry_date(self):
        lot = create_stock_lot(
            product=self.product,
            lot_number="EXP-NONE",
            expiry_date=None,
        )
        self.assertFalse(lot.is_expired())


class StockLotDaysToExpiryTests(TestCase):
    """Test the days_to_expiry() helper method."""

    def setUp(self):
        self.product = create_product(sku="DTE-001")

    def test_positive_days_when_not_expired(self):
        lot = create_stock_lot(
            product=self.product,
            lot_number="DTE-POS",
            expiry_date=date.today() + timedelta(days=10),
        )
        self.assertEqual(lot.days_to_expiry(), 10)

    def test_zero_days_on_expiry_date(self):
        lot = create_stock_lot(
            product=self.product,
            lot_number="DTE-ZERO",
            expiry_date=date.today(),
        )
        self.assertEqual(lot.days_to_expiry(), 0)

    def test_negative_days_when_expired(self):
        lot = create_stock_lot(
            product=self.product,
            lot_number="DTE-NEG",
            expiry_date=date.today() - timedelta(days=5),
        )
        self.assertEqual(lot.days_to_expiry(), -5)

    def test_none_when_no_expiry_date(self):
        lot = create_stock_lot(
            product=self.product,
            lot_number="DTE-NONE",
            expiry_date=None,
        )
        self.assertIsNone(lot.days_to_expiry())


class StockLotValidationTests(TestCase):
    """Test clean() validation logic."""

    def setUp(self):
        self.product = create_product(sku="VAL-001")

    def test_quantity_remaining_cannot_exceed_received(self):
        lot = StockLot(
            product=self.product,
            lot_number="VAL-QTY",
            quantity_received=50,
            quantity_remaining=100,
            received_date=date.today(),
        )
        with self.assertRaises(ValidationError) as ctx:
            lot.full_clean()
        self.assertIn("quantity_remaining", ctx.exception.message_dict)

    def test_expiry_date_must_be_after_manufacturing_date(self):
        lot = StockLot(
            product=self.product,
            lot_number="VAL-DATE",
            quantity_received=50,
            quantity_remaining=50,
            received_date=date.today(),
            manufacturing_date=date(2026, 6, 1),
            expiry_date=date(2026, 1, 1),
        )
        with self.assertRaises(ValidationError) as ctx:
            lot.full_clean()
        self.assertIn("expiry_date", ctx.exception.message_dict)

    def test_expiry_date_equal_to_manufacturing_date_invalid(self):
        lot = StockLot(
            product=self.product,
            lot_number="VAL-EQ",
            quantity_received=50,
            quantity_remaining=50,
            received_date=date.today(),
            manufacturing_date=date(2026, 3, 1),
            expiry_date=date(2026, 3, 1),
        )
        with self.assertRaises(ValidationError) as ctx:
            lot.full_clean()
        self.assertIn("expiry_date", ctx.exception.message_dict)

    def test_valid_lot_passes_clean(self):
        lot = StockLot(
            product=self.product,
            lot_number="VAL-OK",
            quantity_received=100,
            quantity_remaining=80,
            received_date=date.today(),
            manufacturing_date=date(2025, 1, 1),
            expiry_date=date(2027, 1, 1),
        )
        lot.full_clean()


class StockLotOrderingTests(TestCase):
    """Test default ordering by received_date, pk."""

    def test_lots_ordered_by_received_date(self):
        product = create_product(sku="ORD-001")
        lot_newer = create_stock_lot(
            product=product,
            lot_number="ORD-NEW",
            received_date=date(2026, 3, 1),
        )
        lot_older = create_stock_lot(
            product=product,
            lot_number="ORD-OLD",
            received_date=date(2025, 1, 1),
        )
        lots = list(StockLot.objects.filter(product=product))
        self.assertEqual(lots[0].pk, lot_older.pk)
        self.assertEqual(lots[1].pk, lot_newer.pk)


class StockLotCascadeDeleteTests(TestCase):
    """Test FK cascade behavior."""

    def test_deleting_product_deletes_lots(self):
        product = create_product(sku="DEL-001")
        create_stock_lot(product=product, lot_number="DEL-LOT-001")
        create_stock_lot(product=product, lot_number="DEL-LOT-002")
        self.assertEqual(StockLot.objects.filter(product=product).count(), 2)
        product.delete()
        self.assertEqual(StockLot.objects.count(), 0)


# =====================================================================
# StockMovementLot
# =====================================================================


class StockMovementLotCreationTests(TestCase):
    """Test StockMovementLot creation and field values."""

    def setUp(self):
        self.product = create_product(sku="SML-001")
        self.location = create_location(name="SML Warehouse")
        self.lot = create_stock_lot(
            product=self.product, lot_number="SML-BATCH-001",
        )
        self.movement = create_stock_movement(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=50,
            to_location=self.location,
        )

    def test_create_stock_movement_lot(self):
        sml = StockMovementLot.objects.create(
            stock_movement=self.movement,
            stock_lot=self.lot,
            quantity=50,
        )
        self.assertEqual(sml.stock_movement, self.movement)
        self.assertEqual(sml.stock_lot, self.lot)
        self.assertEqual(sml.quantity, 50)

    def test_str_representation(self):
        sml = StockMovementLot.objects.create(
            stock_movement=self.movement,
            stock_lot=self.lot,
            quantity=25,
        )
        expected = (
            f"Movement #{self.movement.pk} "
            f"← Lot SML-BATCH-001 x25"
        )
        self.assertEqual(str(sml), expected)


class StockMovementLotUniquenessTests(TestCase):
    """Test unique_together constraint on (stock_movement, stock_lot)."""

    def setUp(self):
        self.product = create_product(sku="SML-UQ-001")
        self.location = create_location(name="SML UQ Warehouse")
        self.lot = create_stock_lot(
            product=self.product, lot_number="SML-UQ-BATCH",
        )
        self.movement = create_stock_movement(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=100,
            to_location=self.location,
        )

    def test_duplicate_movement_lot_raises_integrity_error(self):
        StockMovementLot.objects.create(
            stock_movement=self.movement,
            stock_lot=self.lot,
            quantity=50,
        )
        with self.assertRaises(IntegrityError):
            StockMovementLot.objects.create(
                stock_movement=self.movement,
                stock_lot=self.lot,
                quantity=30,
            )

    def test_same_lot_different_movements_allowed(self):
        movement_b = create_stock_movement(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=25,
            to_location=self.location,
        )
        sml_a = StockMovementLot.objects.create(
            stock_movement=self.movement,
            stock_lot=self.lot,
            quantity=50,
        )
        sml_b = StockMovementLot.objects.create(
            stock_movement=movement_b,
            stock_lot=self.lot,
            quantity=25,
        )
        self.assertNotEqual(sml_a.pk, sml_b.pk)

    def test_same_movement_different_lots_allowed(self):
        lot_b = create_stock_lot(
            product=self.product, lot_number="SML-UQ-BATCH-B",
        )
        sml_a = StockMovementLot.objects.create(
            stock_movement=self.movement,
            stock_lot=self.lot,
            quantity=60,
        )
        sml_b = StockMovementLot.objects.create(
            stock_movement=self.movement,
            stock_lot=lot_b,
            quantity=40,
        )
        self.assertNotEqual(sml_a.pk, sml_b.pk)


class StockMovementLotFKProtectionTests(TestCase):
    """Test FK cascade/protect behavior."""

    def setUp(self):
        self.product = create_product(sku="SML-FK-001")
        self.location = create_location(name="SML FK Warehouse")
        self.lot = create_stock_lot(
            product=self.product, lot_number="SML-FK-BATCH",
        )
        self.movement = create_stock_movement(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=100,
            to_location=self.location,
        )
        StockMovementLot.objects.create(
            stock_movement=self.movement,
            stock_lot=self.lot,
            quantity=100,
        )

    def test_cannot_delete_lot_with_allocations(self):
        """StockLot FK uses PROTECT — deleting a referenced lot raises."""
        with self.assertRaises(ProtectedError):
            self.lot.delete()

    def test_deleting_movement_cascades_to_allocations(self):
        """StockMovement FK uses CASCADE — allocations are removed."""
        self.assertEqual(StockMovementLot.objects.count(), 1)
        self.movement.delete()
        self.assertEqual(StockMovementLot.objects.count(), 0)
