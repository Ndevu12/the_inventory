"""Lightweight async-job tracker.

Records the lifecycle of Celery tasks so the API can expose
``GET /api/v1/jobs/<job_id>/status/`` without requiring direct access
to the Celery result backend.

When Celery is not available, the tasks run synchronously and the job
record is still created so callers always have a consistent interface.
"""

import uuid

from django.conf import settings
from django.db import models


class JobStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    STARTED = "started", "Started"
    SUCCESS = "success", "Success"
    FAILURE = "failure", "Failure"


class AsyncJob(models.Model):
    """Tracks the status and result of an async (or sync-fallback) task."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task_name = models.CharField(max_length=255, db_index=True)
    status = models.CharField(
        max_length=20,
        choices=JobStatus.choices,
        default=JobStatus.PENDING,
        db_index=True,
    )
    result = models.JSONField(null=True, blank=True)
    error = models.TextField(blank=True, default="")
    celery_task_id = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Celery AsyncResult ID when dispatched via broker.",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="async_jobs",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.task_name} [{self.status}] {self.id}"

    def mark_started(self):
        self.status = JobStatus.STARTED
        self.save(update_fields=["status", "updated_at"])

    def mark_success(self, result=None):
        self.status = JobStatus.SUCCESS
        self.result = result
        self.save(update_fields=["status", "result", "updated_at"])

    def mark_failure(self, error: str):
        self.status = JobStatus.FAILURE
        self.error = error
        self.save(update_fields=["status", "error", "updated_at"])
