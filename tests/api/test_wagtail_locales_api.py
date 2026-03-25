"""Public Wagtail locales API."""

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from wagtail.models import Locale


class WagtailLocalesApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        Locale.objects.get_or_create(language_code="fr")

    def test_list_locales_public(self):
        response = self.client.get("/api/v1/locales/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        codes = {row["code"] for row in response.data}
        self.assertGreaterEqual(codes, {"en", "fr"})
        for row in response.data:
            self.assertIn("display_name", row)
            self.assertIn("is_rtl", row)
            self.assertIn("is_default", row)
