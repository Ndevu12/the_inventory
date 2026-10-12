"""Password reset and email confirmation."""

from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.test import APIClient

from api.views.account_recovery import email_verification_token

User = get_user_model()


@override_settings(FRONTEND_URL="http://localhost:3000")
class AccountRecoveryTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="resetuser",
            email="reset@example.com",
            password="Old-Password-123",
        )

    @patch("api.views.account_recovery.send_mail")
    def test_unknown_email_matches_a_known_one(self, send_mail):
        known = self.client.post(
            reverse("api-password-reset"),
            {"email": "reset@example.com"},
            format="json",
        )
        unknown = self.client.post(
            reverse("api-password-reset"),
            {"email": "nobody@example.com"},
            format="json",
        )
        self.assertEqual(known.status_code, status.HTTP_200_OK)
        self.assertEqual(known.json(), unknown.json())
        self.assertEqual(send_mail.call_count, 1)
        self.assertIn(
            "/en/auth/reset-password/",
            send_mail.call_args.kwargs["message"],
        )

    def test_confirm_replaces_the_password(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        response = self.client.post(
            reverse("api-password-reset-confirm"),
            {
                "uid": uid,
                "token": token,
                "new_password": "New-Password-123",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("New-Password-123"))

    def test_a_reset_token_does_not_confirm_email(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        response = self.client.post(
            reverse("api-email-verification-confirm"),
            {"uid": uid, "token": token},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verification_link_is_accepted(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = email_verification_token.make_token(self.user)
        response = self.client.post(
            reverse("api-email-verification-confirm"),
            {"uid": uid, "token": token},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @override_settings(ENABLE_PUBLIC_TENANT_REGISTRATION=True)
    @patch("api.views.auth.send_email_verification")
    def test_registration_sends_a_confirmation(self, send_email_verification):
        response = self.client.post(
            reverse("api-register"),
            {
                "organization_name": "Reset Org",
                "owner_username": "resetowner",
                "owner_email": "owner@example.com",
                "owner_password": "Owner-Password-123",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        send_email_verification.assert_called_once()
