"""Integration test: the registry-wired ``/api/v1/plugins/`` endpoint."""

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from tenants.context import set_current_tenant
from tenants.models import TenantRole
from tests.fixtures.factories import create_tenant, create_tenant_membership

User = get_user_model()


class InstalledPluginsAPITests(APITestCase):
    """Proves a registry-contributed route is reachable through the real URLconf."""

    def setUp(self):
        self.tenant = create_tenant(name="Plugins Tenant")
        self.user = User.objects.create_user(
            username="pluginuser", password="testpass123", is_staff=True
        )
        create_tenant_membership(self.tenant, self.user, role=TenantRole.MANAGER)
        self.token = Token.objects.create(user=self.user)
        set_current_tenant(self.tenant)

    def test_requires_authentication(self):
        response = self.client.get("/api/v1/plugins/")
        self.assertIn(
            response.status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )

    def test_lists_loaded_plugins(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.get("/api/v1/plugins/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        self.assertEqual(body["count"], len(body["results"]))
        names = {plugin["name"] for plugin in body["results"]}
        self.assertIn("inventory", names)
        # Every record carries the documented metadata shape.
        sample = next(p for p in body["results"] if p["name"] == "inventory")
        self.assertEqual(
            set(sample),
            {"name", "app_label", "version", "verbose_name", "description", "requires"},
        )
