"""Unit tests for ReservationRule model."""

from django.test import TestCase

from inventory.models import AllocationStrategy, ReservationRule

from ..factories import (
    create_category,
    create_product,
    create_reservation_rule,
    create_tenant,
)


# =====================================================================
# ReservationRule — creation & defaults
# =====================================================================


class ReservationRuleCreationTests(TestCase):
    """Test ReservationRule creation and field defaults."""

    def test_create_tenant_wide_rule(self):
        rule = create_reservation_rule(name="Global Policy")
        self.assertEqual(rule.name, "Global Policy")
        self.assertIsNone(rule.product)
        self.assertIsNone(rule.category)

    def test_create_category_rule(self):
        category = create_category(name="Electronics", slug="electronics")
        rule = create_reservation_rule(name="Electronics Policy", category=category)
        self.assertEqual(rule.category, category)
        self.assertIsNone(rule.product)

    def test_create_product_rule(self):
        product = create_product(sku="RULE-P1")
        rule = create_reservation_rule(name="Product Policy", product=product)
        self.assertEqual(rule.product, product)
        self.assertIsNone(rule.category)

    def test_default_values(self):
        rule = create_reservation_rule()
        self.assertFalse(rule.auto_reserve_on_order)
        self.assertEqual(rule.reservation_expiry_hours, 72)
        self.assertEqual(rule.allocation_strategy, AllocationStrategy.FIFO)
        self.assertTrue(rule.is_active)

    def test_custom_values(self):
        rule = create_reservation_rule(
            name="Custom",
            auto_reserve_on_order=True,
            reservation_expiry_hours=24,
            allocation_strategy=AllocationStrategy.LIFO,
        )
        self.assertTrue(rule.auto_reserve_on_order)
        self.assertEqual(rule.reservation_expiry_hours, 24)
        self.assertEqual(rule.allocation_strategy, AllocationStrategy.LIFO)

    def test_timestamps_set_on_create(self):
        rule = create_reservation_rule()
        self.assertIsNotNone(rule.created_at)
        self.assertIsNotNone(rule.updated_at)


# =====================================================================
# ReservationRule — __str__
# =====================================================================


class ReservationRuleStrTests(TestCase):
    """Test ReservationRule __str__ representation."""

    def test_str_tenant_wide(self):
        rule = create_reservation_rule(name="Global")
        self.assertIn("Global", str(rule))
        self.assertIn("tenant-wide", str(rule))

    def test_str_category_scoped(self):
        category = create_category(name="Food", slug="food")
        rule = create_reservation_rule(name="Food Rule", category=category)
        text = str(rule)
        self.assertIn("Food Rule", text)
        self.assertIn("category=", text)

    def test_str_product_scoped(self):
        product = create_product(sku="STR-P1", name="Widget")
        rule = create_reservation_rule(name="Widget Rule", product=product)
        text = str(rule)
        self.assertIn("Widget Rule", text)
        self.assertIn("product=", text)


# =====================================================================
# ReservationRule — precedence via get_rule_for_product
# =====================================================================


class ReservationRulePrecedenceTests(TestCase):
    """Test rule precedence: product > category > tenant-wide."""

    def setUp(self):
        self.category = create_category(name="Gadgets", slug="gadgets")
        self.product = create_product(
            sku="PREC-001", name="Super Gadget", category=self.category,
        )

    def test_product_rule_takes_highest_precedence(self):
        create_reservation_rule(name="Tenant Rule")
        create_reservation_rule(name="Category Rule", category=self.category)
        product_rule = create_reservation_rule(
            name="Product Rule", product=self.product,
        )

        result = ReservationRule.get_rule_for_product(self.product)
        self.assertEqual(result, product_rule)

    def test_category_rule_beats_tenant_wide(self):
        create_reservation_rule(name="Tenant Rule")
        category_rule = create_reservation_rule(
            name="Category Rule", category=self.category,
        )

        result = ReservationRule.get_rule_for_product(self.product)
        self.assertEqual(result, category_rule)

    def test_tenant_wide_rule_used_as_fallback(self):
        tenant_rule = create_reservation_rule(name="Tenant Rule")

        result = ReservationRule.get_rule_for_product(self.product)
        self.assertEqual(result, tenant_rule)

    def test_returns_none_when_no_rules_exist(self):
        result = ReservationRule.get_rule_for_product(self.product)
        self.assertIsNone(result)

    def test_inactive_rules_are_skipped(self):
        create_reservation_rule(
            name="Inactive Product Rule",
            product=self.product,
            is_active=False,
        )
        tenant_rule = create_reservation_rule(name="Active Tenant Rule")

        result = ReservationRule.get_rule_for_product(self.product)
        self.assertEqual(result, tenant_rule)

    def test_product_without_category_skips_category_level(self):
        uncategorised = create_product(sku="NOCAT-001", category=None)
        create_reservation_rule(name="Category Rule", category=self.category)
        tenant_rule = create_reservation_rule(name="Tenant Fallback")

        result = ReservationRule.get_rule_for_product(uncategorised)
        self.assertEqual(result, tenant_rule)

    def test_tenant_scoped_lookup(self):
        tenant_a = create_tenant(name="Tenant A", slug="tenant-a")
        tenant_b = create_tenant(name="Tenant B", slug="tenant-b")
        rule_a = create_reservation_rule(name="Rule A", tenant=tenant_a)
        create_reservation_rule(name="Rule B", tenant=tenant_b)

        result = ReservationRule.get_rule_for_product(self.product, tenant=tenant_a)
        self.assertEqual(result, rule_a)


# =====================================================================
# ReservationRule — FK behaviour
# =====================================================================


class ReservationRuleFKTests(TestCase):
    """Test foreign key on_delete behaviour."""

    def test_product_set_null_on_delete(self):
        product = create_product(sku="FK-R1")
        rule = create_reservation_rule(name="FK Rule", product=product)
        product.delete()
        rule.refresh_from_db()
        self.assertIsNone(rule.product)

    def test_category_set_null_on_delete(self):
        category = create_category(name="Temp", slug="temp")
        rule = create_reservation_rule(name="Cat FK Rule", category=category)
        category.delete()
        rule.refresh_from_db()
        self.assertIsNone(rule.category)


# =====================================================================
# ReservationRule — ordering
# =====================================================================


class ReservationRuleOrderingTests(TestCase):
    """Test default ordering is -created_at (newest first)."""

    def test_default_ordering_newest_first(self):
        r1 = create_reservation_rule(name="First")
        r2 = create_reservation_rule(name="Second")
        rules = list(ReservationRule.objects.all())
        self.assertEqual(rules[0].pk, r2.pk)
        self.assertEqual(rules[1].pk, r1.pk)
