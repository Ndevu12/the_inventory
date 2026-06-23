"""Tests for the dependency-free version helpers."""

from django.test import SimpleTestCase

from plugins.versioning import parse_requirement, parse_version, satisfies


class ParseVersionTests(SimpleTestCase):
    def test_dotted_numeric(self):
        self.assertEqual(parse_version("1.2.3"), (1, 2, 3))

    def test_non_numeric_segments_fall_back_to_zero(self):
        self.assertEqual(parse_version("1.2.0rc1"), (1, 2, 0))

    def test_empty_is_zero(self):
        self.assertEqual(parse_version(""), (0,))


class SatisfiesTests(SimpleTestCase):
    def test_operators(self):
        self.assertTrue(satisfies("1.0.0", "==", "1.0"))
        self.assertTrue(satisfies("1.2", ">=", "1.0"))
        self.assertFalse(satisfies("1.0.0", ">=", "2.0"))
        self.assertTrue(satisfies("1.0", "<=", "1.0.0"))
        self.assertTrue(satisfies("2.0", ">", "1.9.9"))
        self.assertFalse(satisfies("1.0", "<", "1.0"))

    def test_compatible_release(self):
        self.assertTrue(satisfies("1.4", "~=", "1.2"))
        self.assertFalse(satisfies("2.0", "~=", "1.2"))

    def test_unsupported_operator(self):
        with self.assertRaises(ValueError):
            satisfies("1.0", "!=", "1.0")


class ParseRequirementTests(SimpleTestCase):
    def test_bare_name(self):
        self.assertEqual(parse_requirement("inventory"), ("inventory", None, None))

    def test_with_specifier(self):
        self.assertEqual(parse_requirement("barcodes>=1.2"), ("barcodes", ">=", "1.2"))

    def test_operator_without_version_is_invalid(self):
        with self.assertRaises(ValueError):
            parse_requirement("barcodes>=")
