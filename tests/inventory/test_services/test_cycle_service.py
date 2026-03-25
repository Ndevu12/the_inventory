"""Tests for :mod:`inventory.services.cycle` warehouse / location scope."""

from datetime import date

from django.test import TestCase

from inventory.models import CycleCountLine, InventoryCycle, StockLocation, Warehouse
from inventory.services.cycle import (
    CycleCountService,
    filter_cycle_count_lines_by_warehouse_scope,
    filter_inventory_cycles_by_warehouse_scope,
)

from tests.inventory.factories import (
    create_product,
    create_stock_record,
    create_tenant,
    create_user,
)


class CycleServiceWarehouseScopeTests(TestCase):
    """Snapshot and line operations respect ``(tenant, warehouse_id)`` partitions."""

    def setUp(self):
        self.tenant = create_tenant()
        self.user = create_user()
        self.service = CycleCountService()
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
        self.product = create_product(tenant=self.tenant, sku="CYC-001")

    def test_start_cycle_full_facility_only_includes_that_warehouse(self):
        create_stock_record(
            product=self.product, location=self.loc_a, quantity=10,
        )
        create_stock_record(
            product=self.product, location=self.loc_b, quantity=20,
        )
        cycle = self.service.start_cycle(
            name="DC A only",
            tenant=self.tenant,
            scheduled_date=date.today(),
            started_by=self.user,
            warehouse=self.wh_a,
        )
        lines = list(cycle.lines.values_list("location_id", flat=True))
        self.assertEqual(lines, [self.loc_a.pk])

    def test_start_cycle_retail_partition_excludes_facility_locations(self):
        create_stock_record(
            product=self.product, location=self.loc_a, quantity=5,
        )
        create_stock_record(
            product=self.product, location=self.loc_retail, quantity=7,
        )
        cycle = self.service.start_cycle(
            name="Retail wide",
            tenant=self.tenant,
            scheduled_date=date.today(),
            started_by=self.user,
            location=None,
            warehouse=None,
        )
        loc_ids = set(cycle.lines.values_list("location_id", flat=True))
        self.assertEqual(loc_ids, {self.loc_retail.pk})

    def test_start_cycle_single_location_ignores_other_facility_stock(self):
        create_stock_record(
            product=self.product, location=self.loc_a, quantity=3,
        )
        create_stock_record(
            product=self.product, location=self.loc_b, quantity=9,
        )
        cycle = self.service.start_cycle(
            name="Spot A",
            tenant=self.tenant,
            scheduled_date=date.today(),
            started_by=self.user,
            location=self.loc_a,
        )
        self.assertEqual(cycle.lines.count(), 1)

    def test_start_cycle_mismatched_warehouse_and_location_raises(self):
        with self.assertRaises(ValueError) as ctx:
            self.service.start_cycle(
                name="Bad",
                tenant=self.tenant,
                scheduled_date=date.today(),
                started_by=self.user,
                location=self.loc_a,
                warehouse=self.wh_b,
            )
        self.assertIn("warehouse", str(ctx.exception).lower())

    def test_start_cycle_sets_tenant_on_inventory_cycle(self):
        cycle = self.service.start_cycle(
            name="T",
            tenant=self.tenant,
            scheduled_date=date.today(),
            started_by=self.user,
            warehouse=self.wh_a,
        )
        self.assertEqual(cycle.tenant_id, self.tenant.pk)

    def test_record_count_rejects_location_from_other_scope(self):
        create_stock_record(
            product=self.product, location=self.loc_a, quantity=4,
        )
        create_stock_record(
            product=self.product, location=self.loc_b, quantity=4,
        )
        cycle = self.service.start_cycle(
            name="Multi-bin A",
            tenant=self.tenant,
            scheduled_date=date.today(),
            started_by=self.user,
            warehouse=self.wh_a,
        )
        self.assertEqual(cycle.lines.count(), 1)
        with self.assertRaises(ValueError) as ctx:
            self.service.record_count(
                cycle,
                product=self.product,
                location=self.loc_b,
                counted_quantity=4,
                counted_by=self.user,
            )
        self.assertIn("no count line", str(ctx.exception).lower())

    def test_record_count_rejects_peer_mixed_warehouse_scope(self):
        """Partition-wide cycles cannot count a line outside peer locations' scope."""
        create_stock_record(
            product=self.product, location=self.loc_a, quantity=2,
        )
        other_product = create_product(tenant=self.tenant, sku="CYC-002")
        create_stock_record(
            product=other_product, location=self.loc_a, quantity=3,
        )
        cycle = self.service.start_cycle(
            name="Multi SKU A",
            tenant=self.tenant,
            scheduled_date=date.today(),
            started_by=self.user,
            warehouse=self.wh_a,
        )
        self.assertEqual(cycle.lines.count(), 2)
        self.service.record_count(
            cycle,
            product=self.product,
            location=self.loc_a,
            counted_quantity=2,
            counted_by=self.user,
        )
        line_b = cycle.lines.get(product=other_product, location=self.loc_a)
        line_b.location = self.loc_b
        line_b.save(update_fields=["location"])
        with self.assertRaises(ValueError) as ctx:
            self.service.record_count(
                cycle,
                product=other_product,
                location=self.loc_b,
                counted_quantity=3,
                counted_by=self.user,
            )
        self.assertIn("scope", str(ctx.exception).lower())

    def test_foreign_tenant_location_on_start_raises(self):
        other = create_tenant()
        foreign = StockLocation.add_root(name="X", tenant=other)
        with self.assertRaises(ValueError):
            self.service.start_cycle(
                name="Bad tenant",
                tenant=self.tenant,
                scheduled_date=date.today(),
                started_by=self.user,
                location=foreign,
            )


class CycleWarehouseScopeFilterTests(TestCase):
    """Queryset helpers for cycle dashboards / reports."""

    def setUp(self):
        self.tenant = create_tenant()
        self.wh = Warehouse.objects.create(tenant=self.tenant, name="WH1")
        self.user = create_user()
        self.service = CycleCountService()
        self.loc = StockLocation.add_root(
            name="L1",
            tenant=self.tenant,
            warehouse=self.wh,
        )
        self.product = create_product(tenant=self.tenant)

    def test_filter_cycles_by_warehouse_matches_location_scoped_cycle(self):
        create_stock_record(product=self.product, location=self.loc, quantity=2)
        cycle = self.service.start_cycle(
            name="Spot",
            tenant=self.tenant,
            scheduled_date=date.today(),
            started_by=self.user,
            location=self.loc,
        )
        qs = filter_inventory_cycles_by_warehouse_scope(
            InventoryCycle.objects.all(),
            tenant_id=self.tenant.pk,
            warehouse_id=self.wh.pk,
        )
        self.assertEqual(list(qs), [cycle])

    def test_filter_cycle_lines_matches_partition(self):
        create_stock_record(product=self.product, location=self.loc, quantity=2)
        cycle = self.service.start_cycle(
            name="Full WH",
            tenant=self.tenant,
            scheduled_date=date.today(),
            started_by=self.user,
            warehouse=self.wh,
        )
        line = cycle.lines.first()
        qs = filter_cycle_count_lines_by_warehouse_scope(
            CycleCountLine.objects.all(),
            tenant_id=self.tenant.pk,
            warehouse_id=self.wh.pk,
        )
        self.assertEqual(list(qs), [line])

