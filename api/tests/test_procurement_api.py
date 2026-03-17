"""API tests for procurement endpoints."""

from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from inventory.models import StockRecord
from inventory.tests.factories import create_location, create_product

from procurement.models import PurchaseOrderStatus
from procurement.tests.factories import (
    create_goods_received_note,
    create_purchase_order,
    create_purchase_order_line,
    create_supplier,
)

User = get_user_model()


class APISetupMixin:
    def setUp(self):
        self.user = User.objects.create_user(
            username="procapi", password="testpass123", is_staff=True,
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")


# =====================================================================
# Suppliers
# =====================================================================


class SupplierAPITests(APISetupMixin, APITestCase):

    def test_list_suppliers(self):
        create_supplier(code="SUP-API1")
        response = self.client.get("/api/v1/suppliers/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_create_supplier(self):
        response = self.client.post("/api/v1/suppliers/", {
            "code": "SUP-NEW",
            "name": "New Supplier",
            "payment_terms": "net_30",
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_search_suppliers(self):
        create_supplier(code="SUP-SRCH", name="Acme Widgets")
        response = self.client.get("/api/v1/suppliers/", {"search": "Acme"})
        self.assertEqual(response.data["count"], 1)


# =====================================================================
# Purchase Orders
# =====================================================================


class PurchaseOrderAPITests(APISetupMixin, APITestCase):

    def setUp(self):
        super().setUp()
        self.supplier = create_supplier(code="SUP-PO-API")
        self.product = create_product(sku="PO-API-P1")

    def test_list_purchase_orders(self):
        create_purchase_order(supplier=self.supplier)
        response = self.client.get("/api/v1/purchase-orders/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_retrieve_includes_lines(self):
        po = create_purchase_order(supplier=self.supplier)
        create_purchase_order_line(
            purchase_order=po, product=self.product,
            quantity=10, unit_cost=Decimal("5.00"),
        )
        response = self.client.get(f"/api/v1/purchase-orders/{po.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["lines"]), 1)

    def test_confirm_action(self):
        po = create_purchase_order(
            order_number="PO-API-CONF",
            supplier=self.supplier,
        )
        create_purchase_order_line(
            purchase_order=po, product=self.product,
        )
        response = self.client.post(f"/api/v1/purchase-orders/{po.pk}/confirm/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], PurchaseOrderStatus.CONFIRMED)

    def test_confirm_without_lines_fails(self):
        po = create_purchase_order(
            order_number="PO-API-EMPTY",
            supplier=self.supplier,
        )
        response = self.client.post(f"/api/v1/purchase-orders/{po.pk}/confirm/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cancel_action(self):
        po = create_purchase_order(
            order_number="PO-API-CANC",
            supplier=self.supplier,
        )
        response = self.client.post(f"/api/v1/purchase-orders/{po.pk}/cancel/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], PurchaseOrderStatus.CANCELLED)

    def test_filter_by_status(self):
        create_purchase_order(
            order_number="PO-API-F1",
            supplier=self.supplier,
            status=PurchaseOrderStatus.DRAFT,
        )
        create_purchase_order(
            order_number="PO-API-F2",
            supplier=self.supplier,
            status=PurchaseOrderStatus.CONFIRMED,
        )
        response = self.client.get(
            "/api/v1/purchase-orders/", {"status": "confirmed"},
        )
        self.assertEqual(response.data["count"], 1)


# =====================================================================
# Goods Received Notes
# =====================================================================


class GoodsReceivedNoteAPITests(APISetupMixin, APITestCase):

    def setUp(self):
        super().setUp()
        self.supplier = create_supplier(code="SUP-GRN-API")
        self.product = create_product(sku="GRN-API-P1")
        self.warehouse = create_location(name="API Warehouse")

    def test_list_grns(self):
        po = create_purchase_order(
            order_number="PO-GRN-API1",
            supplier=self.supplier,
            status=PurchaseOrderStatus.CONFIRMED,
        )
        create_goods_received_note(
            grn_number="GRN-API1",
            purchase_order=po,
            location=self.warehouse,
        )
        response = self.client.get("/api/v1/goods-received-notes/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_receive_action_creates_stock(self):
        po = create_purchase_order(
            order_number="PO-GRN-RCV",
            supplier=self.supplier,
            status=PurchaseOrderStatus.CONFIRMED,
        )
        create_purchase_order_line(
            purchase_order=po,
            product=self.product,
            quantity=100,
            unit_cost=Decimal("10.00"),
        )
        grn = create_goods_received_note(
            grn_number="GRN-RCV",
            purchase_order=po,
            location=self.warehouse,
        )
        response = self.client.post(
            f"/api/v1/goods-received-notes/{grn.pk}/receive/",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_processed"])

        record = StockRecord.objects.get(
            product=self.product, location=self.warehouse,
        )
        self.assertEqual(record.quantity, 100)

    def test_receive_already_processed_fails(self):
        po = create_purchase_order(
            order_number="PO-GRN-DUP",
            supplier=self.supplier,
            status=PurchaseOrderStatus.CONFIRMED,
        )
        create_purchase_order_line(
            purchase_order=po, product=self.product,
            quantity=10, unit_cost=Decimal("5.00"),
        )
        grn = create_goods_received_note(
            grn_number="GRN-DUP",
            purchase_order=po,
            location=self.warehouse,
        )
        self.client.post(f"/api/v1/goods-received-notes/{grn.pk}/receive/")
        response = self.client.post(
            f"/api/v1/goods-received-notes/{grn.pk}/receive/",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
