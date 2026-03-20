from django.test import TestCase

from inventory.models import StockLocation
from tenants.context import clear_current_tenant, set_current_tenant
from tenants.managers import TenantAwareManager
from tests.fixtures.factories import create_tenant


class TenantAwareManagerTest(TestCase):
    """Test the TenantAwareManager using StockLocation as a concrete model.

    StockLocation inherits from TimeStampedModel (which has the tenant FK)
    and does not override the default manager, making it a good candidate.
    Note: StockLocation actually uses MP_Node's manager, so we'll test
    the manager behaviour directly with a model that has tenant FK.
    """

    def setUp(self):
        self.t1 = create_tenant(slug="tenant-a")
        self.t2 = create_tenant(slug="tenant-b")

    def tearDown(self):
        clear_current_tenant()

    def _create_locations(self):
        """Create locations scoped to different tenants via treebeard API."""
        loc1 = StockLocation.add_root(name="Warehouse A", tenant=self.t1)
        loc2 = StockLocation.add_root(name="Warehouse B", tenant=self.t2)
        loc3 = StockLocation.add_root(name="Warehouse C", tenant=self.t1)
        return loc1, loc2, loc3

    def test_manager_unscoped_returns_all(self):
        self._create_locations()
        mgr = TenantAwareManager()
        mgr.model = StockLocation
        mgr.auto_created = True
        all_qs = mgr.unscoped()
        self.assertEqual(all_qs.count(), 3)

    def test_manager_scoped_filters_by_tenant(self):
        self._create_locations()
        mgr = TenantAwareManager()
        mgr.model = StockLocation
        mgr.auto_created = True
        set_current_tenant(self.t1)
        self.assertEqual(mgr.get_queryset().count(), 2)
        set_current_tenant(self.t2)
        self.assertEqual(mgr.get_queryset().count(), 1)

    def test_manager_no_tenant_returns_all(self):
        self._create_locations()
        mgr = TenantAwareManager()
        mgr.model = StockLocation
        mgr.auto_created = True
        clear_current_tenant()
        with self.assertLogs("tenants.managers", level="WARNING") as captured:
            self.assertEqual(mgr.get_queryset().count(), 3)
        self.assertTrue(
            any("Querying without tenant context" in line for line in captured.output),
            captured.output,
        )

    def test_manager_for_tenant_filters_regardless_of_context(self):
        loc1, loc2, loc3 = self._create_locations()
        mgr = TenantAwareManager()
        mgr.model = StockLocation
        mgr.auto_created = True
        set_current_tenant(self.t2)
        qs = mgr.for_tenant(self.t1)
        self.assertEqual(set(qs.values_list("pk", flat=True)), {loc1.pk, loc3.pk})

    def test_queryset_for_tenant_helper(self):
        loc1, loc2, loc3 = self._create_locations()
        mgr = TenantAwareManager()
        mgr.model = StockLocation
        mgr.auto_created = True
        qs = mgr.unscoped().for_tenant(self.t1)
        self.assertEqual(set(qs.values_list("pk", flat=True)), {loc1.pk, loc3.pk})
