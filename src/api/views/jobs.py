"""API views for async job status polling."""

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from api.serializers.jobs import AsyncJobSerializer
from inventory.models.job import AsyncJob


class JobStatusView(generics.RetrieveAPIView):
    """``GET /api/v1/jobs/<uuid:job_id>/status/``

    Returns the current status and result of an async job.  Clients
    should poll this endpoint until ``status`` is ``"success"`` or
    ``"failure"``.
    """

    serializer_class = AsyncJobSerializer
    permission_classes = (IsAuthenticated,)
    lookup_field = "pk"
    lookup_url_kwarg = "job_id"

    def get_queryset(self):
        return AsyncJob.objects.filter(created_by=self.request.user)


class JobListView(generics.ListAPIView):
    """``GET /api/v1/jobs/``

    List recent async jobs for the authenticated user.
    """

    serializer_class = AsyncJobSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return AsyncJob.objects.filter(created_by=self.request.user)
