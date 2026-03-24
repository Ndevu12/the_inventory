"""API tests for sales endpoints."""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from inventory.models import MovementType, StockRecord
from inventory.services.stock import StockService
from sales.models import SalesOrderStatus
from tenants.context import set_current_tenant
from tenants.models import TenantRole
from tests.fixtures.factories import (
    create_customer,
    create_dispatch,
    create_location,
    create_product,
    create_sales_order,
    create_sales_order_line,
    create_tenant,
    create_tenant_membership,
)

User = get_user_model()


class APISetupMixin:
    def setUp(self):
        self.tenant = create_tenant(name="Sales Test Tenant")
        self.user = User.objects.create_user(
            username="salesapi", password="testpass123", is_staff=True,
        )
        create_tenant_membership(self.tenant, self.user, role=TenantRole.MANAGER)
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        set_current_tenant(self.tenant)


# =====================================================================
# Customers
# =====================================================================


class CustomerAPITests(APISetupMixin, APITestCase):

    def test_list_customers(self):
        create_customer(code="CUST-API1")
        response = self.client.get("/api/v1/customers/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_create_customer(self):
        response = self.client.post("/api/v1/customers/", {
            "code": "CUST-NEW",
            "name": "New Customer",
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_customer_without_code_auto_generates(self):
        response = self.client.post(
            "/api/v1/customers/",
            {"name": "Walk-in Buyer"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertTrue(str(response.data.get("code", "")).startswith("C-"))

    def test_search_customers(self):
        create_customer(code="CUST-SRCH", name="Widget Corp")
        response = self.client.get("/api/v1/customers/", {"search": "Widget"})
        self.assertEqual(response.data["count"], 1)


# =====================================================================
# Sales Orders
# =====================================================================


class SalesOrderAPITests(APISetupMixin, APITestCase):

    def setUp(self):
        super().setUp()
        self.customer = create_customer(code="CUST-SO-API")
        self.product = create_product(sku="SO-API-P1")

    def test_list_sales_orders(self):
        create_sales_order(customer=self.customer)
        response = self.client.get("/api/v1/sales-orders/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_create_sales_order_with_lines_auto_number(self):
        response = self.client.post(
            "/api/v1/sales-orders/",
            {
                "customer": self.customer.pk,
                "order_date": str(timezone.localdate()),
                "notes": "",
                "lines": [
                    {
                        "product": self.product.pk,
                        "quantity": 2,
                        "unit_price": "15.00",
                    },
                ],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertTrue(str(response.data.get("order_number", "")).startswith("SO-"))
        self.assertEqual(len(response.data["lines"]), 1)
        self.assertEqual(
            Decimal(str(response.data["lines"][0]["line_total"])),
            Decimal("30.00"),
        )

    def test_create_sales_order_explicit_order_number(self):
        response = self.client.post(
            "/api/v1/sales-orders/",
            {
                "customer": self.customer.pk,
                "order_number": "SO-MANUAL-001",
                "order_date": str(timezone.localdate()),
                "lines": [
                    {
                        "product": self.product.pk,
                        "quantity": 1,
                        "unit_price": "1.00",
                    },
                ],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data["order_number"], "SO-MANUAL-001")

    def test_create_sales_order_requires_lines(self):
        response = self.client.post(
            "/api/v1/sales-orders/",
            {
                "customer": self.customer.pk,
                "order_date": str(timezone.localdate()),
                "lines": [],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_includes_lines(self):
        so = create_sales_order(customer=self.customer)
        create_sales_order_line(
            sales_order=so, product=self.product,
            quantity=10, unit_price=Decimal("15.00"),
        )
        response = self.client.get(f"/api/v1/sales-orders/{so.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["lines"]), 1)

    def test_confirm_action(self):
        so = create_sales_order(
            order_number="SO-API-CONF",
            customer=self.customer,
        )
        create_sales_order_line(
            sales_order=so, product=self.product,
        )
        response = self.client.post(f"/api/v1/sales-orders/{so.pk}/confirm/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], SalesOrderStatus.CONFIRMED)

    def test_confirm_without_lines_fails(self):
        so = create_sales_order(
            order_number="SO-API-EMPTY",
            customer=self.customer,
        )
        response = self.client.post(f"/api/v1/sales-orders/{so.pk}/confirm/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cancel_action(self):
        so = create_sales_order(
            order_number="SO-API-CANC",
            customer=self.customer,
        )
        response = self.client.post(f"/api/v1/sales-orders/{so.pk}/cancel/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], SalesOrderStatus.CANCELLED)

    def test_filter_by_status(self):
        create_sales_order(
            order_number="SO-API-F1",
            customer=self.customer,
            status=SalesOrderStatus.DRAFT,
        )
        create_sales_order(
            order_number="SO-API-F2",
            customer=self.customer,
            status=SalesOrderStatus.CONFIRMED,
        )
        response = self.client.get(
            "/api/v1/sales-orders/", {"status": "draft"},
        )
        self.assertEqual(response.data["count"], 1)


# =====================================================================
# Dispatches
# =====================================================================


class DispatchAPITests(APISetupMixin, APITestCase):

    def setUp(self):
        super().setUp()
        self.customer = create_customer(code="CUST-DSP-API")
        self.product = create_product(sku="DSP-API-P1")
        self.warehouse = create_location(name="API Ship Dock")

    def test_list_dispatches(self):
        so = create_sales_order(
            order_number="SO-DSP-API1",
            customer=self.customer,
            status=SalesOrderStatus.CONFIRMED,
        )
        create_dispatch(
            dispatch_number="DSP-API1",
            sales_order=so,
            from_location=self.warehouse,
        )
        response = self.client.get("/api/v1/dispatches/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_create_dispatch_without_number_auto_generates(self):
        so = create_sales_order(
            order_number="SO-DSP-POST",
            customer=self.customer,
            status=SalesOrderStatus.CONFIRMED,
        )
        response = self.client.post(
            "/api/v1/dispatches/",
            {
                "sales_order": so.pk,
                "dispatch_date": str(timezone.localdate()),
                "from_location": self.warehouse.pk,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertTrue(str(response.data.get("dispatch_number", "")).startswith("DSP-"))

    def test_process_action_creates_stock_movements(self):
        StockService().process_movement(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=200,
            to_location=self.warehouse,
        )
        so = create_sales_order(
            order_number="SO-DSP-PROC",
            customer=self.customer,
            status=SalesOrderStatus.CONFIRMED,
        )
        create_sales_order_line(
            sales_order=so,
            product=self.product,
            quantity=50,
            unit_price=Decimal("15.00"),
        )
        dispatch = create_dispatch(
            dispatch_number="DSP-PROC",
            sales_order=so,
            from_location=self.warehouse,
        )
        response = self.client.post(
            f"/api/v1/dispatches/{dispatch.pk}/process/",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_processed"])

        record = StockRecord.objects.get(
            product=self.product, location=self.warehouse,
        )
        self.assertEqual(record.quantity, 150)

    def test_process_insufficient_stock_fails(self):
        so = create_sales_order(
            order_number="SO-DSP-INSUF",
            customer=self.customer,
            status=SalesOrderStatus.CONFIRMED,
        )
        create_sales_order_line(
            sales_order=so,
            product=self.product,
            quantity=9999,
            unit_price=Decimal("10.00"),
        )
        dispatch = create_dispatch(
            dispatch_number="DSP-INSUF",
            sales_order=so,
            from_location=self.warehouse,
        )
        response = self.client.post(
            f"/api/v1/dispatches/{dispatch.pk}/process/",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
