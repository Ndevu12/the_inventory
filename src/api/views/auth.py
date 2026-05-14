"""Authentication views: JWT login/refresh, profile, password change, config, registration."""

from django.conf import settings as django_settings
from django.db import transaction
from drf_spectacular.utils import extend_schema, extend_schema_view
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
    memberships_payload_for_user,
)
from api.utils.cookies import set_jwt_cookie, delete_jwt_cookie
from tenants.models import Tenant, TenantMembership, TenantRole


class LoginView(TokenObtainPairView):
    """Obtain JWT access + refresh tokens.

    Returns tokens along with user profile and default tenant info.
    Sets tokens in HttpOnly cookies for browser clients while maintaining
    backward compatibility for mobile/API clients via JSON response body.
    """

    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        """Override to set tokens in HttpOnly cookies after successful login."""
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == status.HTTP_200_OK:
            access_token = response.data.get('access')
            refresh_token = response.data.get('refresh')
            
            if access_token and refresh_token:
                # Set access token cookie using centralized utility
                set_jwt_cookie(
                    response,
                    'access_token',
                    access_token,
                    max_age=django_settings.JWT_ACCESS_TOKEN_COOKIE_MAX_AGE,
                )
                
                # Set refresh token cookie using centralized utility
                set_jwt_cookie(
                    response,
                    'refresh_token',
                    refresh_token,
                    max_age=django_settings.JWT_REFRESH_TOKEN_COOKIE_MAX_AGE,
                )
        
        return response


class RefreshView(TokenRefreshView):
    """Refresh an expired access token using a valid refresh token.
    
    Accepts refresh token from cookie or JSON body. Returns new access token
    in both HttpOnly cookie and JSON response body.
    """

    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        """Override to handle refresh token from cookie if not in request body."""
        # If refresh token is not in the request body, try to get it from cookies
        if 'refresh' not in request.data and 'refresh_token' in request.COOKIES:
            # Check if request.data is a QueryDict (from form data) or dict (from JSON)
            if hasattr(request.data, '_mutable'):
                request.data._mutable = True
                request.data['refresh'] = request.COOKIES['refresh_token']
                request.data._mutable = False
            else:
                # For dict/other types, just add the key
                request.data['refresh'] = request.COOKIES['refresh_token']
        
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == status.HTTP_200_OK:
            access_token = response.data.get('access')
            
            if access_token:
                # Set new access token cookie using centralized utility
                set_jwt_cookie(
                    response,
                    'access_token',
                    access_token,
                    max_age=django_settings.JWT_ACCESS_TOKEN_COOKIE_MAX_AGE,
                )
        
        return response


class LogoutView(APIView):
    """Logout and clear authentication cookies.
    
    POST endpoint that clears access_token and refresh_token cookies.
    Can be called by authenticated users or as a public endpoint.
    """

    permission_classes = (AllowAny,)

    def post(self, request):
        """Clear authentication cookies on logout."""
        response = Response(
            {"detail": "Successfully logged out."},
            status=status.HTTP_200_OK
        )
        
        # Clear authentication cookies using centralized utility
        delete_jwt_cookie(response, 'access_token')
        delete_jwt_cookie(response, 'refresh_token')
        
        return response


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
                is_staff=False,
            )
            TenantMembership.objects.create(
                tenant=tenant,
                user=user,
                role=TenantRole.OWNER,
                is_active=True,
                is_default=True,
            )

        refresh = RefreshToken.for_user(user)
        memberships = memberships_payload_for_user(user)

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
                    "preferred_language": tenant.preferred_language,
                },
                "memberships": memberships,
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema_view(
    post=extend_schema(
        summary="Start API impersonation (platform support)",
        description=(
            "Issues JWTs for a **tenant member** (active ``TenantMembership`` required) on "
            "behalf of a **Django superuser**. Every start is written to the compliance audit "
            "log. Prefer Wagtail admin for routine platform work; this route exists for "
            "support and automation when the operator needs the same JWT shape as the SPA. "
            "Set ``ENABLE_API_IMPERSONATION=False`` to disable while keeping Wagtail session "
            "impersonation."
        ),
        tags=["Authentication"],
    ),
)
class ImpersonateStartView(APIView):
    """Platform superuser only: JWT as another user (audited, optional env kill-switch)."""

    permission_classes = (IsAuthenticated, IsPlatformSuperuser)

    def post(self, request):
        if not getattr(django_settings, "ENABLE_API_IMPERSONATION", True):
            return Response(
                {
                    "detail": (
                        "API impersonation is disabled for this deployment. "
                        "Use Wagtail admin for session-based impersonation."
                    ),
                },
                status=status.HTTP_403_FORBIDDEN,
            )

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

        if target_user.is_superuser:
            return Response(
                {"detail": "Cannot impersonate platform superusers."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        real_user = request.user
        membership = (
            TenantMembership.objects.filter(user=target_user, is_active=True)
            .select_related("tenant")
            .order_by("-is_default", "pk")
            .first()
        )
        if membership is None:
            return Response(
                {
                    "detail": (
                        "Target user must have at least one active organization membership. "
                        "API impersonation issues a tenant-member identity for inventory API "
                        "access; use Wagtail for users without memberships."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        tenant = membership.tenant

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

        memberships = memberships_payload_for_user(target_user)

        AuditService().log(
            tenant=audit_tenant,
            action=AuditAction.IMPERSONATION_STARTED,
            user=real_user,
            ip_address=AuditService._get_client_ip(request),
            details={
                "impersonated_user_id": target_user.pk,
                "impersonated_username": target_user.username,
                "channel": "api",
            },
        )

        real_refresh = RefreshToken.for_user(real_user)

        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": UserSerializer(target_user).data,
                "tenant": {
                    "id": tenant.pk,
                    "name": tenant.name,
                    "slug": tenant.slug,
                    "role": membership.role,
                    "preferred_language": tenant.preferred_language,
                },
                "memberships": memberships,
                "impersonation": {
                    "real_user": UserSerializer(real_user).data,
                    "real_access_token": str(real_refresh.access_token),
                    "real_refresh_token": str(real_refresh),
                },
            },
            status=status.HTTP_200_OK,
        )


@extend_schema_view(
    post=extend_schema(
        summary="End API impersonation (audit)",
        description=(
            "Record end of an API impersonation session. The caller must present an access "
            "JWT issued by ``/auth/impersonate/start/`` (includes ``impersonated_by``). "
            "The original operator must still be a Django superuser."
        ),
        tags=["Authentication"],
    ),
)
class ImpersonateEndView(APIView):
    """Audit-only end of API impersonation; client restores the superuser JWT locally."""

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
            real_user = User.objects.get(pk=int(real_user_id))
        except (User.DoesNotExist, ValueError, TypeError):
            return Response(
                {"detail": "Real user no longer exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not real_user.is_superuser:
            return Response(
                {
                    "detail": (
                        "Impersonation session is no longer valid: the issuing account "
                        "is not a platform superuser. Restore your stored operator tokens "
                        "or sign in via Wagtail."
                    ),
                    "code": "impersonation_invalid_operator",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        imp_user = request.user

        if imp_user.pk == real_user.pk:
            return Response(
                {"detail": "Not in impersonation session."},
                status=status.HTTP_400_BAD_REQUEST,
            )

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
                    "channel": "api",
                },
            )

        return Response(
            {"detail": "Impersonation ended. Restore your tokens to resume as yourself."},
            status=status.HTTP_200_OK,
        )
