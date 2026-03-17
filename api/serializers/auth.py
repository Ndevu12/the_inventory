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
        fields = ("id", "username", "email", "first_name", "last_name", "is_staff")
        read_only_fields = ("id", "username", "is_staff")


class UserProfileSerializer(serializers.ModelSerializer):
    """Writable serializer for the /auth/me/ PATCH endpoint."""

    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name", "is_staff")
        read_only_fields = ("id", "username", "is_staff")


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
