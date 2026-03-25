"""Authentication and user profile serializers."""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import update_last_login
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.settings import api_settings

from tenants.models import TenantMembership

User = get_user_model()

NO_ACTIVE_TENANT_MEMBERSHIP_DETAIL = {
    "code": "no_tenant_membership",
    "message": (
        "No active organization membership. Platform operators should sign in via Wagtail."
    ),
}


def memberships_payload_for_user(user):
    """Membership rows for API responses (login, /me/, register, impersonate)."""
    return list(
        TenantMembership.objects.filter(user=user, is_active=True)
        .select_related("tenant")
        .order_by("-is_default", "pk")
        .values(
            "tenant__id",
            "tenant__name",
            "tenant__slug",
            "tenant__preferred_language",
            "role",
            "is_default",
        )
    )


class InventoryTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Extends the default JWT login response with user, tenant, and all memberships."""

    def validate(self, attrs):
        data = super(TokenObtainPairSerializer, self).validate(attrs)
        if not TenantMembership.objects.filter(user=self.user, is_active=True).exists():
            raise PermissionDenied(detail=NO_ACTIVE_TENANT_MEMBERSHIP_DETAIL)
        refresh = self.get_token(self.user)
        data["refresh"] = str(refresh)
        data["access"] = str(refresh.access_token)
        if api_settings.UPDATE_LAST_LOGIN:
            update_last_login(None, self.user)

        data["user"] = UserSerializer(self.user).data

        membership = (
            TenantMembership.objects.filter(user=self.user, is_active=True)
            .select_related("tenant")
            .order_by("-is_default", "pk")
            .first()
        )
        if membership:
            data["tenant"] = {
                "id": membership.tenant.pk,
                "name": membership.tenant.name,
                "slug": membership.tenant.slug,
                "role": membership.role,
                "preferred_language": membership.tenant.preferred_language,
            }
        else:
            data["tenant"] = None

        data["memberships"] = memberships_payload_for_user(self.user)

        return data


class InventoryTokenRefreshSerializer(TokenRefreshSerializer):
    """Handle token refresh with graceful user deletion handling."""

    def validate(self, attrs):
        refresh = self.token_class(attrs["refresh"])

        user_id = refresh.payload.get(api_settings.USER_ID_CLAIM, None)
        if user_id:
            try:
                user = User.objects.get(**{api_settings.USER_ID_FIELD: user_id})
            except User.DoesNotExist:
                raise InvalidToken("User associated with token no longer exists.")
            if not api_settings.USER_AUTHENTICATION_RULE(user):
                raise AuthenticationFailed(
                    self.error_messages["no_active_account"],
                    "no_active_account",
                )
            if not TenantMembership.objects.filter(user=user, is_active=True).exists():
                raise PermissionDenied(detail=NO_ACTIVE_TENANT_MEMBERSHIP_DETAIL)

        try:
            return super().validate(attrs)
        except User.DoesNotExist:
            raise InvalidToken("User associated with token no longer exists.")


class UserSerializer(serializers.ModelSerializer):
    """Tenant-app user summary (no platform flags — use Wagtail for staff/superuser)."""

    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name")
        read_only_fields = ("id", "username")


class UserProfileSerializer(serializers.ModelSerializer):
    """Writable serializer for the /auth/me/ PATCH endpoint."""

    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name")
        read_only_fields = ("id", "username")


class MeResponseSerializer(serializers.Serializer):
    """Read-only representation of the current user with tenant context."""

    user = UserSerializer()
    tenant = serializers.SerializerMethodField()
    memberships = serializers.SerializerMethodField()

    def get_tenant(self, obj):
        request = self.context.get("request")
        tenant = getattr(request, "tenant", None) if request else None
        if not tenant:
            return None
        membership = TenantMembership.objects.filter(
            user=obj["user"], tenant=tenant, is_active=True,
        ).first()
        return {
            "id": tenant.pk,
            "name": tenant.name,
            "slug": tenant.slug,
            "role": membership.role if membership else None,
            "preferred_language": tenant.preferred_language,
        }

    def get_memberships(self, obj):
        return memberships_payload_for_user(obj["user"])


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value


class RegisterTenantSerializer(serializers.Serializer):
    """Validate public tenant registration (organization + owner)."""

    organization_name = serializers.CharField(max_length=255)
    organization_slug = serializers.SlugField(required=False, allow_blank=True)
    owner_username = serializers.CharField(max_length=150)
    owner_email = serializers.EmailField()
    owner_password = serializers.CharField(min_length=8, write_only=True)
    owner_first_name = serializers.CharField(required=False, default="", allow_blank=True)
    owner_last_name = serializers.CharField(required=False, default="", allow_blank=True)

    def validate_owner_username(self, value):
        value = (value or "").strip()
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value

    def validate_owner_email(self, value):
        value = (value or "").strip().lower()
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value

    def validate(self, attrs):
        from django.utils.text import slugify
        from tenants.models import Tenant

        slug = (attrs.get("organization_slug") or "").strip()
        if not slug:
            slug = slugify(attrs.get("organization_name", ""))
        if not slug:
            raise serializers.ValidationError(
                {"organization_name": "Organization name must yield a valid slug."}
            )
        if Tenant.objects.filter(slug=slug).exists():
            raise serializers.ValidationError(
                {"organization_slug": "An organization with this slug already exists."}
            )
        attrs["slug"] = slug
        return attrs
