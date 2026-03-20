"""API tests for sales endpoints."""

from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from inventory.models import MovementType, StockRecord
from inventory.services.stock import StockService
from tests.fixtures.factories import create_location, create_product

from sales.models import SalesOrderStatus
from tests.fixtures.factories import (
    create_customer,
    create_dispatch,
    create_sales_order,
    create_sales_order_line,
)

User = get_user_model()


class APISetupMixin:
    def setUp(self):
        self.user = User.objects.create_user(
            username="salesapi", password="testpass123", is_staff=True,
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")


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
