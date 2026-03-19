"""Platform user serializers for platform admin API.

Used for managing all users across tenants. Only superusers can access.
"""

from django.contrib.auth import get_user_model
from rest_framework import serializers

from tenants.models import Tenant, TenantMembership, TenantRole

User = get_user_model()


class PlatformUserListSerializer(serializers.ModelSerializer):
    """List representation for platform users."""

    tenants_display = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "is_active",
            "is_staff",
            "is_superuser",
            "date_joined",
            "tenants_display",
        )

    def get_tenants_display(self, obj):
        memberships = TenantMembership.objects.filter(
            user=obj, is_active=True,
        ).select_related("tenant").order_by("tenant__name")
        return [
            {"id": m.tenant.pk, "name": m.tenant.name, "slug": m.tenant.slug, "role": m.role}
            for m in memberships
        ]


class PlatformUserDetailSerializer(serializers.ModelSerializer):
    """Detail representation for platform users with tenant memberships."""

    tenants_display = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "is_active",
            "is_staff",
            "is_superuser",
            "date_joined",
            "last_login",
            "tenants_display",
        )

    def get_tenants_display(self, obj):
        memberships = TenantMembership.objects.filter(
            user=obj, is_active=True,
        ).select_related("tenant").order_by("tenant__name")
        return [
            {
                "id": m.tenant.pk,
                "name": m.tenant.name,
                "slug": m.tenant.slug,
                "role": m.role,
                "is_default": m.is_default,
                "membership_id": m.pk,
            }
            for m in memberships
        ]


class PlatformUserCreateSerializer(serializers.Serializer):
    """Create a new platform user."""

    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)
    first_name = serializers.CharField(required=False, default="", allow_blank=True)
    last_name = serializers.CharField(required=False, default="", allow_blank=True)
    is_active = serializers.BooleanField(default=True)
    tenant_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        default=list,
    )
    default_role = serializers.ChoiceField(
        choices=[r.value for r in TenantRole],
        default=TenantRole.VIEWER,
        required=False,
    )

    def validate_username(self, value):
        value = (value or "").strip()
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value

    def validate_email(self, value):
        value = (value or "").strip().lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_tenant_ids(self, value):
        if not value:
            return value
        tenants = Tenant.objects.filter(pk__in=value, is_active=True)
        found = set(tenants.values_list("pk", flat=True))
        missing = set(value) - found
        if missing:
            raise serializers.ValidationError(
                f"Invalid tenant(s): {sorted(missing)}"
            )
        return list(found)


class PlatformUserUpdateSerializer(serializers.Serializer):
    """Update an existing platform user."""

    email = serializers.EmailField(required=False)
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    is_active = serializers.BooleanField(required=False)
    is_staff = serializers.BooleanField(required=False)

    def validate_email(self, value):
        if value is None:
            return value
        value = (value or "").strip().lower()
        user = self.context.get("user")
        if user and User.objects.filter(email__iexact=value).exclude(pk=user.pk).exists():
            raise serializers.ValidationError("Another user already has this email.")
        return value


class PlatformUserResetPasswordSerializer(serializers.Serializer):
    """Reset a user's password (platform admin action)."""

    new_password = serializers.CharField(min_length=8, write_only=True)


class TenantMembershipAssignSerializer(serializers.Serializer):
    """Add a user to a tenant."""

    tenant_id = serializers.IntegerField()
    role = serializers.ChoiceField(choices=[r.value for r in TenantRole], default=TenantRole.VIEWER)
    is_default = serializers.BooleanField(default=False)

    def validate_tenant_id(self, value):
        if not Tenant.objects.filter(pk=value, is_active=True).exists():
            raise serializers.ValidationError("Invalid or inactive tenant.")
        return value


class TenantMembershipRemoveSerializer(serializers.Serializer):
    """Remove a user from a tenant."""

    membership_id = serializers.IntegerField()
