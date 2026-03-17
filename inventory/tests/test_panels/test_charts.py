"""Tests for the Chart.js dashboard panels."""

import json
from datetime import date

from django.test import TestCase

from inventory.models import MovementType
from inventory.panels import MovementTrendChart, OrderStatusChart, StockByLocationChart
from procurement.models import PurchaseOrder, Supplier
from sales.models import Customer, SalesOrder

from ..factories import create_location, create_product, create_stock_movement, create_stock_record


class StockByLocationChartTests(TestCase):
    """Test StockByLocationChart context data."""

    def test_empty(self):
        panel = StockByLocationChart()
        context = panel.get_context_data()

        self.assertEqual(json.loads(context["labels_json"]), [])
        self.assertEqual(json.loads(context["data_json"]), [])

    def test_with_data(self):
        loc = create_location(name="Warehouse A")
        product = create_product(sku="SLC-001")
        create_stock_record(product=product, location=loc, quantity=50)

        panel = StockByLocationChart()
        context = panel.get_context_data()

        labels = json.loads(context["labels_json"])
        data = json.loads(context["data_json"])

        self.assertIn("Warehouse A", labels)
        idx = labels.index("Warehouse A")
        self.assertEqual(data[idx], 50)

    def test_excludes_inactive_locations(self):
        active = create_location(name="Active Loc")
        inactive = create_location(name="Closed Loc", is_active=False)
        product = create_product(sku="SLC-002")
        create_stock_record(product=product, location=active, quantity=30)
        create_stock_record(product=product, location=inactive, quantity=20)

        panel = StockByLocationChart()
        context = panel.get_context_data()

        labels = json.loads(context["labels_json"])
        self.assertIn("Active Loc", labels)
        self.assertNotIn("Closed Loc", labels)

    def test_aggregates_across_products(self):
        loc = create_location(name="AggLoc")
        p1 = create_product(sku="SLC-A1")
        p2 = create_product(sku="SLC-A2")
        create_stock_record(product=p1, location=loc, quantity=10)
        create_stock_record(product=p2, location=loc, quantity=15)

        panel = StockByLocationChart()
        context = panel.get_context_data()

        labels = json.loads(context["labels_json"])
        data = json.loads(context["data_json"])
        idx = labels.index("AggLoc")
        self.assertEqual(data[idx], 25)


class MovementTrendChartTests(TestCase):
    """Test MovementTrendChart context data."""

    def test_empty(self):
        panel = MovementTrendChart()
        context = panel.get_context_data()

        labels = json.loads(context["labels_json"])
        data = json.loads(context["data_json"])

        self.assertEqual(len(labels), 31)
        self.assertTrue(all(count == 0 for count in data))

    def test_with_data(self):
        loc = create_location(name="MTC-Wh")
        product = create_product(sku="MTC-001")
        create_stock_movement(
            product=product,
            movement_type=MovementType.RECEIVE,
            quantity=5,
            to_location=loc,
        )

        panel = MovementTrendChart()
        context = panel.get_context_data()

        data = json.loads(context["data_json"])
        self.assertGreater(sum(data), 0, "Today's movement should appear in the chart data")

    def test_labels_are_date_strings(self):
        panel = MovementTrendChart()
        context = panel.get_context_data()

        labels = json.loads(context["labels_json"])
        for label in labels:
            year, month, day = label.split("-")
            self.assertEqual(len(year), 4)
            self.assertEqual(len(month), 2)
            self.assertEqual(len(day), 2)


class OrderStatusChartTests(TestCase):
    """Test OrderStatusChart context data."""

    def test_empty(self):
        panel = OrderStatusChart()
        context = panel.get_context_data()

        self.assertEqual(json.loads(context["po_labels_json"]), [])
        self.assertEqual(json.loads(context["po_data_json"]), [])
        self.assertEqual(json.loads(context["so_labels_json"]), [])
        self.assertEqual(json.loads(context["so_data_json"]), [])

    def test_with_purchase_orders(self):
        supplier = Supplier.objects.create(code="SUP-CH1", name="Chart Supplier")
        PurchaseOrder.objects.create(
            order_number="PO-CH1",
            supplier=supplier,
            status="draft",
            order_date=date.today(),
        )
        PurchaseOrder.objects.create(
            order_number="PO-CH2",
            supplier=supplier,
            status="draft",
            order_date=date.today(),
        )
        PurchaseOrder.objects.create(
            order_number="PO-CH3",
            supplier=supplier,
            status="confirmed",
            order_date=date.today(),
        )

        panel = OrderStatusChart()
        context = panel.get_context_data()

        po_labels = json.loads(context["po_labels_json"])
        po_data = json.loads(context["po_data_json"])

        self.assertIn("Confirmed", po_labels)
        self.assertIn("Draft", po_labels)
        self.assertEqual(po_data[po_labels.index("Draft")], 2)
        self.assertEqual(po_data[po_labels.index("Confirmed")], 1)

    def test_with_sales_orders(self):
        customer = Customer.objects.create(code="CUST-CH1", name="Chart Customer")
        SalesOrder.objects.create(
            order_number="SO-CH1",
            customer=customer,
            status="draft",
            order_date=date.today(),
        )
        SalesOrder.objects.create(
            order_number="SO-CH2",
            customer=customer,
            status="fulfilled",
            order_date=date.today(),
        )

        panel = OrderStatusChart()
        context = panel.get_context_data()

        so_labels = json.loads(context["so_labels_json"])
        so_data = json.loads(context["so_data_json"])

        self.assertIn("Draft", so_labels)
        self.assertIn("Fulfilled", so_labels)
        self.assertEqual(so_data[so_labels.index("Draft")], 1)
        self.assertEqual(so_data[so_labels.index("Fulfilled")], 1)

    def test_with_both_order_types(self):
        supplier = Supplier.objects.create(code="SUP-CH2", name="Both Supplier")
        customer = Customer.objects.create(code="CUST-CH2", name="Both Customer")

        PurchaseOrder.objects.create(
            order_number="PO-B1",
            supplier=supplier,
            status="draft",
            order_date=date.today(),
        )
        SalesOrder.objects.create(
            order_number="SO-B1",
            customer=customer,
            status="confirmed",
            order_date=date.today(),
        )

        panel = OrderStatusChart()
        context = panel.get_context_data()

        po_labels = json.loads(context["po_labels_json"])
        so_labels = json.loads(context["so_labels_json"])

        self.assertEqual(len(po_labels), 1)
        self.assertEqual(len(so_labels), 1)
        self.assertEqual(po_labels[0], "Draft")
        self.assertEqual(so_labels[0], "Confirmed")
