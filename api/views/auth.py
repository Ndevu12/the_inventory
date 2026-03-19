"""Authentication views: JWT login/refresh, profile, password change, config, registration."""

from django.conf import settings as django_settings
from django.db import transaction
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from api.permissions import IsPlatformSuperuser
from api.serializers.auth import (
    ChangePasswordSerializer,
    MeResponseSerializer,
    RegisterTenantSerializer,
    UserProfileSerializer,
    UserSerializer,
)
from tenants.models import Tenant, TenantMembership, TenantRole


class LoginView(TokenObtainPairView):
    """Obtain JWT access + refresh tokens.

    Returns tokens along with user profile and default tenant info.
    """

    permission_classes = (AllowAny,)


class RefreshView(TokenRefreshView):
    """Refresh an expired access token using a valid refresh token."""

    permission_classes = (AllowAny,)


class MeView(APIView):
    """Current user profile with tenant context.

    GET  — return user, current tenant, and all memberships.
    PATCH — update editable profile fields (email, first/last name).
    """

    permission_classes = (IsAuthenticated,)

    def get(self, request):
        data = {"user": request.user}
        serializer = MeResponseSerializer(data, context={"request": request})
        return Response(serializer.data)

    def patch(self, request):
        serializer = UserProfileSerializer(
            request.user, data=request.data, partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class ChangePasswordView(APIView):
    """Change the authenticated user's password."""

    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save()
        return Response({"detail": "Password updated."}, status=status.HTTP_200_OK)


class AuthConfigView(APIView):
    """Public config for auth-related features (e.g. whether registration is enabled)."""

    permission_classes = (AllowAny,)

    def get(self, request):
        return Response({
            "allow_registration": getattr(
                django_settings,
                "ENABLE_PUBLIC_TENANT_REGISTRATION",
                False,
            ),
        })


class RegisterTenantView(APIView):
    """Public tenant (organization) registration.

    Only available when ENABLE_PUBLIC_TENANT_REGISTRATION is True.
    Creates tenant + owner user + membership, returns JWT tokens.
    """

    permission_classes = (AllowAny,)

    def post(self, request):
        if not getattr(django_settings, "ENABLE_PUBLIC_TENANT_REGISTRATION", False):
            return Response(
                {"detail": "Public registration is not enabled for this deployment."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = RegisterTenantSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        from django.contrib.auth import get_user_model
        from tenants.models import SubscriptionPlan

        User = get_user_model()

        with transaction.atomic():
            tenant = Tenant.objects.create(
                name=data["organization_name"].strip(),
                slug=data["slug"],
                is_active=True,
                subscription_plan=SubscriptionPlan.FREE,
            )
            user = User.objects.create_user(
                username=data["owner_username"],
                email=data["owner_email"],
                password=data["owner_password"],
                first_name=data.get("owner_first_name", "") or "",
                last_name=data.get("owner_last_name", "") or "",
                is_staff=True,
            )
            TenantMembership.objects.create(
                tenant=tenant,
                user=user,
                role=TenantRole.OWNER,
                is_active=True,
                is_default=True,
            )

        refresh = RefreshToken.for_user(user)
        memberships = list(
            TenantMembership.objects.filter(user=user, is_active=True)
            .select_related("tenant")
            .values("tenant__id", "tenant__name", "tenant__slug", "role", "is_default")
        )

        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": UserSerializer(user).data,
                "tenant": {
                    "id": tenant.pk,
                    "name": tenant.name,
                    "slug": tenant.slug,
                    "role": TenantRole.OWNER,
                },
                "memberships": memberships,
            },
            status=status.HTTP_201_CREATED,
        )


class ImpersonateStartView(APIView):
    """Start impersonating a user (platform superuser only).

    Returns JWT tokens for the target user. Frontend stores the real user's
    tokens for exit. Impersonation is audited.
    """

    permission_classes = (IsAuthenticated, IsPlatformSuperuser)

    def post(self, request):
        from django.contrib.auth import get_user_model
        from inventory.models.audit import AuditAction
        from inventory.services.audit import AuditService

        User = get_user_model()
        user_id = request.data.get("user_id")
        if not user_id:
            return Response(
                {"detail": "user_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            target_user = User.objects.get(pk=user_id, is_active=True)
        except User.DoesNotExist:
            return Response(
                {"detail": "User not found or inactive."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if target_user.pk == request.user.pk:
            return Response(
                {"detail": "Cannot impersonate yourself."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        real_user = request.user
        membership = (
            TenantMembership.objects.filter(user=target_user, is_active=True)
            .select_related("tenant")
            .order_by("-is_default", "pk")
            .first()
        )
        tenant = membership.tenant if membership else None

        # Use target user's tenant for audit; fallback to real user's or first active
        audit_tenant = tenant
        if audit_tenant is None:
            real_m = (
                TenantMembership.objects.filter(user=real_user, is_active=True)
                .select_related("tenant")
                .first()
            )
            audit_tenant = real_m.tenant if real_m else None
        if audit_tenant is None:
            audit_tenant = Tenant.objects.filter(is_active=True).first()
        if audit_tenant is None:
            return Response(
                {"detail": "No tenant available for audit."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        refresh = RefreshToken.for_user(target_user)
        refresh["impersonated_by"] = real_user.pk

        memberships = list(
            TenantMembership.objects.filter(user=target_user, is_active=True)
            .select_related("tenant")
            .values("tenant__id", "tenant__name", "tenant__slug", "role", "is_default")
        )

        AuditService().log(
            tenant=audit_tenant,
            action=AuditAction.IMPERSONATION_STARTED,
            user=real_user,
            ip_address=AuditService._get_client_ip(request),
            details={
                "impersonated_user_id": target_user.pk,
                "impersonated_username": target_user.username,
            },
        )

        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": UserSerializer(target_user).data,
                "tenant": (
                    {
                        "id": tenant.pk,
                        "name": tenant.name,
                        "slug": tenant.slug,
                        "role": membership.role,
                    }
                    if tenant
                    else None
                ),
                "memberships": memberships,
                "impersonation": {
                    "real_user": UserSerializer(real_user).data,
                    "real_access_token": str(RefreshToken.for_user(real_user).access_token),
                    "real_refresh_token": str(RefreshToken.for_user(real_user)),
                },
            },
            status=status.HTTP_200_OK,
        )


class ImpersonateEndView(APIView):
    """End impersonation (audit only; frontend restores stored tokens).

    Expects the current JWT (impersonation token) to have 'impersonated_by' claim.
    """

    permission_classes = (IsAuthenticated,)

    def post(self, request):
        from rest_framework_simplejwt.tokens import AccessToken
        from rest_framework_simplejwt.exceptions import InvalidToken

        # Decode JWT from Authorization header to get impersonated_by claim
        real_user_id = None
        try:
            auth_header = request.META.get("HTTP_AUTHORIZATION", "")
            if auth_header.startswith("Bearer "):
                token = AccessToken(auth_header[7:])
                real_user_id = token.get("impersonated_by")
        except (InvalidToken, KeyError, TypeError):
            pass

        from django.contrib.auth import get_user_model
        from inventory.models.audit import AuditAction
        from inventory.services.audit import AuditService

        User = get_user_model()
        if not real_user_id:
            return Response(
                {"detail": "Not in impersonation session."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            real_user = User.objects.get(pk=real_user_id)
        except User.DoesNotExist:
            return Response(
                {"detail": "Real user no longer exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        imp_user = request.user

        # Audit tenant: use impersonated user's first tenant or real user's
        membership = (
            TenantMembership.objects.filter(user=imp_user, is_active=True)
            .select_related("tenant")
            .first()
        )
        audit_tenant = membership.tenant if membership else None
        if audit_tenant is None:
            real_m = (
                TenantMembership.objects.filter(user=real_user, is_active=True)
                .select_related("tenant")
                .first()
            )
            audit_tenant = real_m.tenant if real_m else None
        if audit_tenant is None:
            audit_tenant = Tenant.objects.filter(is_active=True).first()

        if audit_tenant:
            AuditService().log(
                tenant=audit_tenant,
                action=AuditAction.IMPERSONATION_ENDED,
                user=real_user,
                ip_address=AuditService._get_client_ip(request),
                details={
                    "impersonated_user_id": imp_user.pk,
                    "impersonated_username": imp_user.username,
                },
            )

        return Response(
            {"detail": "Impersonation ended. Restore your tokens to resume as yourself."},
            status=status.HTTP_200_OK,
        )
