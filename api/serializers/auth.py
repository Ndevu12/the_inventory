"""Authentication and user profile serializers."""

from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from tenants.models import TenantMembership

User = get_user_model()


class InventoryTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Extends the default JWT login response with user and tenant info."""

    def validate(self, attrs):
        data = super().validate(attrs)
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
            }
        else:
            data["tenant"] = None

        return data


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name", "is_staff", "is_superuser")
        read_only_fields = ("id", "username", "is_staff", "is_superuser")


class UserProfileSerializer(serializers.ModelSerializer):
    """Writable serializer for the /auth/me/ PATCH endpoint."""

    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name", "is_staff", "is_superuser")
        read_only_fields = ("id", "username", "is_staff", "is_superuser")


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
        }

    def get_memberships(self, obj):
        return list(
            TenantMembership.objects.filter(user=obj["user"], is_active=True)
            .select_related("tenant")
            .values("tenant__id", "tenant__name", "tenant__slug", "role", "is_default")
        )


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
