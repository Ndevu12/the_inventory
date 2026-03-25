"""Unit tests for BulkStockService.

Tests cover all three bulk operations (transfer, adjustment, revalue)
with both fail_fast modes, including edge cases such as empty lists,
all-invalid items, partial failures, and no-op adjustments.
"""

from decimal import Decimal

from django.test import TestCase

from inventory.exceptions import InventoryError
from inventory.models import StockRecord
from inventory.services.bulk import BulkOperationResult, BulkStockService

from ..factories import create_location, create_product, create_stock_record, create_tenant


class BulkServiceSetupMixin:
    """Shared setUp for BulkStockService tests."""

    def setUp(self):
        self.service = BulkStockService()
        self.tenant = create_tenant()
        self.warehouse = create_location(name="Bulk Warehouse", tenant=self.tenant)
        self.store = create_location(name="Bulk Store", tenant=self.tenant)
        self.product_a = create_product(
            sku="BULK-A", unit_cost=Decimal("10.00"), tenant=self.tenant,
        )
        self.product_b = create_product(
            sku="BULK-B", unit_cost=Decimal("20.00"), tenant=self.tenant,
        )
        self.product_c = create_product(
            sku="BULK-C", unit_cost=Decimal("30.00"), tenant=self.tenant,
        )


# =====================================================================
# BulkOperationResult
# =====================================================================


class BulkOperationResultTests(TestCase):

    def test_initial_state(self):
        result = BulkOperationResult()
        self.assertEqual(result.success_count, 0)
        self.assertEqual(result.failure_count, 0)
        self.assertEqual(result.errors, [])
        self.assertEqual(result.total_count, 0)

    def test_total_count(self):
        result = BulkOperationResult(success_count=3, failure_count=2)
        self.assertEqual(result.total_count, 5)


# =====================================================================
# Bulk Transfer — fail_fast=True (default, all-or-nothing)
# =====================================================================


class BulkTransferAtomicTests(BulkServiceSetupMixin, TestCase):

    def test_transfer_all_succeed(self):
        create_stock_record(product=self.product_a, location=self.warehouse, quantity=100)
        create_stock_record(product=self.product_b, location=self.warehouse, quantity=200)

        result = self.service.bulk_transfer(
            items=[
                {"product_id": self.product_a.pk, "quantity": 30},
                {"product_id": self.product_b.pk, "quantity": 50},
            ],
            from_location=self.warehouse,
            to_location=self.store,
            fail_fast=True,
        )

        self.assertEqual(result.success_count, 2)
        self.assertEqual(result.failure_count, 0)
        self.assertEqual(result.errors, [])

        rec_a = StockRecord.objects.get(product=self.product_a, location=self.warehouse)
        rec_b = StockRecord.objects.get(product=self.product_b, location=self.warehouse)
        self.assertEqual(rec_a.quantity, 70)
        self.assertEqual(rec_b.quantity, 150)

        dest_a = StockRecord.objects.get(product=self.product_a, location=self.store)
        dest_b = StockRecord.objects.get(product=self.product_b, location=self.store)
        self.assertEqual(dest_a.quantity, 30)
        self.assertEqual(dest_b.quantity, 50)

    def test_transfer_fail_fast_rolls_back_all(self):
        """When second item fails, the first item's transfer is also rolled back."""
        create_stock_record(product=self.product_a, location=self.warehouse, quantity=100)
        create_stock_record(product=self.product_b, location=self.warehouse, quantity=5)

        with self.assertRaises(InventoryError):
            self.service.bulk_transfer(
                items=[
                    {"product_id": self.product_a.pk, "quantity": 30},
                    {"product_id": self.product_b.pk, "quantity": 50},
                ],
                from_location=self.warehouse,
                to_location=self.store,
                fail_fast=True,
            )

        rec_a = StockRecord.objects.get(product=self.product_a, location=self.warehouse)
        self.assertEqual(rec_a.quantity, 100)
        self.assertFalse(
            StockRecord.objects.filter(product=self.product_a, location=self.store).exists()
        )

    def test_transfer_fail_fast_invalid_product(self):
        create_stock_record(product=self.product_a, location=self.warehouse, quantity=100)

        with self.assertRaises(InventoryError):
            self.service.bulk_transfer(
                items=[
                    {"product_id": self.product_a.pk, "quantity": 10},
                    {"product_id": 99999, "quantity": 10},
                ],
                from_location=self.warehouse,
                to_location=self.store,
                fail_fast=True,
            )

        rec_a = StockRecord.objects.get(product=self.product_a, location=self.warehouse)
        self.assertEqual(rec_a.quantity, 100)

    def test_transfer_single_item(self):
        create_stock_record(product=self.product_a, location=self.warehouse, quantity=50)

        result = self.service.bulk_transfer(
            items=[{"product_id": self.product_a.pk, "quantity": 20}],
            from_location=self.warehouse,
            to_location=self.store,
            fail_fast=True,
        )

        self.assertEqual(result.success_count, 1)
        self.assertEqual(result.failure_count, 0)


# =====================================================================
# Bulk Transfer — fail_fast=False (partial success)
# =====================================================================


class BulkTransferPartialTests(BulkServiceSetupMixin, TestCase):

    def test_partial_failure_continues(self):
        """Valid items succeed even when one item fails."""
        create_stock_record(product=self.product_a, location=self.warehouse, quantity=100)
        create_stock_record(product=self.product_b, location=self.warehouse, quantity=5)

        result = self.service.bulk_transfer(
            items=[
                {"product_id": self.product_a.pk, "quantity": 30},
                {"product_id": self.product_b.pk, "quantity": 50},
            ],
            from_location=self.warehouse,
            to_location=self.store,
            fail_fast=False,
        )

        self.assertEqual(result.success_count, 1)
        self.assertEqual(result.failure_count, 1)
        self.assertEqual(len(result.errors), 1)
        self.assertEqual(result.errors[0]["product_id"], self.product_b.pk)

        rec_a = StockRecord.objects.get(product=self.product_a, location=self.warehouse)
        self.assertEqual(rec_a.quantity, 70)

    def test_all_items_invalid(self):
        result = self.service.bulk_transfer(
            items=[
                {"product_id": 99998, "quantity": 10},
                {"product_id": 99999, "quantity": 10},
            ],
            from_location=self.warehouse,
            to_location=self.store,
            fail_fast=False,
        )

        self.assertEqual(result.success_count, 0)
        self.assertEqual(result.failure_count, 2)
        self.assertEqual(len(result.errors), 2)

    def test_missing_product_id(self):
        result = self.service.bulk_transfer(
            items=[{"quantity": 10}],
            from_location=self.warehouse,
            to_location=self.store,
            fail_fast=False,
        )

        self.assertEqual(result.failure_count, 1)
        self.assertIn("Missing product_id", result.errors[0]["error"])


# =====================================================================
# Bulk Adjustment — fail_fast=True
# =====================================================================


class BulkAdjustmentAtomicTests(BulkServiceSetupMixin, TestCase):

    def test_adjustment_increases_and_decreases(self):
        create_stock_record(product=self.product_a, location=self.warehouse, quantity=50)
        create_stock_record(product=self.product_b, location=self.warehouse, quantity=100)

        result = self.service.bulk_adjustment(
            items=[
                {"product_id": self.product_a.pk, "new_quantity": 80},
                {"product_id": self.product_b.pk, "new_quantity": 60},
            ],
            location=self.warehouse,
            fail_fast=True,
        )

        self.assertEqual(result.success_count, 2)
        self.assertEqual(result.failure_count, 0)

        rec_a = StockRecord.objects.get(product=self.product_a, location=self.warehouse)
        rec_b = StockRecord.objects.get(product=self.product_b, location=self.warehouse)
        self.assertEqual(rec_a.quantity, 80)
        self.assertEqual(rec_b.quantity, 60)

    def test_adjustment_no_op_for_same_quantity(self):
        create_stock_record(product=self.product_a, location=self.warehouse, quantity=50)

        result = self.service.bulk_adjustment(
            items=[{"product_id": self.product_a.pk, "new_quantity": 50}],
            location=self.warehouse,
            fail_fast=True,
        )

        self.assertEqual(result.success_count, 1)
        self.assertEqual(result.failure_count, 0)

        rec = StockRecord.objects.get(product=self.product_a, location=self.warehouse)
        self.assertEqual(rec.quantity, 50)

    def test_adjustment_creates_record_if_missing(self):
        result = self.service.bulk_adjustment(
            items=[{"product_id": self.product_a.pk, "new_quantity": 75}],
            location=self.warehouse,
            fail_fast=True,
        )

        self.assertEqual(result.success_count, 1)
        rec = StockRecord.objects.get(product=self.product_a, location=self.warehouse)
        self.assertEqual(rec.quantity, 75)

    def test_adjustment_fail_fast_rolls_back(self):
        """Excessive reduction on second item rolls back all adjustments."""
        create_stock_record(product=self.product_a, location=self.warehouse, quantity=100)
        create_stock_record(product=self.product_b, location=self.warehouse, quantity=10)

        with self.assertRaises(InventoryError):
            self.service.bulk_adjustment(
                items=[
                    {"product_id": self.product_a.pk, "new_quantity": 200},
                    {"product_id": self.product_b.pk, "new_quantity": 0},
                    {"product_id": 99999, "new_quantity": 50},
                ],
                location=self.warehouse,
                fail_fast=True,
            )

        rec_a = StockRecord.objects.get(product=self.product_a, location=self.warehouse)
        self.assertEqual(rec_a.quantity, 100)

    def test_adjustment_with_notes(self):
        create_stock_record(product=self.product_a, location=self.warehouse, quantity=10)

        result = self.service.bulk_adjustment(
            items=[{"product_id": self.product_a.pk, "new_quantity": 20}],
            location=self.warehouse,
            notes="Cycle count correction",
            fail_fast=True,
        )

        self.assertEqual(result.success_count, 1)


# =====================================================================
# Bulk Adjustment — fail_fast=False
# =====================================================================


class BulkAdjustmentPartialTests(BulkServiceSetupMixin, TestCase):

    def test_partial_adjustment_continues(self):
        create_stock_record(product=self.product_a, location=self.warehouse, quantity=50)

        result = self.service.bulk_adjustment(
            items=[
                {"product_id": self.product_a.pk, "new_quantity": 100},
                {"product_id": 99999, "new_quantity": 50},
            ],
            location=self.warehouse,
            fail_fast=False,
        )

        self.assertEqual(result.success_count, 1)
        self.assertEqual(result.failure_count, 1)

        rec = StockRecord.objects.get(product=self.product_a, location=self.warehouse)
        self.assertEqual(rec.quantity, 100)


# =====================================================================
# Bulk Revalue — fail_fast=True
# =====================================================================


class BulkRevalueAtomicTests(BulkServiceSetupMixin, TestCase):

    def test_revalue_all_succeed(self):
        result = self.service.bulk_revalue(
            items=[
                {"product_id": self.product_a.pk, "new_unit_cost": "15.00"},
                {"product_id": self.product_b.pk, "new_unit_cost": "25.00"},
            ],
            fail_fast=True,
        )

        self.assertEqual(result.success_count, 2)
        self.assertEqual(result.failure_count, 0)

        self.product_a.refresh_from_db()
        self.product_b.refresh_from_db()
        self.assertEqual(self.product_a.unit_cost, Decimal("15.00"))
        self.assertEqual(self.product_b.unit_cost, Decimal("25.00"))

    def test_revalue_fail_fast_rolls_back(self):
        with self.assertRaises(Exception):
            self.service.bulk_revalue(
                items=[
                    {"product_id": self.product_a.pk, "new_unit_cost": "15.00"},
                    {"product_id": 99999, "new_unit_cost": "25.00"},
                ],
                fail_fast=True,
            )

        self.product_a.refresh_from_db()
        self.assertEqual(self.product_a.unit_cost, Decimal("10.00"))

    def test_revalue_negative_cost_raises(self):
        with self.assertRaises(Exception):
            self.service.bulk_revalue(
                items=[
                    {"product_id": self.product_a.pk, "new_unit_cost": "-5.00"},
                ],
                fail_fast=True,
            )

        self.product_a.refresh_from_db()
        self.assertEqual(self.product_a.unit_cost, Decimal("10.00"))

    def test_revalue_zero_cost_succeeds(self):
        result = self.service.bulk_revalue(
            items=[{"product_id": self.product_a.pk, "new_unit_cost": "0.00"}],
            fail_fast=True,
        )

        self.assertEqual(result.success_count, 1)
        self.product_a.refresh_from_db()
        self.assertEqual(self.product_a.unit_cost, Decimal("0.00"))

    def test_revalue_accepts_decimal_objects(self):
        result = self.service.bulk_revalue(
            items=[{"product_id": self.product_a.pk, "new_unit_cost": Decimal("12.50")}],
            fail_fast=True,
        )

        self.assertEqual(result.success_count, 1)
        self.product_a.refresh_from_db()
        self.assertEqual(self.product_a.unit_cost, Decimal("12.50"))


# =====================================================================
# Bulk Revalue — fail_fast=False
# =====================================================================


class BulkRevaluePartialTests(BulkServiceSetupMixin, TestCase):

    def test_partial_revalue_continues(self):
        result = self.service.bulk_revalue(
            items=[
                {"product_id": self.product_a.pk, "new_unit_cost": "99.99"},
                {"product_id": 99999, "new_unit_cost": "50.00"},
            ],
            fail_fast=False,
        )

        self.assertEqual(result.success_count, 1)
        self.assertEqual(result.failure_count, 1)

        self.product_a.refresh_from_db()
        self.assertEqual(self.product_a.unit_cost, Decimal("99.99"))

    def test_all_items_invalid_revalue(self):
        result = self.service.bulk_revalue(
            items=[
                {"product_id": 99998, "new_unit_cost": "10.00"},
                {"product_id": 99999, "new_unit_cost": "20.00"},
            ],
            fail_fast=False,
        )

        self.assertEqual(result.success_count, 0)
        self.assertEqual(result.failure_count, 2)
        self.assertEqual(len(result.errors), 2)

    def test_partial_revalue_negative_cost_skips(self):
        result = self.service.bulk_revalue(
            items=[
                {"product_id": self.product_a.pk, "new_unit_cost": "-5.00"},
                {"product_id": self.product_b.pk, "new_unit_cost": "50.00"},
            ],
            fail_fast=False,
        )

        self.assertEqual(result.success_count, 1)
        self.assertEqual(result.failure_count, 1)

        self.product_a.refresh_from_db()
        self.product_b.refresh_from_db()
        self.assertEqual(self.product_a.unit_cost, Decimal("10.00"))
        self.assertEqual(self.product_b.unit_cost, Decimal("50.00"))


# =====================================================================
# Edge Cases
# =====================================================================


class BulkEdgeCaseTests(BulkServiceSetupMixin, TestCase):

    def test_empty_items_transfer_partial(self):
        """Empty items list produces zero-count result."""
        result = self.service.bulk_transfer(
            items=[],
            from_location=self.warehouse,
            to_location=self.store,
            fail_fast=False,
        )
        self.assertEqual(result.success_count, 0)
        self.assertEqual(result.failure_count, 0)

    def test_empty_items_adjustment_partial(self):
        result = self.service.bulk_adjustment(
            items=[],
            location=self.warehouse,
            fail_fast=False,
        )
        self.assertEqual(result.success_count, 0)
        self.assertEqual(result.failure_count, 0)

    def test_empty_items_revalue_partial(self):
        result = self.service.bulk_revalue(items=[], fail_fast=False)
        self.assertEqual(result.success_count, 0)
        self.assertEqual(result.failure_count, 0)

    def test_large_batch_transfer(self):
        """Verify a batch with many items processes correctly."""
        products = []
        for i in range(20):
            p = create_product(
                sku=f"BATCH-{i:03d}", unit_cost=Decimal("5.00"), tenant=self.tenant,
            )
            create_stock_record(product=p, location=self.warehouse, quantity=100)
            products.append(p)

        items = [{"product_id": p.pk, "quantity": 10} for p in products]
        result = self.service.bulk_transfer(
            items=items,
            from_location=self.warehouse,
            to_location=self.store,
            fail_fast=True,
        )

        self.assertEqual(result.success_count, 20)
        self.assertEqual(result.failure_count, 0)

        for p in products:
            rec = StockRecord.objects.get(product=p, location=self.warehouse)
            self.assertEqual(rec.quantity, 90)

    def test_duplicate_product_in_batch_transfers_twice(self):
        create_stock_record(product=self.product_a, location=self.warehouse, quantity=100)

        result = self.service.bulk_transfer(
            items=[
                {"product_id": self.product_a.pk, "quantity": 10},
                {"product_id": self.product_a.pk, "quantity": 20},
            ],
            from_location=self.warehouse,
            to_location=self.store,
            fail_fast=True,
        )

        self.assertEqual(result.success_count, 2)
        rec = StockRecord.objects.get(product=self.product_a, location=self.warehouse)
        self.assertEqual(rec.quantity, 70)
        dest = StockRecord.objects.get(product=self.product_a, location=self.store)
        self.assertEqual(dest.quantity, 30)

    def test_adjustment_to_zero(self):
        create_stock_record(product=self.product_a, location=self.warehouse, quantity=50)

        result = self.service.bulk_adjustment(
            items=[{"product_id": self.product_a.pk, "new_quantity": 0}],
            location=self.warehouse,
            fail_fast=True,
        )

        self.assertEqual(result.success_count, 1)
        rec = StockRecord.objects.get(product=self.product_a, location=self.warehouse)
        self.assertEqual(rec.quantity, 0)

    def test_transfer_conserves_total_quantity(self):
        create_stock_record(product=self.product_a, location=self.warehouse, quantity=100)
        create_stock_record(product=self.product_b, location=self.warehouse, quantity=200)

        self.service.bulk_transfer(
            items=[
                {"product_id": self.product_a.pk, "quantity": 30},
                {"product_id": self.product_b.pk, "quantity": 50},
            ],
            from_location=self.warehouse,
            to_location=self.store,
            fail_fast=True,
        )

        total = sum(
            StockRecord.objects.all().values_list("quantity", flat=True)
        )
        self.assertEqual(total, 300)
