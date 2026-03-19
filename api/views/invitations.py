"""Invitation API views.

Authenticated admin/owner endpoints:
  - POST   /tenants/invitations/        — send an invitation
  - GET    /tenants/invitations/        — list invitations for current tenant
  - DELETE /tenants/invitations/<pk>/   — cancel a pending invitation

Platform admin endpoints (superuser only):
  - GET    /platform/invitations/          — list all invitations
  - DELETE /platform/invitations/<pk>/     — cancel any pending invitation
  - POST   /platform/invitations/<pk>/resend/ — resend invitation (new token, extended expiry)

Public endpoints (no auth required):
  - GET    /auth/invitations/<token>/   — peek at invitation details
  - POST   /auth/invitations/<token>/accept/  — accept & join the tenant
"""

import secrets

from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings as django_settings
from django.db import transaction
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend, FilterSet, filters
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from api.pagination import StandardPagination
from api.permissions import IsPlatformSuperuser
from api.serializers.invitations import (
    AcceptInvitationSerializer,
    InvitationCreateSerializer,
    InvitationInfoSerializer,
    InvitationSerializer,
    PlatformInvitationSerializer,
)
from tenants.models import (
    INVITATION_EXPIRY_DAYS,
    InvitationStatus,
    TenantInvitation,
    TenantMembership,
    TenantRole,
)
from tenants.permissions import IsTenantAdmin

User = get_user_model()


class InvitationListCreateView(ListAPIView):
    """List or create invitations for the current tenant.

    GET  — list all invitations (any status).
    POST — create a new invitation (admin/owner only).
    """

    serializer_class = InvitationSerializer
    permission_classes = (IsAuthenticated, IsTenantAdmin)
    pagination_class = None

    def get_queryset(self):
        tenant = getattr(self.request, "tenant", None)
        if not tenant:
            return TenantInvitation.objects.none()
        return (
            TenantInvitation.objects.filter(tenant=tenant)
            .select_related("invited_by", "tenant")
            .order_by("-created_at")
        )

    def post(self, request):
        tenant = getattr(request, "tenant", None)
        if not tenant:
            return Response(
                {"detail": "No active tenant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = InvitationCreateSerializer(
            data=request.data,
            context={"request": request, "tenant": tenant},
        )
        serializer.is_valid(raise_exception=True)

        invitation = TenantInvitation.objects.create(
            tenant=tenant,
            email=serializer.validated_data["email"],
            role=serializer.validated_data["role"],
            invited_by=request.user,
            expires_at=timezone.now() + timezone.timedelta(days=7),
        )

        _send_invitation_email(invitation, request)

        return Response(
            InvitationSerializer(invitation).data,
            status=status.HTTP_201_CREATED,
        )


class InvitationCancelView(APIView):
    """Cancel (revoke) a pending invitation."""

    permission_classes = (IsAuthenticated, IsTenantAdmin)

    def delete(self, request, pk):
        tenant = getattr(request, "tenant", None)
        if not tenant:
            return Response(
                {"detail": "No active tenant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            invitation = TenantInvitation.objects.get(
                pk=pk, tenant=tenant, status=InvitationStatus.PENDING,
            )
        except TenantInvitation.DoesNotExist:
            return Response(
                {"detail": "Invitation not found or already resolved."},
                status=status.HTTP_404_NOT_FOUND,
            )

        invitation.status = InvitationStatus.CANCELLED
        invitation.save(update_fields=["status"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class InvitationInfoView(APIView):
    """Public endpoint to peek at invitation details before accepting."""

    permission_classes = (AllowAny,)

    def get(self, request, token):
        try:
            invitation = TenantInvitation.objects.select_related("tenant").get(
                token=token,
            )
        except TenantInvitation.DoesNotExist:
            return Response(
                {"detail": "Invalid invitation token."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = InvitationInfoSerializer(invitation)
        return Response(serializer.data)


class AcceptInvitationView(APIView):
    """Accept an invitation and join the tenant.

    If the invitee already has an account (matched by email), they are
    added to the tenant.  Otherwise a new user is created from the
    supplied username/password.

    Returns JWT tokens so the frontend can log the user in immediately.
    """

    permission_classes = (AllowAny,)

    @transaction.atomic
    def post(self, request, token):
        serializer = AcceptInvitationSerializer(
            data={**request.data, "token": token},
        )
        serializer.is_valid(raise_exception=True)

        invitation = serializer.context["invitation"]
        existing_user = serializer.context.get("existing_user")

        if existing_user:
            user = existing_user
        else:
            user = User.objects.create_user(
                username=serializer.validated_data["username"],
                email=invitation.email,
                password=serializer.validated_data["password"],
                first_name=serializer.validated_data.get("first_name", ""),
                last_name=serializer.validated_data.get("last_name", ""),
                is_staff=True,
            )

        has_other_memberships = TenantMembership.objects.filter(
            user=user, is_active=True,
        ).exists()

        TenantMembership.objects.update_or_create(
            tenant=invitation.tenant,
            user=user,
            defaults={
                "role": invitation.role,
                "is_active": True,
                "is_default": not has_other_memberships,
            },
        )

        invitation.status = InvitationStatus.ACCEPTED
        invitation.accepted_at = timezone.now()
        invitation.save(update_fields=["status", "accepted_at"])

        memberships = list(
            TenantMembership.objects.filter(user=user, is_active=True)
            .select_related("tenant")
            .values("tenant__id", "tenant__name", "tenant__slug", "role", "is_default")
        )

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "detail": f"Welcome to {invitation.tenant.name}!",
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": {
                    "id": user.pk,
                    "username": user.username,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "is_staff": user.is_staff,
                },
                "tenant": {
                    "id": invitation.tenant.pk,
                    "name": invitation.tenant.name,
                    "slug": invitation.tenant.slug,
                    "role": invitation.role,
                },
                "memberships": memberships,
            },
            status=status.HTTP_200_OK,
        )


class PlatformInvitationFilter(FilterSet):
    """Filter platform invitations by status, tenant, and date range."""

    status = filters.ChoiceFilter(choices=InvitationStatus.choices)
    tenant = filters.NumberFilter(field_name="tenant_id")
    date_from = filters.DateTimeFilter(field_name="created_at", lookup_expr="gte")
    date_to = filters.DateTimeFilter(field_name="created_at", lookup_expr="lte")

    class Meta:
        model = TenantInvitation
        fields = ["status", "tenant", "date_from", "date_to"]


class PlatformInvitationViewSet(viewsets.ReadOnlyModelViewSet):
    """Platform admin: list all invitations across tenants.

    GET    /platform/invitations/          — list (paginated, filterable)
    DELETE /platform/invitations/<pk>/      — cancel pending invitation
    POST   /platform/invitations/<pk>/resend/ — resend (new token, extended expiry)
    """

    serializer_class = PlatformInvitationSerializer
    permission_classes = (IsPlatformSuperuser,)
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = PlatformInvitationFilter
    ordering = ["-created_at"]
    http_method_names = ["get", "delete", "head", "options"]

    def get_queryset(self):
        return (
            TenantInvitation.objects.select_related("invited_by", "tenant")
            .all()
            .order_by("-created_at")
        )

    def destroy(self, request, *args, **kwargs):
        """Cancel a pending invitation."""
        invitation = self.get_object()
        if invitation.status != InvitationStatus.PENDING:
            return Response(
                {"detail": "Only pending invitations can be cancelled."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        invitation.status = InvitationStatus.CANCELLED
        invitation.save(update_fields=["status"])
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"])
    def resend(self, request, pk=None):
        """Regenerate token, extend expiry, and resend the invitation email."""
        invitation = self.get_object()
        if invitation.status != InvitationStatus.PENDING:
            return Response(
                {"detail": "Only pending invitations can be resent."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        invitation.token = secrets.token_urlsafe(48)
        invitation.expires_at = timezone.now() + timezone.timedelta(
            days=INVITATION_EXPIRY_DAYS
        )
        invitation.save(update_fields=["token", "expires_at"])
        _send_invitation_email(invitation, request)
        serializer = PlatformInvitationSerializer(invitation)
        return Response(serializer.data, status=status.HTTP_200_OK)


def _send_invitation_email(invitation, request):
    """Best-effort email delivery. Fails silently in development."""
    frontend_base = getattr(
        django_settings, "FRONTEND_URL", "http://localhost:3000"
    )
    accept_url = f"{frontend_base}/accept-invitation/{invitation.token}"

    inviter_display = "A team admin"
    if invitation.invited_by:
        inviter_display = (
            invitation.invited_by.get_full_name()
            or invitation.invited_by.username
        )

    subject = f"You've been invited to {invitation.tenant.name}"
    message = (
        f"Hi,\n\n"
        f"{inviter_display} "
        f"has invited you to join \"{invitation.tenant.name}\" "
        f"as {invitation.get_role_display()}.\n\n"
        f"Click the link below to accept:\n{accept_url}\n\n"
        f"This invitation expires on "
        f"{invitation.expires_at.strftime('%B %d, %Y at %H:%M UTC')}.\n\n"
        f"If you didn't expect this invitation, you can safely ignore it."
    )

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=None,
            recipient_list=[invitation.email],
            fail_silently=True,
        )
    except Exception:
        pass
