"""Integration tests for StockService movement processing.

These tests exercise the full flow: create a movement via
:meth:`StockService.process_movement` and verify that StockRecords
are updated correctly, including edge cases like insufficient stock,
transaction atomicity, and multi-step movement sequences.

The lot-aware tests (process_movement_with_lots) verify FIFO/LIFO
allocation, manual lot selection, transfer lineage preservation,
and tracking_mode enforcement.
"""

from datetime import date, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from inventory.exceptions import (
    InsufficientStockError,
    LocationCapacityExceededError,
    LotTrackingRequiredError,
    MovementImmutableError,
    MovementWarehouseScopeError,
)
from inventory.models import (
    MovementType,
    StockLocation,
    StockLot,
    StockMovement,
    StockMovementLot,
    StockRecord,
    Warehouse,
)
from inventory.services.stock import (
    StockService,
    filter_stock_locations_by_warehouse_scope,
    filter_stock_movements_by_warehouse_scope,
    filter_stock_records_by_warehouse_scope,
    validate_movement_location_scope,
)

from ..factories import (
    create_location,
    create_product,
    create_stock_lot,
    create_stock_record,
    create_tenant,
)


class StockServiceSetupMixin:
    """Shared setUp for StockService tests."""

    def setUp(self):
        self.service = StockService()
        self.tenant = create_tenant()
        self.product = create_product(
            sku="SVC-001",
            unit_cost=Decimal("10.00"),
            tenant=self.tenant,
        )
        self.warehouse = create_location(name="Warehouse", tenant=self.tenant)
        self.store = create_location(name="Store", tenant=self.tenant)


# =====================================================================
# Receive
# =====================================================================


class StockServiceReceiveTests(StockServiceSetupMixin, TestCase):
    """Test RECEIVE movement processing."""

    def test_receive_creates_stock_record(self):
        movement = self.service.process_movement(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=100,
            to_location=self.warehouse,
        )
        self.assertEqual(movement.movement_type, MovementType.RECEIVE)
        record = StockRecord.objects.get(
            product=self.product, location=self.warehouse,
        )
        self.assertEqual(record.quantity, 100)

    def test_receive_increments_existing_record(self):
        create_stock_record(
            product=self.product, location=self.warehouse, quantity=50,
        )
        self.service.process_movement(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=30,
            to_location=self.warehouse,
        )
        record = StockRecord.objects.get(
            product=self.product, location=self.warehouse,
        )
        self.assertEqual(record.quantity, 80)

    def test_receive_returns_movement_instance(self):
        movement = self.service.process_movement(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=10,
            to_location=self.warehouse,
        )
        self.assertIsNotNone(movement.pk)
        self.assertEqual(movement.product, self.product)
        self.assertEqual(movement.quantity, 10)

    def test_receive_with_unit_cost(self):
        movement = self.service.process_movement(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=20,
            to_location=self.warehouse,
            unit_cost=Decimal("15.00"),
        )
        self.assertEqual(movement.unit_cost, Decimal("15.00"))

    def test_receive_with_reference_and_notes(self):
        movement = self.service.process_movement(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=10,
            to_location=self.warehouse,
            reference="PO-12345",
            notes="Received from supplier",
        )
        self.assertEqual(movement.reference, "PO-12345")
        self.assertEqual(movement.notes, "Received from supplier")


# =====================================================================
# Issue
# =====================================================================


class StockServiceIssueTests(StockServiceSetupMixin, TestCase):
    """Test ISSUE movement processing."""

    def test_issue_decrements_stock(self):
        create_stock_record(
            product=self.product, location=self.warehouse, quantity=100,
        )
        self.service.process_movement(
            product=self.product,
            movement_type=MovementType.ISSUE,
            quantity=30,
            from_location=self.warehouse,
        )
        record = StockRecord.objects.get(
            product=self.product, location=self.warehouse,
        )
        self.assertEqual(record.quantity, 70)

    def test_issue_to_zero(self):
        create_stock_record(
            product=self.product, location=self.warehouse, quantity=10,
        )
        self.service.process_movement(
            product=self.product,
            movement_type=MovementType.ISSUE,
            quantity=10,
            from_location=self.warehouse,
        )
        record = StockRecord.objects.get(
            product=self.product, location=self.warehouse,
        )
        self.assertEqual(record.quantity, 0)

    def test_issue_insufficient_stock_raises_error(self):
        create_stock_record(
            product=self.product, location=self.warehouse, quantity=5,
        )
        with self.assertRaises(InsufficientStockError) as ctx:
            self.service.process_movement(
                product=self.product,
                movement_type=MovementType.ISSUE,
                quantity=10,
                from_location=self.warehouse,
            )
        self.assertIn("Insufficient stock", str(ctx.exception))

    def test_issue_no_record_raises_error(self):
        with self.assertRaises(InsufficientStockError) as ctx:
            self.service.process_movement(
                product=self.product,
                movement_type=MovementType.ISSUE,
                quantity=5,
                from_location=self.warehouse,
            )
        self.assertIn("No stock record", str(ctx.exception))


# =====================================================================
# Transfer
# =====================================================================


class StockServiceTransferTests(StockServiceSetupMixin, TestCase):
    """Test TRANSFER movement processing."""

    def test_transfer_moves_stock(self):
        create_stock_record(
            product=self.product, location=self.warehouse, quantity=100,
        )
        self.service.process_movement(
            product=self.product,
            movement_type=MovementType.TRANSFER,
            quantity=40,
            from_location=self.warehouse,
            to_location=self.store,
        )
        source = StockRecord.objects.get(
            product=self.product, location=self.warehouse,
        )
        dest = StockRecord.objects.get(
            product=self.product, location=self.store,
        )
        self.assertEqual(source.quantity, 60)
        self.assertEqual(dest.quantity, 40)

    def test_transfer_creates_destination_record(self):
        """Destination record is created if it doesn't exist."""
        create_stock_record(
            product=self.product, location=self.warehouse, quantity=50,
        )
        self.service.process_movement(
            product=self.product,
            movement_type=MovementType.TRANSFER,
            quantity=20,
            from_location=self.warehouse,
            to_location=self.store,
        )
        self.assertTrue(
            StockRecord.objects.filter(
                product=self.product, location=self.store,
            ).exists()
        )

    def test_transfer_insufficient_stock_raises_error(self):
        create_stock_record(
            product=self.product, location=self.warehouse, quantity=5,
        )
        with self.assertRaises(InsufficientStockError):
            self.service.process_movement(
                product=self.product,
                movement_type=MovementType.TRANSFER,
                quantity=50,
                from_location=self.warehouse,
                to_location=self.store,
            )

    def test_transfer_conserves_total_quantity(self):
        """Total stock across locations stays the same after transfer."""
        create_stock_record(
            product=self.product, location=self.warehouse, quantity=100,
        )
        create_stock_record(
            product=self.product, location=self.store, quantity=20,
        )
        self.service.process_movement(
            product=self.product,
            movement_type=MovementType.TRANSFER,
            quantity=30,
            from_location=self.warehouse,
            to_location=self.store,
        )
        total = sum(
            StockRecord.objects.filter(product=self.product)
            .values_list("quantity", flat=True)
        )
        self.assertEqual(total, 120)


# =====================================================================
# Warehouse scope
# =====================================================================


class StockServiceWarehouseScopeTests(TestCase):
    """Tenant alignment and mixed retail vs facility movement rules."""

    def setUp(self):
        self.tenant = create_tenant()
        self.service = StockService()
        self.product = create_product(tenant=self.tenant, sku="SCOPE-001")
        self.wh_a = Warehouse.objects.create(tenant=self.tenant, name="DC A")
        self.wh_b = Warehouse.objects.create(tenant=self.tenant, name="DC B")
        self.loc_a = StockLocation.add_root(
            name="Bin A",
            tenant=self.tenant,
            warehouse=self.wh_a,
        )
        self.loc_b = StockLocation.add_root(
            name="Bin B",
            tenant=self.tenant,
            warehouse=self.wh_b,
        )
        self.loc_retail = StockLocation.add_root(
            name="Shop floor",
            tenant=self.tenant,
        )

    def test_cross_warehouse_transfer_succeeds(self):
        create_stock_record(product=self.product, location=self.loc_a, quantity=50)
        self.service.process_movement(
            product=self.product,
            movement_type=MovementType.TRANSFER,
            quantity=20,
            from_location=self.loc_a,
            to_location=self.loc_b,
        )
        self.assertEqual(
            StockRecord.objects.get(product=self.product, location=self.loc_a).quantity,
            30,
        )
        self.assertEqual(
            StockRecord.objects.get(product=self.product, location=self.loc_b).quantity,
            20,
        )

    def test_mixed_retail_and_facility_transfer_raises(self):
        create_stock_record(product=self.product, location=self.loc_a, quantity=10)
        with self.assertRaises(MovementWarehouseScopeError):
            self.service.process_movement(
                product=self.product,
                movement_type=MovementType.TRANSFER,
                quantity=5,
                from_location=self.loc_a,
                to_location=self.loc_retail,
            )

    def test_retail_to_retail_transfer_succeeds(self):
        """Two roots with ``warehouse=NULL`` stay in the retail partition."""
        loc_back = StockLocation.add_root(
            name="Stockroom",
            tenant=self.tenant,
        )
        loc_front = StockLocation.add_root(
            name="Shop floor front",
            tenant=self.tenant,
        )
        create_stock_record(product=self.product, location=loc_back, quantity=25)
        self.service.process_movement(
            product=self.product,
            movement_type=MovementType.TRANSFER,
            quantity=8,
            from_location=loc_back,
            to_location=loc_front,
        )
        self.assertEqual(
            StockRecord.objects.get(product=self.product, location=loc_back).quantity,
            17,
        )
        self.assertEqual(
            StockRecord.objects.get(product=self.product, location=loc_front).quantity,
            8,
        )

    def test_two_sided_adjustment_mixed_scope_raises(self):
        create_stock_record(product=self.product, location=self.loc_a, quantity=20)
        with self.assertRaises(MovementWarehouseScopeError):
            self.service.process_movement(
                product=self.product,
                movement_type=MovementType.ADJUSTMENT,
                quantity=5,
                from_location=self.loc_a,
                to_location=self.loc_retail,
            )

    def test_one_sided_adjustment_on_facility_location_ok(self):
        create_stock_record(product=self.product, location=self.loc_a, quantity=10)
        self.service.process_movement(
            product=self.product,
            movement_type=MovementType.ADJUSTMENT,
            quantity=3,
            from_location=self.loc_a,
        )
        self.assertEqual(
            StockRecord.objects.get(
                product=self.product, location=self.loc_a,
            ).quantity,
            7,
        )

    def test_receive_with_foreign_tenant_location_raises(self):
        other_tenant = create_tenant()
        foreign_loc = StockLocation.add_root(name="Elsewhere", tenant=other_tenant)
        with self.assertRaises(ValidationError) as ctx:
            self.service.process_movement(
                product=self.product,
                movement_type=MovementType.RECEIVE,
                quantity=5,
                to_location=foreign_loc,
            )
        self.assertIn("to_location", ctx.exception.message_dict)

    def test_validate_movement_location_scope_unknown_type_raises(self):
        with self.assertRaises(ValueError):
            validate_movement_location_scope(
                product=self.product,
                movement_type="not-a-type",
                to_location=self.loc_retail,
            )


class StockServiceWarehouseScopeQueryTests(TestCase):
    """Queryset helpers for (tenant, warehouse_id) partitions."""

    def setUp(self):
        self.tenant = create_tenant()
        self.product = create_product(tenant=self.tenant, sku="Q-SCOPE-1")
        self.wh = Warehouse.objects.create(tenant=self.tenant, name="Main DC")
        self.loc_dc = StockLocation.add_root(
            name="Dock",
            tenant=self.tenant,
            warehouse=self.wh,
        )
        self.loc_shop = StockLocation.add_root(
            name="Till",
            tenant=self.tenant,
        )
        create_stock_record(product=self.product, location=self.loc_dc, quantity=3)
        create_stock_record(product=self.product, location=self.loc_shop, quantity=7)

    def test_filter_locations_by_scope(self):
        qs = StockLocation.objects.all()
        dc_roots = filter_stock_locations_by_warehouse_scope(
            qs, tenant_id=self.tenant.pk, warehouse_id=self.wh.pk,
        )
        self.assertCountEqual(list(dc_roots), [self.loc_dc])

    def test_filter_records_by_scope(self):
        qs = StockRecord.objects.filter(product=self.product)
        dc_records = filter_stock_records_by_warehouse_scope(
            qs, tenant_id=self.tenant.pk, warehouse_id=self.wh.pk,
        )
        self.assertEqual(dc_records.count(), 1)
        self.assertEqual(dc_records.first().location_id, self.loc_dc.pk)

    def test_filter_movements_by_facility_scope(self):
        service = StockService()
        service.process_movement(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=2,
            to_location=self.loc_dc,
        )
        mv = StockMovement.objects.get(product=self.product)
        scoped = filter_stock_movements_by_warehouse_scope(
            StockMovement.objects.all(),
            tenant_id=self.tenant.pk,
            warehouse_id=self.wh.pk,
        )
        self.assertIn(mv.pk, list(scoped.values_list("pk", flat=True)))

    def test_filter_movements_retail_scope_matches_null_warehouse_leg(self):
        service = StockService()
        service.process_movement(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=1,
            to_location=self.loc_shop,
        )
        mv = StockMovement.objects.filter(to_location=self.loc_shop).get()
        scoped = filter_stock_movements_by_warehouse_scope(
            StockMovement.objects.all(),
            tenant_id=self.tenant.pk,
            warehouse_id=None,
        )
        self.assertIn(mv.pk, list(scoped.values_list("pk", flat=True)))


# =====================================================================
# Adjustment
# =====================================================================


class StockServiceAdjustmentTests(StockServiceSetupMixin, TestCase):
    """Test ADJUSTMENT movement processing."""

    def test_positive_adjustment_increments(self):
        self.service.process_movement(
            product=self.product,
            movement_type=MovementType.ADJUSTMENT,
            quantity=25,
            to_location=self.warehouse,
        )
        record = StockRecord.objects.get(
            product=self.product, location=self.warehouse,
        )
        self.assertEqual(record.quantity, 25)

    def test_negative_adjustment_decrements(self):
        create_stock_record(
            product=self.product, location=self.warehouse, quantity=50,
        )
        self.service.process_movement(
            product=self.product,
            movement_type=MovementType.ADJUSTMENT,
            quantity=15,
            from_location=self.warehouse,
        )
        record = StockRecord.objects.get(
            product=self.product, location=self.warehouse,
        )
        self.assertEqual(record.quantity, 35)

    def test_adjustment_both_locations(self):
        create_stock_record(
            product=self.product, location=self.warehouse, quantity=100,
        )
        self.service.process_movement(
            product=self.product,
            movement_type=MovementType.ADJUSTMENT,
            quantity=10,
            from_location=self.warehouse,
            to_location=self.store,
        )
        source = StockRecord.objects.get(
            product=self.product, location=self.warehouse,
        )
        dest = StockRecord.objects.get(
            product=self.product, location=self.store,
        )
        self.assertEqual(source.quantity, 90)
        self.assertEqual(dest.quantity, 10)

    def test_negative_adjustment_insufficient_stock_raises_error(self):
        create_stock_record(
            product=self.product, location=self.warehouse, quantity=3,
        )
        with self.assertRaises(InsufficientStockError):
            self.service.process_movement(
                product=self.product,
                movement_type=MovementType.ADJUSTMENT,
                quantity=10,
                from_location=self.warehouse,
            )


# =====================================================================
# Capacity Enforcement
# =====================================================================


class StockServiceCapacityTests(TestCase):
    """Test that StockService prevents exceeding location capacity."""

    def setUp(self):
        self.service = StockService()
        self.tenant = create_tenant()
        self.product = create_product(sku="CAP-SVC-001", tenant=self.tenant)
        self.limited = create_location(
            name="Limited Bin", max_capacity=100, tenant=self.tenant,
        )
        self.unlimited = create_location(
            name="Unlimited Warehouse", tenant=self.tenant,
        )

    # -- RECEIVE --

    def test_receive_within_capacity_succeeds(self):
        self.service.process_movement(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=80,
            to_location=self.limited,
        )
        record = StockRecord.objects.get(
            product=self.product, location=self.limited,
        )
        self.assertEqual(record.quantity, 80)

    def test_receive_at_exact_capacity_succeeds(self):
        self.service.process_movement(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=100,
            to_location=self.limited,
        )
        record = StockRecord.objects.get(
            product=self.product, location=self.limited,
        )
        self.assertEqual(record.quantity, 100)

    def test_receive_exceeding_capacity_raises_error(self):
        self.service.process_movement(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=80,
            to_location=self.limited,
        )
        with self.assertRaises(LocationCapacityExceededError) as ctx:
            self.service.process_movement(
                product=self.product,
                movement_type=MovementType.RECEIVE,
                quantity=30,
                to_location=self.limited,
            )
        self.assertIn("cannot accept", str(ctx.exception))

    def test_receive_unlimited_location_always_succeeds(self):
        self.service.process_movement(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=999999,
            to_location=self.unlimited,
        )
        record = StockRecord.objects.get(
            product=self.product, location=self.unlimited,
        )
        self.assertEqual(record.quantity, 999999)

    def test_receive_capacity_check_is_atomic(self):
        """Failed receive should not partially update stock."""
        self.service.process_movement(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=90,
            to_location=self.limited,
        )
        with self.assertRaises(LocationCapacityExceededError):
            self.service.process_movement(
                product=self.product,
                movement_type=MovementType.RECEIVE,
                quantity=20,
                to_location=self.limited,
            )
        record = StockRecord.objects.get(
            product=self.product, location=self.limited,
        )
        self.assertEqual(record.quantity, 90)

    # -- TRANSFER --

    def test_transfer_within_dest_capacity_succeeds(self):
        create_stock_record(
            product=self.product, location=self.unlimited, quantity=200,
        )
        self.service.process_movement(
            product=self.product,
            movement_type=MovementType.TRANSFER,
            quantity=50,
            from_location=self.unlimited,
            to_location=self.limited,
        )
        dest = StockRecord.objects.get(
            product=self.product, location=self.limited,
        )
        self.assertEqual(dest.quantity, 50)

    def test_transfer_exceeding_dest_capacity_raises_error(self):
        create_stock_record(
            product=self.product, location=self.unlimited, quantity=200,
        )
        with self.assertRaises(LocationCapacityExceededError):
            self.service.process_movement(
                product=self.product,
                movement_type=MovementType.TRANSFER,
                quantity=150,
                from_location=self.unlimited,
                to_location=self.limited,
            )

    def test_transfer_capacity_failure_preserves_source(self):
        """Source stock must not change when destination rejects."""
        create_stock_record(
            product=self.product, location=self.unlimited, quantity=200,
        )
        with self.assertRaises(LocationCapacityExceededError):
            self.service.process_movement(
                product=self.product,
                movement_type=MovementType.TRANSFER,
                quantity=150,
                from_location=self.unlimited,
                to_location=self.limited,
            )
        source = StockRecord.objects.get(
            product=self.product, location=self.unlimited,
        )
        self.assertEqual(source.quantity, 200)

    # -- ADJUSTMENT --

    def test_positive_adjustment_within_capacity_succeeds(self):
        self.service.process_movement(
            product=self.product,
            movement_type=MovementType.ADJUSTMENT,
            quantity=100,
            to_location=self.limited,
        )
        record = StockRecord.objects.get(
            product=self.product, location=self.limited,
        )
        self.assertEqual(record.quantity, 100)

    def test_positive_adjustment_exceeding_capacity_raises_error(self):
        self.service.process_movement(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=80,
            to_location=self.limited,
        )
        with self.assertRaises(LocationCapacityExceededError):
            self.service.process_movement(
                product=self.product,
                movement_type=MovementType.ADJUSTMENT,
                quantity=30,
                to_location=self.limited,
            )

    # -- Multiple products share capacity --

    def test_capacity_accounts_for_all_products(self):
        """Location capacity is shared across all products stored there."""
        p2 = create_product(sku="CAP-SVC-002", tenant=self.tenant)
        self.service.process_movement(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=60,
            to_location=self.limited,
        )
        self.service.process_movement(
            product=p2,
            movement_type=MovementType.RECEIVE,
            quantity=30,
            to_location=self.limited,
        )
        with self.assertRaises(LocationCapacityExceededError):
            self.service.process_movement(
                product=p2,
                movement_type=MovementType.RECEIVE,
                quantity=20,
                to_location=self.limited,
            )

    # -- Null capacity (backward compat) --

    def test_null_capacity_allows_unlimited_stock(self):
        """Existing locations with null max_capacity remain unlimited."""
        self.assertIsNone(self.unlimited.max_capacity)
        for _ in range(5):
            self.service.process_movement(
                product=self.product,
                movement_type=MovementType.RECEIVE,
                quantity=10000,
                to_location=self.unlimited,
            )
        record = StockRecord.objects.get(
            product=self.product, location=self.unlimited,
        )
        self.assertEqual(record.quantity, 50000)


# =====================================================================
# Immutability
# =====================================================================


class StockServiceImmutabilityTests(StockServiceSetupMixin, TestCase):
    """Test that processed movements cannot be modified."""

    def test_cannot_update_processed_movement(self):
        movement = self.service.process_movement(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=10,
            to_location=self.warehouse,
        )
        movement.quantity = 999
        with self.assertRaises(MovementImmutableError) as ctx:
            movement.save()
        self.assertIn("immutable", str(ctx.exception))


# =====================================================================
# Transaction Integrity
# =====================================================================


class StockServiceTransactionTests(StockServiceSetupMixin, TestCase):
    """Test that failed movements don't leave partial state."""

    def test_failed_issue_does_not_create_movement(self):
        """If processing fails, neither movement nor record changes persist."""
        initial_count = self.product.stock_movements.count()
        with self.assertRaises(InsufficientStockError):
            self.service.process_movement(
                product=self.product,
                movement_type=MovementType.ISSUE,
                quantity=999,
                from_location=self.warehouse,
            )
        self.assertEqual(self.product.stock_movements.count(), initial_count)

    def test_failed_transfer_preserves_source_quantity(self):
        create_stock_record(
            product=self.product, location=self.warehouse, quantity=10,
        )
        with self.assertRaises(InsufficientStockError):
            self.service.process_movement(
                product=self.product,
                movement_type=MovementType.TRANSFER,
                quantity=50,
                from_location=self.warehouse,
                to_location=self.store,
            )
        record = StockRecord.objects.get(
            product=self.product, location=self.warehouse,
        )
        self.assertEqual(record.quantity, 10)


# =====================================================================
# Multi-step Sequences
# =====================================================================


class StockServiceSequentialTests(StockServiceSetupMixin, TestCase):
    """Test sequential movements across multiple operations."""

    def test_receive_then_issue_then_transfer(self):
        """Receive → Issue → Transfer sequence produces correct state."""
        # Receive 100 at warehouse
        self.service.process_movement(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=100,
            to_location=self.warehouse,
        )
        # Issue 20 from warehouse
        self.service.process_movement(
            product=self.product,
            movement_type=MovementType.ISSUE,
            quantity=20,
            from_location=self.warehouse,
        )
        # Transfer 30 warehouse → store
        self.service.process_movement(
            product=self.product,
            movement_type=MovementType.TRANSFER,
            quantity=30,
            from_location=self.warehouse,
            to_location=self.store,
        )

        warehouse_record = StockRecord.objects.get(
            product=self.product, location=self.warehouse,
        )
        store_record = StockRecord.objects.get(
            product=self.product, location=self.store,
        )
        self.assertEqual(warehouse_record.quantity, 50)  # 100 - 20 - 30
        self.assertEqual(store_record.quantity, 30)

    def test_multiple_receives_accumulate(self):
        for i in range(5):
            self.service.process_movement(
                product=self.product,
                movement_type=MovementType.RECEIVE,
                quantity=10,
                to_location=self.warehouse,
            )
        record = StockRecord.objects.get(
            product=self.product, location=self.warehouse,
        )
        self.assertEqual(record.quantity, 50)

    def test_movement_count_after_sequence(self):
        """Each process_movement call creates exactly one StockMovement."""
        for qty in [100, 20, 30]:
            self.service.process_movement(
                product=self.product,
                movement_type=MovementType.RECEIVE,
                quantity=qty,
                to_location=self.warehouse,
            )
        self.assertEqual(self.product.stock_movements.count(), 3)


# =====================================================================
# Lot-Aware: Shared setup
# =====================================================================


class LotServiceSetupMixin:
    """Shared setUp for lot-aware StockService tests.

    Creates a product with tracking_mode="optional" to enable lot logic.
    """

    def setUp(self):
        self.service = StockService()
        self.tenant = create_tenant()
        self.product = create_product(
            sku="LOT-001",
            unit_cost=Decimal("10.00"),
            tracking_mode="optional",
            tenant=self.tenant,
        )
        self.warehouse = create_location(name="Lot Warehouse", tenant=self.tenant)
        self.store = create_location(name="Lot Store", tenant=self.tenant)


# =====================================================================
# Lot-Aware: RECEIVE
# =====================================================================


class LotReceiveTests(LotServiceSetupMixin, TestCase):
    """Test RECEIVE via process_movement_with_lots."""

    def test_receive_creates_lot_and_link(self):
        movement = self.service.process_movement_with_lots(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=100,
            to_location=self.warehouse,
            lot_number="BATCH-001",
        )
        lot = StockLot.objects.get(
            product=self.product, lot_number="BATCH-001",
        )
        self.assertEqual(lot.quantity_received, 100)
        self.assertEqual(lot.quantity_remaining, 100)
        self.assertEqual(lot.received_date, date.today())

        sml = StockMovementLot.objects.get(stock_movement=movement)
        self.assertEqual(sml.stock_lot, lot)
        self.assertEqual(sml.quantity, 100)

    def test_receive_increments_existing_lot(self):
        self.service.process_movement_with_lots(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=100,
            to_location=self.warehouse,
            lot_number="BATCH-001",
        )
        self.service.process_movement_with_lots(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=50,
            to_location=self.warehouse,
            lot_number="BATCH-001",
        )
        lot = StockLot.objects.get(
            product=self.product, lot_number="BATCH-001",
        )
        self.assertEqual(lot.quantity_received, 150)
        self.assertEqual(lot.quantity_remaining, 150)
        self.assertEqual(StockMovementLot.objects.count(), 2)

    def test_receive_stores_serial_and_dates(self):
        mfg = date(2026, 1, 1)
        exp = date(2027, 1, 1)
        self.service.process_movement_with_lots(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=10,
            to_location=self.warehouse,
            lot_number="SN-LOT",
            serial_number="SN-12345",
            manufacturing_date=mfg,
            expiry_date=exp,
        )
        lot = StockLot.objects.get(lot_number="SN-LOT")
        self.assertEqual(lot.serial_number, "SN-12345")
        self.assertEqual(lot.manufacturing_date, mfg)
        self.assertEqual(lot.expiry_date, exp)

    def test_receive_without_lot_number_skips_lot_creation(self):
        movement = self.service.process_movement_with_lots(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=50,
            to_location=self.warehouse,
        )
        self.assertIsNotNone(movement.pk)
        self.assertEqual(StockLot.objects.count(), 0)
        self.assertEqual(StockMovementLot.objects.count(), 0)
        record = StockRecord.objects.get(
            product=self.product, location=self.warehouse,
        )
        self.assertEqual(record.quantity, 50)

    def test_receive_updates_stock_record(self):
        self.service.process_movement_with_lots(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=75,
            to_location=self.warehouse,
            lot_number="BATCH-X",
        )
        record = StockRecord.objects.get(
            product=self.product, location=self.warehouse,
        )
        self.assertEqual(record.quantity, 75)


# =====================================================================
# Lot-Aware: ISSUE — FIFO
# =====================================================================


class LotIssueFIFOTests(LotServiceSetupMixin, TestCase):
    """Test ISSUE with FIFO allocation."""

    def _receive_lots(self):
        """Create three lots with staggered received_dates."""
        today = date.today()
        create_stock_record(
            product=self.product, location=self.warehouse, quantity=250,
        )
        self.lot_old = create_stock_lot(
            product=self.product,
            lot_number="OLD",
            quantity_received=100,
            quantity_remaining=100,
            received_date=today - timedelta(days=30),
        )
        self.lot_mid = create_stock_lot(
            product=self.product,
            lot_number="MID",
            quantity_received=100,
            quantity_remaining=100,
            received_date=today - timedelta(days=15),
        )
        self.lot_new = create_stock_lot(
            product=self.product,
            lot_number="NEW",
            quantity_received=50,
            quantity_remaining=50,
            received_date=today,
        )

    def test_fifo_allocates_from_oldest_first(self):
        self._receive_lots()
        movement = self.service.process_movement_with_lots(
            product=self.product,
            movement_type=MovementType.ISSUE,
            quantity=80,
            from_location=self.warehouse,
            allocation_strategy="FIFO",
        )
        self.lot_old.refresh_from_db()
        self.assertEqual(self.lot_old.quantity_remaining, 20)

        allocs = StockMovementLot.objects.filter(stock_movement=movement)
        self.assertEqual(allocs.count(), 1)
        self.assertEqual(allocs.first().stock_lot, self.lot_old)
        self.assertEqual(allocs.first().quantity, 80)

    def test_fifo_spans_multiple_lots(self):
        self._receive_lots()
        movement = self.service.process_movement_with_lots(
            product=self.product,
            movement_type=MovementType.ISSUE,
            quantity=150,
            from_location=self.warehouse,
            allocation_strategy="FIFO",
        )
        self.lot_old.refresh_from_db()
        self.lot_mid.refresh_from_db()
        self.assertEqual(self.lot_old.quantity_remaining, 0)
        self.assertEqual(self.lot_mid.quantity_remaining, 50)

        allocs = list(
            StockMovementLot.objects
            .filter(stock_movement=movement)
            .order_by("stock_lot__received_date")
        )
        self.assertEqual(len(allocs), 2)
        self.assertEqual(allocs[0].stock_lot, self.lot_old)
        self.assertEqual(allocs[0].quantity, 100)
        self.assertEqual(allocs[1].stock_lot, self.lot_mid)
        self.assertEqual(allocs[1].quantity, 50)

    def test_fifo_insufficient_lot_quantity_raises_error(self):
        create_stock_record(
            product=self.product, location=self.warehouse, quantity=999,
        )
        create_stock_lot(
            product=self.product,
            lot_number="SMALL",
            quantity_received=10,
            quantity_remaining=10,
        )
        with self.assertRaises(InsufficientStockError) as ctx:
            self.service.process_movement_with_lots(
                product=self.product,
                movement_type=MovementType.ISSUE,
                quantity=50,
                from_location=self.warehouse,
            )
        self.assertIn("lot quantity", str(ctx.exception))

    def test_fifo_decrements_stock_record(self):
        self._receive_lots()
        self.service.process_movement_with_lots(
            product=self.product,
            movement_type=MovementType.ISSUE,
            quantity=60,
            from_location=self.warehouse,
        )
        record = StockRecord.objects.get(
            product=self.product, location=self.warehouse,
        )
        self.assertEqual(record.quantity, 190)


# =====================================================================
# Lot-Aware: ISSUE — LIFO
# =====================================================================


class LotIssueLIFOTests(LotServiceSetupMixin, TestCase):
    """Test ISSUE with LIFO allocation."""

    def test_lifo_allocates_from_newest_first(self):
        today = date.today()
        create_stock_record(
            product=self.product, location=self.warehouse, quantity=200,
        )
        lot_old = create_stock_lot(
            product=self.product,
            lot_number="OLD",
            quantity_received=100,
            quantity_remaining=100,
            received_date=today - timedelta(days=30),
        )
        lot_new = create_stock_lot(
            product=self.product,
            lot_number="NEW",
            quantity_received=100,
            quantity_remaining=100,
            received_date=today,
        )
        movement = self.service.process_movement_with_lots(
            product=self.product,
            movement_type=MovementType.ISSUE,
            quantity=80,
            from_location=self.warehouse,
            allocation_strategy="LIFO",
        )
        lot_new.refresh_from_db()
        lot_old.refresh_from_db()
        self.assertEqual(lot_new.quantity_remaining, 20)
        self.assertEqual(lot_old.quantity_remaining, 100)

        alloc = StockMovementLot.objects.get(stock_movement=movement)
        self.assertEqual(alloc.stock_lot, lot_new)


# =====================================================================
# Lot-Aware: ISSUE — MANUAL
# =====================================================================


class LotIssueManualTests(LotServiceSetupMixin, TestCase):
    """Test ISSUE with MANUAL allocation strategy."""

    def test_manual_allocation(self):
        create_stock_record(
            product=self.product, location=self.warehouse, quantity=200,
        )
        lot_a = create_stock_lot(
            product=self.product, lot_number="A",
            quantity_received=100, quantity_remaining=100,
        )
        lot_b = create_stock_lot(
            product=self.product, lot_number="B",
            quantity_received=100, quantity_remaining=100,
        )
        movement = self.service.process_movement_with_lots(
            product=self.product,
            movement_type=MovementType.ISSUE,
            quantity=70,
            from_location=self.warehouse,
            allocation_strategy="MANUAL",
            manual_lot_allocations=[
                {"lot_id": lot_a.pk, "quantity": 30},
                {"lot_id": lot_b.pk, "quantity": 40},
            ],
        )
        lot_a.refresh_from_db()
        lot_b.refresh_from_db()
        self.assertEqual(lot_a.quantity_remaining, 70)
        self.assertEqual(lot_b.quantity_remaining, 60)

        allocs = StockMovementLot.objects.filter(stock_movement=movement)
        self.assertEqual(allocs.count(), 2)

    def test_manual_total_mismatch_raises_error(self):
        create_stock_record(
            product=self.product, location=self.warehouse, quantity=200,
        )
        lot = create_stock_lot(
            product=self.product, lot_number="A",
            quantity_received=100, quantity_remaining=100,
        )
        with self.assertRaises(ValueError) as ctx:
            self.service.process_movement_with_lots(
                product=self.product,
                movement_type=MovementType.ISSUE,
                quantity=50,
                from_location=self.warehouse,
                allocation_strategy="MANUAL",
                manual_lot_allocations=[
                    {"lot_id": lot.pk, "quantity": 30},
                ],
            )
        self.assertIn("does not match", str(ctx.exception))

    def test_manual_insufficient_lot_raises_error(self):
        create_stock_record(
            product=self.product, location=self.warehouse, quantity=200,
        )
        lot = create_stock_lot(
            product=self.product, lot_number="A",
            quantity_received=10, quantity_remaining=10,
        )
        with self.assertRaises(InsufficientStockError):
            self.service.process_movement_with_lots(
                product=self.product,
                movement_type=MovementType.ISSUE,
                quantity=50,
                from_location=self.warehouse,
                allocation_strategy="MANUAL",
                manual_lot_allocations=[
                    {"lot_id": lot.pk, "quantity": 50},
                ],
            )

    def test_manual_requires_allocations(self):
        create_stock_record(
            product=self.product, location=self.warehouse, quantity=100,
        )
        create_stock_lot(
            product=self.product, lot_number="A",
            quantity_received=100, quantity_remaining=100,
        )
        with self.assertRaises(ValueError):
            self.service.process_movement_with_lots(
                product=self.product,
                movement_type=MovementType.ISSUE,
                quantity=10,
                from_location=self.warehouse,
                allocation_strategy="MANUAL",
            )


# =====================================================================
# Lot-Aware: TRANSFER
# =====================================================================


class LotTransferTests(LotServiceSetupMixin, TestCase):
    """Test TRANSFER preserves lot identity (no quantity_remaining change)."""

    def test_transfer_preserves_lot_quantity_remaining(self):
        create_stock_record(
            product=self.product, location=self.warehouse, quantity=100,
        )
        lot = create_stock_lot(
            product=self.product, lot_number="T-LOT",
            quantity_received=100, quantity_remaining=100,
        )
        self.service.process_movement_with_lots(
            product=self.product,
            movement_type=MovementType.TRANSFER,
            quantity=40,
            from_location=self.warehouse,
            to_location=self.store,
        )
        lot.refresh_from_db()
        self.assertEqual(lot.quantity_remaining, 100)

    def test_transfer_creates_movement_lot_entries(self):
        create_stock_record(
            product=self.product, location=self.warehouse, quantity=100,
        )
        lot = create_stock_lot(
            product=self.product, lot_number="T-LOT",
            quantity_received=100, quantity_remaining=100,
        )
        movement = self.service.process_movement_with_lots(
            product=self.product,
            movement_type=MovementType.TRANSFER,
            quantity=40,
            from_location=self.warehouse,
            to_location=self.store,
        )
        sml = StockMovementLot.objects.get(stock_movement=movement)
        self.assertEqual(sml.stock_lot, lot)
        self.assertEqual(sml.quantity, 40)

    def test_transfer_updates_stock_records(self):
        create_stock_record(
            product=self.product, location=self.warehouse, quantity=100,
        )
        create_stock_lot(
            product=self.product, lot_number="T-LOT",
            quantity_received=100, quantity_remaining=100,
        )
        self.service.process_movement_with_lots(
            product=self.product,
            movement_type=MovementType.TRANSFER,
            quantity=30,
            from_location=self.warehouse,
            to_location=self.store,
        )
        src = StockRecord.objects.get(
            product=self.product, location=self.warehouse,
        )
        dst = StockRecord.objects.get(
            product=self.product, location=self.store,
        )
        self.assertEqual(src.quantity, 70)
        self.assertEqual(dst.quantity, 30)


# =====================================================================
# Lot-Aware: ADJUSTMENT
# =====================================================================


class LotAdjustmentTests(LotServiceSetupMixin, TestCase):
    """Test ADJUSTMENT with lot operations."""

    def test_negative_adjustment_targets_specific_lot(self):
        create_stock_record(
            product=self.product, location=self.warehouse, quantity=100,
        )
        lot = create_stock_lot(
            product=self.product, lot_number="ADJ-LOT",
            quantity_received=100, quantity_remaining=100,
        )
        self.service.process_movement_with_lots(
            product=self.product,
            movement_type=MovementType.ADJUSTMENT,
            quantity=25,
            from_location=self.warehouse,
            lot_number="ADJ-LOT",
        )
        lot.refresh_from_db()
        self.assertEqual(lot.quantity_remaining, 75)

    def test_negative_adjustment_fifo_when_no_lot_number(self):
        today = date.today()
        create_stock_record(
            product=self.product, location=self.warehouse, quantity=200,
        )
        lot_old = create_stock_lot(
            product=self.product, lot_number="OLD",
            quantity_received=100, quantity_remaining=100,
            received_date=today - timedelta(days=10),
        )
        lot_new = create_stock_lot(
            product=self.product, lot_number="NEW",
            quantity_received=100, quantity_remaining=100,
            received_date=today,
        )
        self.service.process_movement_with_lots(
            product=self.product,
            movement_type=MovementType.ADJUSTMENT,
            quantity=50,
            from_location=self.warehouse,
        )
        lot_old.refresh_from_db()
        lot_new.refresh_from_db()
        self.assertEqual(lot_old.quantity_remaining, 50)
        self.assertEqual(lot_new.quantity_remaining, 100)

    def test_positive_adjustment_creates_lot(self):
        self.service.process_movement_with_lots(
            product=self.product,
            movement_type=MovementType.ADJUSTMENT,
            quantity=50,
            to_location=self.warehouse,
            lot_number="ADJ-NEW",
        )
        lot = StockLot.objects.get(lot_number="ADJ-NEW")
        self.assertEqual(lot.quantity_received, 50)
        self.assertEqual(lot.quantity_remaining, 50)

    def test_adjustment_insufficient_specific_lot_raises_error(self):
        create_stock_record(
            product=self.product, location=self.warehouse, quantity=100,
        )
        create_stock_lot(
            product=self.product, lot_number="SMALL",
            quantity_received=10, quantity_remaining=10,
        )
        with self.assertRaises(InsufficientStockError):
            self.service.process_movement_with_lots(
                product=self.product,
                movement_type=MovementType.ADJUSTMENT,
                quantity=50,
                from_location=self.warehouse,
                lot_number="SMALL",
            )


# =====================================================================
# Tracking Mode Validation
# =====================================================================


class TrackingModeTests(TestCase):
    """Test tracking_mode enforcement."""

    def setUp(self):
        self.service = StockService()
        self.tenant = create_tenant()
        self.warehouse = create_location(name="TM Warehouse", tenant=self.tenant)

    def test_tracking_none_ignores_lot_info(self):
        product = create_product(
            sku="TM-NONE", tracking_mode="none", tenant=self.tenant,
        )
        movement = self.service.process_movement_with_lots(
            product=product,
            movement_type=MovementType.RECEIVE,
            quantity=100,
            to_location=self.warehouse,
            lot_number="IGNORED",
        )
        self.assertIsNotNone(movement.pk)
        self.assertEqual(StockLot.objects.count(), 0)
        self.assertEqual(StockMovementLot.objects.count(), 0)

    def test_tracking_required_without_lot_raises_error(self):
        product = create_product(
            sku="TM-REQ", tracking_mode="required", tenant=self.tenant,
        )
        with self.assertRaises(LotTrackingRequiredError) as ctx:
            self.service.process_movement_with_lots(
                product=product,
                movement_type=MovementType.RECEIVE,
                quantity=100,
                to_location=self.warehouse,
            )
        self.assertIn("requires lot tracking", str(ctx.exception))

    def test_tracking_required_with_lot_succeeds(self):
        product = create_product(
            sku="TM-REQ-OK", tracking_mode="required", tenant=self.tenant,
        )
        movement = self.service.process_movement_with_lots(
            product=product,
            movement_type=MovementType.RECEIVE,
            quantity=100,
            to_location=self.warehouse,
            lot_number="REQ-LOT",
        )
        self.assertIsNotNone(movement.pk)
        self.assertTrue(
            StockLot.objects.filter(lot_number="REQ-LOT").exists(),
        )

    def test_tracking_optional_creates_lot_when_provided(self):
        product = create_product(
            sku="TM-OPT", tracking_mode="optional", tenant=self.tenant,
        )
        movement = self.service.process_movement_with_lots(
            product=product,
            movement_type=MovementType.RECEIVE,
            quantity=50,
            to_location=self.warehouse,
            lot_number="OPT-LOT",
        )
        self.assertIsNotNone(movement.pk)
        self.assertTrue(
            StockLot.objects.filter(lot_number="OPT-LOT").exists(),
        )

    def test_tracking_optional_skips_lot_when_not_provided(self):
        product = create_product(
            sku="TM-OPT-SKIP", tracking_mode="optional", tenant=self.tenant,
        )
        movement = self.service.process_movement_with_lots(
            product=product,
            movement_type=MovementType.RECEIVE,
            quantity=50,
            to_location=self.warehouse,
        )
        self.assertIsNotNone(movement.pk)
        self.assertEqual(StockLot.objects.count(), 0)


# =====================================================================
# Backward Compatibility
# =====================================================================


class BackwardCompatibilityTests(StockServiceSetupMixin, TestCase):
    """Ensure process_movement() is unchanged alongside the new method."""

    def test_process_movement_still_works(self):
        self.service.process_movement(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=100,
            to_location=self.warehouse,
        )
        record = StockRecord.objects.get(
            product=self.product, location=self.warehouse,
        )
        self.assertEqual(record.quantity, 100)
        self.assertEqual(StockLot.objects.count(), 0)
        self.assertEqual(StockMovementLot.objects.count(), 0)

    def test_process_movement_creates_no_lot_entries(self):
        self.service.process_movement(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=50,
            to_location=self.warehouse,
        )
        self.assertEqual(StockMovementLot.objects.count(), 0)


# =====================================================================
# Lot-Aware: End-to-End Sequences
# =====================================================================


class LotSequenceTests(LotServiceSetupMixin, TestCase):
    """Test multi-step lot-aware movement sequences."""

    def test_receive_then_fifo_issue(self):
        """Receive into lots, then FIFO issue draws from oldest."""
        self.service.process_movement_with_lots(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=100,
            to_location=self.warehouse,
            lot_number="FIRST",
        )
        first_lot = StockLot.objects.get(lot_number="FIRST")
        first_lot.received_date = date.today() - timedelta(days=10)
        first_lot.save(update_fields=["received_date"])

        self.service.process_movement_with_lots(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=100,
            to_location=self.warehouse,
            lot_number="SECOND",
        )

        self.service.process_movement_with_lots(
            product=self.product,
            movement_type=MovementType.ISSUE,
            quantity=120,
            from_location=self.warehouse,
            allocation_strategy="FIFO",
        )

        first_lot.refresh_from_db()
        second_lot = StockLot.objects.get(lot_number="SECOND")
        self.assertEqual(first_lot.quantity_remaining, 0)
        self.assertEqual(second_lot.quantity_remaining, 80)

        record = StockRecord.objects.get(
            product=self.product, location=self.warehouse,
        )
        self.assertEqual(record.quantity, 80)

    def test_receive_transfer_then_issue_preserves_lots(self):
        """Transfer doesn't consume lots; subsequent issue still can."""
        self.service.process_movement_with_lots(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=100,
            to_location=self.warehouse,
            lot_number="LOT-A",
        )
        lot = StockLot.objects.get(lot_number="LOT-A")

        self.service.process_movement_with_lots(
            product=self.product,
            movement_type=MovementType.TRANSFER,
            quantity=40,
            from_location=self.warehouse,
            to_location=self.store,
        )
        lot.refresh_from_db()
        self.assertEqual(lot.quantity_remaining, 100)

        self.service.process_movement_with_lots(
            product=self.product,
            movement_type=MovementType.ISSUE,
            quantity=30,
            from_location=self.store,
        )
        lot.refresh_from_db()
        self.assertEqual(lot.quantity_remaining, 70)
