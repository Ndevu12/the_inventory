"""Serializers for the async-job status endpoint."""

from rest_framework import serializers

from inventory.models.job import AsyncJob


class AsyncJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = AsyncJob
        fields = [
            "id",
            "task_name",
            "status",
            "result",
            "error",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
