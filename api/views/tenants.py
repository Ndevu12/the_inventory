"""Tenant management API views."""

from datetime import date

from django.http import HttpResponse
from rest_framework import status
from rest_framework.generics import ListAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.permissions import IsPlatformSuperuser
from api.serializers.tenants import TenantMemberSerializer, TenantSerializer
from inventory.models import AuditAction
from inventory.services.audit import AuditService
from tenants.models import Tenant, TenantMembership
from tenants.permissions import IsTenantAdmin, IsTenantMember
from tenants.services import TenantExportService


class CurrentTenantView(APIView):
    """GET / PATCH the current tenant.

    All authenticated members can read; only admins/owners can update.
    """

    def get_permissions(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return [IsAuthenticated(), IsTenantMember()]
        return [IsAuthenticated(), IsTenantAdmin()]

    def get(self, request):
        tenant = getattr(request, "tenant", None)
        if not tenant:
            return Response(
                {"detail": "No active tenant."}, status=status.HTTP_404_NOT_FOUND,
            )
        serializer = TenantSerializer(tenant)
        return Response(serializer.data)

    def patch(self, request):
        tenant = getattr(request, "tenant", None)
        if not tenant:
            return Response(
                {"detail": "No active tenant."}, status=status.HTTP_404_NOT_FOUND,
            )
        serializer = TenantSerializer(tenant, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class TenantMemberListView(ListAPIView):
    """List all members of the current tenant."""

    serializer_class = TenantMemberSerializer
    permission_classes = (IsAuthenticated, IsTenantMember)

    def get_queryset(self):
        tenant = getattr(self.request, "tenant", None)
        if not tenant:
            return TenantMembership.objects.none()
        return (
            TenantMembership.objects.filter(tenant=tenant)
            .select_related("user")
            .order_by("-is_default", "user__username")
        )


class TenantMemberDetailView(RetrieveUpdateDestroyAPIView):
    """View / update role / remove a tenant member.

    Only admins and owners can modify or remove members.
    """

    serializer_class = TenantMemberSerializer
    permission_classes = (IsAuthenticated, IsTenantAdmin)

    def get_queryset(self):
        tenant = getattr(self.request, "tenant", None)
        if not tenant:
            return TenantMembership.objects.none()
        return TenantMembership.objects.filter(tenant=tenant).select_related("user")


class TenantExportView(APIView):
    """Export tenant data as ZIP (JSON + CSV). Platform superuser only.

    GET /platform/tenants/<pk>/export/
    Query params: entity_types (comma-separated), date_from, date_to (YYYY-MM-DD)
    """

    permission_classes = (IsPlatformSuperuser,)

    def get(self, request, pk):
        tenant = Tenant.objects.filter(pk=pk).first()
        if not tenant:
            return Response(
                {"detail": "Tenant not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        params = request.query_params
        entity_types = None
        if params.get("entity_types"):
            entity_types = [x.strip() for x in params["entity_types"].split(",") if x.strip()]

        date_from = None
        date_to = None
        if params.get("date_from"):
            try:
                date_from = date.fromisoformat(params["date_from"])
            except ValueError:
                pass
        if params.get("date_to"):
            try:
                date_to = date.fromisoformat(params["date_to"])
            except ValueError:
                pass

        service = TenantExportService(
            tenant=tenant,
            entity_types=entity_types,
            date_from=date_from,
            date_to=date_to,
        )
        buffer = service.export_to_zip()

        audit = AuditService()
        audit.log(
            tenant=tenant,
            action=AuditAction.TENANT_EXPORT,
            user=request.user,
            ip_address=audit._get_client_ip(request),
            entity_types=list(service.entity_types),
            date_from=date_from.isoformat() if date_from else None,
            date_to=date_to.isoformat() if date_to else None,
        )

        filename = f"{tenant.slug}_export.zip"
        response = HttpResponse(buffer.getvalue(), content_type="application/zip")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
