"""Factories for DC-linked vs retail-only (``warehouse=NULL``) location trees."""

from django.test import TestCase

from tests.fixtures.factories import (
    create_child_location,
    create_location,
    create_tenant,
    create_warehouse,
)
from tests.inventory import factories as inventory_factories


class WarehouseFixturesFactoriesTest(TestCase):
    """``tests/fixtures/factories`` helpers for Warehouse + StockLocation."""

    def test_dc_root_links_warehouse(self):
        tenant = create_tenant()
        wh = create_warehouse(name="Fixture DC", tenant=tenant)
        root = create_location(name="Receiving", tenant=tenant, warehouse=wh)
        self.assertEqual(root.warehouse_id, wh.id)
        self.assertEqual(wh.tenant_id, tenant.id)

    def test_retail_root_warehouse_null(self):
        tenant = create_tenant()
        root = create_location(name="Shop Floor", tenant=tenant, warehouse=None)
        self.assertIsNone(root.warehouse_id)

    def test_child_inherits_warehouse_from_dc_parent(self):
        tenant = create_tenant()
        wh = create_warehouse(tenant=tenant)
        root = create_location(name="DC Root", tenant=tenant, warehouse=wh)
        child = create_child_location(root, name="Aisle 1")
        self.assertEqual(child.warehouse_id, wh.id)

    def test_retail_child_stays_unlinked(self):
        tenant = create_tenant()
        root = create_location(name="Store", tenant=tenant, warehouse=None)
        child = create_child_location(root, name="Stockroom")
        self.assertIsNone(child.warehouse_id)


class InventoryModuleFactoriesWarehouseTest(TestCase):
    """``tests/inventory/factories`` parallel helpers."""

    def test_create_warehouse_ensures_tenant(self):
        wh = inventory_factories.create_warehouse(name="Auto-tenant DC")
        self.assertIsNotNone(wh.tenant_id)
        root = inventory_factories.create_location(
            name="Root",
            tenant=wh.tenant,
            warehouse=wh,
        )
        bin_loc = inventory_factories.create_child_location(root, name="Bin 1")
        self.assertEqual(bin_loc.warehouse_id, wh.id)

    def test_retail_tree_via_inventory_factories(self):
        tenant = inventory_factories.create_tenant()
        root = inventory_factories.create_location(
            name="Retail Root",
            tenant=tenant,
            warehouse=None,
        )
        self.assertIsNone(root.warehouse_id)
