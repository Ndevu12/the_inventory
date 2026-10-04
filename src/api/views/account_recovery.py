"""Password reset and email confirmation for accounts that can receive mail."""

from django.conf import settings as django_settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import (
    PasswordResetTokenGenerator,
    default_token_generator,
)
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

RESET_DETAIL = "If an account uses that email, a reset link was sent."
INVALID_LINK = "This link is no longer valid."


class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
    key_salt = "api.account_recovery.EmailVerificationTokenGenerator"


email_verification_token = EmailVerificationTokenGenerator()


def _frontend_url(path: str) -> str:
    base = (
        getattr(django_settings, "FRONTEND_URL", "http://localhost:3000")
        or "http://localhost:3000"
    )
    return f"{base.rstrip('/')}/en{path}"


def _deliver(subject: str, message: str, recipient: str) -> None:
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=None,
            recipient_list=[recipient],
            fail_silently=True,
        )
    except Exception:
        return


def _user_from_uid(uid: str):
    User = get_user_model()
    try:
        pk = force_str(urlsafe_base64_decode(uid))
        return User.objects.get(pk=pk, is_active=True)
    except Exception:
        return None


def send_password_reset_email(user) -> None:
    """Email a link that sets a new password for this account."""
    if not user.email:
        return
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    url = _frontend_url(f"/auth/reset-password/{uid}/{token}")
    _deliver(
        "Reset your password",
        (
            "Hi,\n\n"
            "Use the link below to choose a new password:\n"
            f"{url}\n\n"
            "If you did not ask for this, you can ignore this email.\n"
        ),
        user.email,
    )


def send_email_verification(user) -> None:
    """Email a link that confirms this account's address."""
    if not user.email:
        return
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = email_verification_token.make_token(user)
    url = _frontend_url(f"/auth/verify-email/{uid}/{token}")
    _deliver(
        "Confirm your email",
        (
            "Hi,\n\n"
            "Confirm this email address:\n"
            f"{url}\n\n"
            "If you did not create an account, you can ignore this email.\n"
        ),
        user.email,
    )


class PasswordResetRequestView(APIView):
    """Email a reset link when the address matches an active account."""

    permission_classes = (AllowAny,)

    def post(self, request):
        email = str(request.data.get("email") or "").strip()
        if "@" in email:
            User = get_user_model()
            for user in User.objects.filter(email__iexact=email, is_active=True):
                send_password_reset_email(user)
        return Response({"detail": RESET_DETAIL})


class PasswordResetConfirmView(APIView):
    """Set a new password when the reset link is still valid."""

    permission_classes = (AllowAny,)

    def post(self, request):
        user = _user_from_uid(str(request.data.get("uid") or ""))
        token = str(request.data.get("token") or "")
        password = request.data.get("new_password") or ""
        if user is None or not default_token_generator.check_token(user, token):
            return Response(
                {"detail": INVALID_LINK},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            validate_password(password, user)
        except ValidationError as exc:
            return Response(
                {"new_password": list(exc.messages)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.set_password(password)
        user.save()
        return Response({"detail": "Password updated."})


class EmailVerificationConfirmView(APIView):
    """Accept the confirmation link sent after registration."""

    permission_classes = (AllowAny,)

    def post(self, request):
        user = _user_from_uid(str(request.data.get("uid") or ""))
        token = str(request.data.get("token") or "")
        if user is None or not email_verification_token.check_token(user, token):
            return Response(
                {"detail": INVALID_LINK},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response({"detail": "Email confirmed."})
