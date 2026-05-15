"""Warehouse scope tests for StockService."""

from django.core.exceptions import ValidationError
from django.test import TestCase

from inventory.exceptions import MovementWarehouseScopeError
from inventory.models import MovementType, StockLocation, StockMovement, StockRecord, Warehouse
from inventory.services.stock import (
    StockService,
    filter_stock_locations_by_warehouse_scope,
    filter_stock_movements_by_warehouse_scope,
    filter_stock_records_by_warehouse_scope,
    validate_movement_location_scope,
)

from ..factories import create_product, create_stock_record, create_tenant


class StockServiceWarehouseScopeTests(TestCase):
    """Tenant alignment and mixed retail vs facility movement rules."""

    @classmethod
    def setUpTestData(cls):
        cls.tenant = create_tenant()
        cls.product = create_product(tenant=cls.tenant, sku="SCOPE-001")
        cls.wh_a = Warehouse.objects.create(tenant=cls.tenant, name="DC A")
        cls.wh_b = Warehouse.objects.create(tenant=cls.tenant, name="DC B")
        cls.loc_a = StockLocation.add_root(
            name="Bin A",
            tenant=cls.tenant,
            warehouse=cls.wh_a,
        )
        cls.loc_b = StockLocation.add_root(
            name="Bin B",
            tenant=cls.tenant,
            warehouse=cls.wh_b,
        )
        cls.loc_retail = StockLocation.add_root(
            name="Shop floor",
            tenant=cls.tenant,
        )

    def setUp(self):
        self.service = StockService()

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

    @classmethod
    def setUpTestData(cls):
        cls.tenant = create_tenant()
        cls.product = create_product(tenant=cls.tenant, sku="Q-SCOPE-1")
        cls.wh = Warehouse.objects.create(tenant=cls.tenant, name="Main DC")
        cls.loc_dc = StockLocation.add_root(
            name="Dock",
            tenant=cls.tenant,
            warehouse=cls.wh,
        )
        cls.loc_shop = StockLocation.add_root(
            name="Till",
            tenant=cls.tenant,
        )
        create_stock_record(product=cls.product, location=cls.loc_dc, quantity=3)
        create_stock_record(product=cls.product, location=cls.loc_shop, quantity=7)

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
