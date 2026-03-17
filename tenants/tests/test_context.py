from django.test import TestCase

from tenants.context import clear_current_tenant, get_current_tenant, set_current_tenant
from tenants.tests.factories import create_tenant


class TenantContextTest(TestCase):
    def tearDown(self):
        clear_current_tenant()

    def test_default_is_none(self):
        clear_current_tenant()
        self.assertIsNone(get_current_tenant())

    def test_set_and_get(self):
        tenant = create_tenant()
        set_current_tenant(tenant)
        self.assertEqual(get_current_tenant(), tenant)

    def test_clear(self):
        tenant = create_tenant()
        set_current_tenant(tenant)
        clear_current_tenant()
        self.assertIsNone(get_current_tenant())

    def test_overwrite(self):
        t1 = create_tenant()
        t2 = create_tenant()
        set_current_tenant(t1)
        set_current_tenant(t2)
        self.assertEqual(get_current_tenant(), t2)
