"""Serializers for the tenant invitation flow."""

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from rest_framework import serializers

from tenants.models import (
    InvitationStatus,
    TenantInvitation,
    TenantMembership,
    TenantRole,
)
from tenants.role_validation import ensure_valid_tenant_role

User = get_user_model()


class InvitationCreateSerializer(serializers.Serializer):
    """Validate a new invitation request from an owner or coordinator."""

    email = serializers.EmailField()
    role = serializers.CharField(
        max_length=20,
        default=TenantRole.VIEWER,
    )

    def validate_email(self, value):
        value = value.lower().strip()
        tenant = self.context["tenant"]

        if TenantMembership.objects.filter(
            tenant=tenant, user__email=value, is_active=True,
        ).exists():
            raise serializers.ValidationError(
                "This user is already a member of this organization."
            )

        if TenantInvitation.objects.filter(
            tenant=tenant,
            email=value,
            status=InvitationStatus.PENDING,
            expires_at__gt=timezone.now(),
        ).exists():
            raise serializers.ValidationError(
                "A pending invitation already exists for this email."
            )

        return value

    def validate_role(self, value):
        try:
            ensure_valid_tenant_role(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc
        request = self.context.get("request")
        if not request:
            return value
        from tenants.permissions import get_membership
        actor = get_membership(request.user, request=request)
        if not actor:
            raise serializers.ValidationError("You are not a member of this tenant.")
        if value == TenantRole.OWNER and not actor.is_owner:
            raise serializers.ValidationError("Only the owner can invite with the owner role.")
        return value

    def validate(self, attrs):
        tenant = self.context["tenant"]
        if not tenant.is_within_user_limit():
            raise serializers.ValidationError(
                "This organization has reached its user limit. "
                "Upgrade the subscription plan to invite more members."
            )
        return attrs


class InvitationSerializer(serializers.ModelSerializer):
    """Read-only representation of an invitation."""

    invited_by_username = serializers.CharField(
        source="invited_by.username", read_only=True, default=None,
    )
    tenant_name = serializers.CharField(
        source="tenant.name", read_only=True,
    )

    class Meta:
        model = TenantInvitation
        fields = (
            "id", "email", "role", "status", "token",
            "invited_by_username", "tenant_name",
            "created_at", "expires_at", "accepted_at",
        )
        read_only_fields = fields


class PlatformInvitationSerializer(serializers.ModelSerializer):
    """Read-only representation for platform admin (all tenants)."""

    invited_by_username = serializers.CharField(
        source="invited_by.username", read_only=True, allow_null=True,
    )
    tenant_id = serializers.IntegerField(source="tenant.id", read_only=True)
    tenant_name = serializers.CharField(
        source="tenant.name", read_only=True,
    )

    class Meta:
        model = TenantInvitation
        fields = (
            "id",
            "email",
            "tenant_id",
            "tenant_name",
            "role",
            "status",
            "invited_by_username",
            "created_at",
            "expires_at",
            "accepted_at",
        )
        read_only_fields = fields


class AcceptInvitationSerializer(serializers.Serializer):
    """Validate an accept-invitation request.

    Existing users supply only the token.  New users also supply
    username and password to create an account.
    """

    token = serializers.CharField()
    username = serializers.CharField(required=False)
    password = serializers.CharField(required=False, min_length=8, write_only=True)
    first_name = serializers.CharField(required=False, default="")
    last_name = serializers.CharField(required=False, default="")

    def validate_token(self, value):
        try:
            invitation = TenantInvitation.objects.select_related("tenant").get(
                token=value,
            )
        except TenantInvitation.DoesNotExist:
            raise serializers.ValidationError("Invalid invitation token.")

        if invitation.status != InvitationStatus.PENDING:
            raise serializers.ValidationError(
                f"This invitation has already been {invitation.get_status_display().lower()}."
            )
        if invitation.is_expired:
            raise serializers.ValidationError("This invitation has expired.")

        self.context["invitation"] = invitation
        return value

    def validate(self, attrs):
        invitation = self.context.get("invitation")
        if not invitation:
            return attrs

        existing_user = User.objects.filter(email=invitation.email).first()

        if existing_user:
            self.context["existing_user"] = existing_user
            # Require password to prove identity
            password = attrs.get("password")
            if not password:
                raise serializers.ValidationError(
                    {"password": "Enter your password to confirm your identity."}
                )
            if not existing_user.check_password(password):
                raise serializers.ValidationError(
                    {"password": "Incorrect password."}
                )
        else:
            if not attrs.get("username"):
                raise serializers.ValidationError(
                    {"username": "A username is required to create your account."}
                )
            if not attrs.get("password"):
                raise serializers.ValidationError(
                    {"password": "A password is required to create your account."}
                )
            if User.objects.filter(username=attrs["username"]).exists():
                raise serializers.ValidationError(
                    {"username": "This username is already taken."}
                )

        return attrs


class InvitationInfoSerializer(serializers.Serializer):
    """Public read-only info about an invitation (for the accept page)."""

    email = serializers.EmailField()
    role = serializers.CharField()
    tenant_name = serializers.CharField(source="tenant.name")
    expires_at = serializers.DateTimeField()
    status = serializers.CharField()
    needs_account = serializers.SerializerMethodField()

    def get_needs_account(self, obj):
        return not User.objects.filter(email=obj.email).exists()
