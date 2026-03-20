"""Tests for inventory admin views tenant filtering and security."""

from django.core.exceptions import PermissionDenied
from django.test import RequestFactory, TestCase

from tenants.context import clear_current_tenant, set_current_tenant

from inventory.filters import ProductFilterSet
from inventory.models import Product
from inventory.views import InventorySearchView, LowStockAlertView

from tests.fixtures.factories import (
    create_category,
    create_location,
    create_product,
    create_stock_record,
    create_tenant,
    create_tenant_membership,
    create_user,
)


class LowStockAlertViewTenantTests(TestCase):
    """Test LowStockAlertView tenant filtering and permission checks."""

    def setUp(self):
        clear_current_tenant()
        self.factory = RequestFactory()
        self.tenant1 = create_tenant(name="Tenant 1", slug="tenant-1")
        self.tenant2 = create_tenant(name="Tenant 2", slug="tenant-2")
        self.user1 = create_user(username="user1", is_staff=True)
        self.user2 = create_user(username="user2", is_staff=True)
        create_tenant_membership(self.tenant1, self.user1)
        create_tenant_membership(self.tenant2, self.user2)

        set_current_tenant(self.tenant1)
        self.cat1 = create_category(name="Cat 1", tenant=self.tenant1)
        self.prod1 = create_product(
            sku="LOW-1",
            tenant=self.tenant1,
            category=self.cat1,
            reorder_point=50,
        )
        self.loc1 = create_location(name="Loc 1", tenant=self.tenant1)
        create_stock_record(self.prod1, self.loc1, quantity=10)

        set_current_tenant(self.tenant2)
        self.cat2 = create_category(name="Cat 2", tenant=self.tenant2)
        self.prod2 = create_product(
            sku="LOW-2",
            tenant=self.tenant2,
            category=self.cat2,
            reorder_point=50,
        )
        self.loc2 = create_location(name="Loc 2", tenant=self.tenant2)
        create_stock_record(self.prod2, self.loc2, quantity=10)

    def tearDown(self):
        clear_current_tenant()

    def test_get_queryset_returns_only_tenant_products(self):
        """Admin users see only their tenant's low-stock products."""
        set_current_tenant(self.tenant1)
        request = self.factory.get("/")
        request.user = self.user1
        view = LowStockAlertView.as_view()
        response = view(request)
        self.assertEqual(response.status_code, 200)
        products = list(response.context_data["products"])
        skus = [p.sku for p in products]
        self.assertIn("LOW-1", skus)
        self.assertNotIn("LOW-2", skus)

    def test_no_tenant_context_raises_permission_denied(self):
        """Raises PermissionDenied when tenant context is not set."""
        clear_current_tenant()
        request = self.factory.get("/")
        request.user = self.user1
        view = LowStockAlertView()
        view.request = request
        view.setup(request)
        with self.assertRaises(PermissionDenied) as cm:
            view.get_queryset()
        self.assertIn("Tenant context", str(cm.exception))

    def test_user_without_membership_raises_permission_denied(self):
        """Raises PermissionDenied when user has no membership in tenant."""
        set_current_tenant(self.tenant1)
        request = self.factory.get("/")
        request.user = self.user2
        view = LowStockAlertView()
        view.request = request
        view.setup(request)
        with self.assertRaises(PermissionDenied) as cm:
            view.get_queryset()
        self.assertIn("do not have access", str(cm.exception))


class InventorySearchViewTenantTests(TestCase):
    """Test InventorySearchView tenant filtering and permission checks."""

    def setUp(self):
        clear_current_tenant()
        self.factory = RequestFactory()
        self.tenant1 = create_tenant(name="Tenant 1", slug="tenant-1")
        self.tenant2 = create_tenant(name="Tenant 2", slug="tenant-2")
        self.user1 = create_user(username="user1", is_staff=True)
        self.user2 = create_user(username="user2", is_staff=True)
        create_tenant_membership(self.tenant1, self.user1)
        create_tenant_membership(self.tenant2, self.user2)

        set_current_tenant(self.tenant1)
        self.cat1 = create_category(name="Electronics", tenant=self.tenant1)
        self.prod1 = create_product(
            sku="PROD-1",
            name="Widget",
            tenant=self.tenant1,
            category=self.cat1,
        )

        set_current_tenant(self.tenant2)
        self.cat2 = create_category(name="Clothing", tenant=self.tenant2)
        self.prod2 = create_product(
            sku="PROD-2",
            name="Gadget",
            tenant=self.tenant2,
            category=self.cat2,
        )

    def tearDown(self):
        clear_current_tenant()

    def test_get_context_data_empty_query_returns_empty_results(self):
        """Empty search query returns empty querysets for all model types."""
        set_current_tenant(self.tenant1)
        request = self.factory.get("/", {"q": ""})
        request.user = self.user1
        view = InventorySearchView()
        view.request = request
        view.setup(request)
        context = view.get_context_data()
        self.assertEqual(context["product_results"].count(), 0)
        self.assertEqual(context["category_results"].count(), 0)
        self.assertEqual(context["location_results"].count(), 0)

    def test_get_context_data_with_query_passes_tenant_filtered_querysets(self):
        """Search receives tenant-filtered querysets (tenant isolation)."""
        from unittest.mock import MagicMock, patch

        set_current_tenant(self.tenant1)
        request = self.factory.get("/", {"q": "Widget"})
        request.user = self.user1
        view = InventorySearchView()
        view.request = request
        view.setup(request)

        captured_querysets = []

        def capture_search(query, queryset):
            captured_querysets.append(queryset)
            self.assertIn("tenant", str(queryset.query))
            return queryset.none()

        with patch("inventory.views.get_search_backend") as mock_get_backend:
            mock_backend = MagicMock()
            mock_backend.search = capture_search
            mock_get_backend.return_value = mock_backend
            view.get_context_data()

        self.assertEqual(len(captured_querysets), 3)

    def test_no_tenant_context_raises_permission_denied(self):
        """Raises PermissionDenied when tenant context is not set."""
        clear_current_tenant()
        request = self.factory.get("/", {"q": "test"})
        request.user = self.user1
        view = InventorySearchView()
        view.request = request
        view.setup(request)
        with self.assertRaises(PermissionDenied) as cm:
            view.get_context_data()
        self.assertIn("Tenant context", str(cm.exception))

    def test_user_without_membership_raises_permission_denied(self):
        """Raises PermissionDenied when user has no membership in tenant."""
        set_current_tenant(self.tenant1)
        request = self.factory.get("/", {"q": "test"})
        request.user = self.user2
        view = InventorySearchView()
        view.request = request
        view.setup(request)
        with self.assertRaises(PermissionDenied) as cm:
            view.get_context_data()
        self.assertIn("do not have access", str(cm.exception))


class ProductFilterSetTenantTests(TestCase):
    """Test ProductFilterSet tenant-scoped category and location dropdowns."""

    def setUp(self):
        clear_current_tenant()
        self.tenant1 = create_tenant(name="Tenant 1", slug="tenant-1")
        self.tenant2 = create_tenant(name="Tenant 2", slug="tenant-2")

        set_current_tenant(self.tenant1)
        self.cat1 = create_category(name="Cat 1", tenant=self.tenant1)
        self.loc1 = create_location(name="Loc 1", tenant=self.tenant1)

        set_current_tenant(self.tenant2)
        self.cat2 = create_category(name="Cat 2", tenant=self.tenant2)
        self.loc2 = create_location(name="Loc 2", tenant=self.tenant2)

    def tearDown(self):
        clear_current_tenant()

    def test_filterset_with_tenant_restricts_category_choices(self):
        """Category filter only shows current tenant's categories."""
        set_current_tenant(self.tenant1)
        qs = Product.objects.filter(tenant=self.tenant1)
        fs = ProductFilterSet({}, queryset=qs, tenant=self.tenant1)
        category_queryset = fs.filters["category"].queryset
        self.assertIn(self.cat1, category_queryset)
        self.assertNotIn(self.cat2, category_queryset)

    def test_filterset_with_tenant_restricts_location_choices(self):
        """Location filter only shows current tenant's locations."""
        set_current_tenant(self.tenant1)
        qs = Product.objects.filter(tenant=self.tenant1)
        fs = ProductFilterSet({}, queryset=qs, tenant=self.tenant1)
        location_queryset = fs.filters["location"].queryset
        self.assertIn(self.loc1, location_queryset)
        self.assertNotIn(self.loc2, location_queryset)
