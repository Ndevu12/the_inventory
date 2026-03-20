"""Tests for report views.

Admin report URLs were removed in SaaS redesign — reports are
available to tenants via the REST API at /api/v1/reports/.

Wagtail report views (reports/views.py) remain in the codebase with
explicit tenant filtering per TSS-04.
"""

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest
from django.test import RequestFactory, TestCase

from tenants.context import clear_current_tenant, set_current_tenant

from reports.views import (
    ExpiryReportView,
    LowStockReportView,
    MovementHistoryView,
    OverstockReportView,
    PurchaseSummaryView,
    SalesSummaryView,
    StockValuationView,
)
from tests.fixtures.factories import create_tenant

User = get_user_model()


class ReportViewTenantSecurityTests(TestCase):
    """Test that Wagtail report views require tenant context and filter by tenant."""

    def setUp(self):
        self.factory = RequestFactory()
        self.tenant = create_tenant(name="Test Tenant", slug="test-tenant")
        self.user = User.objects.create_user(
            username="reportuser",
            email="report@test.com",
            password="test123",
            is_staff=True,
        )

    def tearDown(self):
        clear_current_tenant()

    def _get_request(self):
        request = self.factory.get("/reports/stock-valuation/")
        request.user = self.user
        return request

    def test_stock_valuation_raises_without_tenant(self):
        clear_current_tenant()
        view = StockValuationView.as_view()
        request = self._get_request()
        with self.assertRaises(PermissionDenied):
            view(request)

    def test_stock_valuation_returns_data_with_tenant(self):
        set_current_tenant(self.tenant)
        view = StockValuationView.as_view()
        request = self._get_request()
        response = view(request)
        self.assertEqual(response.status_code, 200)

    def test_movement_history_raises_without_tenant(self):
        clear_current_tenant()
        view = MovementHistoryView.as_view()
        request = self._get_request()
        with self.assertRaises(PermissionDenied):
            view(request)

    def test_movement_history_returns_data_with_tenant(self):
        set_current_tenant(self.tenant)
        view = MovementHistoryView.as_view()
        request = self._get_request()
        response = view(request)
        self.assertEqual(response.status_code, 200)

    def test_low_stock_raises_without_tenant(self):
        clear_current_tenant()
        view = LowStockReportView.as_view()
        request = self._get_request()
        with self.assertRaises(PermissionDenied):
            view(request)

    def test_low_stock_returns_data_with_tenant(self):
        set_current_tenant(self.tenant)
        view = LowStockReportView.as_view()
        request = self._get_request()
        response = view(request)
        self.assertEqual(response.status_code, 200)

    def test_overstock_raises_without_tenant(self):
        clear_current_tenant()
        view = OverstockReportView.as_view()
        request = self._get_request()
        with self.assertRaises(PermissionDenied):
            view(request)

    def test_overstock_returns_data_with_tenant(self):
        set_current_tenant(self.tenant)
        view = OverstockReportView.as_view()
        request = self._get_request()
        response = view(request)
        self.assertEqual(response.status_code, 200)

    def test_expiry_report_raises_without_tenant(self):
        clear_current_tenant()
        view = ExpiryReportView.as_view()
        request = self._get_request()
        with self.assertRaises(PermissionDenied):
            view(request)

    def test_expiry_report_returns_data_with_tenant(self):
        set_current_tenant(self.tenant)
        view = ExpiryReportView.as_view()
        request = self._get_request()
        response = view(request)
        self.assertEqual(response.status_code, 200)

    def test_purchase_summary_raises_without_tenant(self):
        clear_current_tenant()
        view = PurchaseSummaryView.as_view()
        request = self._get_request()
        with self.assertRaises(PermissionDenied):
            view(request)

    def test_purchase_summary_returns_data_with_tenant(self):
        set_current_tenant(self.tenant)
        view = PurchaseSummaryView.as_view()
        request = self._get_request()
        response = view(request)
        self.assertEqual(response.status_code, 200)

    def test_sales_summary_raises_without_tenant(self):
        clear_current_tenant()
        view = SalesSummaryView.as_view()
        request = self._get_request()
        with self.assertRaises(PermissionDenied):
            view(request)

    def test_sales_summary_returns_data_with_tenant(self):
        set_current_tenant(self.tenant)
        view = SalesSummaryView.as_view()
        request = self._get_request()
        response = view(request)
        self.assertEqual(response.status_code, 200)
