"""Serializers for tenant management API."""

from django.contrib.auth import get_user_model
from rest_framework import serializers

from tenants.models import Tenant, TenantMembership, TenantRole

User = get_user_model()


class TenantSerializer(serializers.ModelSerializer):
    user_count = serializers.SerializerMethodField()
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Tenant
        fields = (
            "id", "name", "slug", "is_active",
            "branding_site_name", "branding_primary_color",
            "subscription_plan", "subscription_status",
            "max_users", "max_products",
            "user_count", "product_count",
            "created_at", "updated_at",
        )
        read_only_fields = (
            "id", "slug", "is_active",
            "subscription_plan", "subscription_status",
            "max_users", "max_products",
            "created_at", "updated_at",
        )

    def get_user_count(self, obj):
        return obj.user_count()

    def get_product_count(self, obj):
        return obj.product_count()


class TenantMemberSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.CharField(source="user.email", read_only=True)
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)

    class Meta:
        model = TenantMembership
        fields = (
            "id", "username", "email", "first_name", "last_name",
            "role", "is_active", "is_default", "created_at",
        )
        read_only_fields = ("id", "username", "email", "first_name", "last_name", "created_at")

    def validate_role(self, value):
        request = self.context.get("request")
        if not request:
            return value
        from tenants.permissions import get_membership
        actor = get_membership(request.user)
        if not actor:
            raise serializers.ValidationError("You are not a member of this tenant.")
        if value == TenantRole.OWNER and not actor.is_owner:
            raise serializers.ValidationError("Only the owner can assign the owner role.")
        return value
