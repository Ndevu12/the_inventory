"""API tests for the async-job status endpoints."""

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from inventory.models.job import AsyncJob, JobStatus

User = get_user_model()


class JobAPISetupMixin:
    def setUp(self):
        self.user = User.objects.create_user(
            username="jobuser", password="testpass123", is_staff=True,
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")


class JobStatusAPITests(JobAPISetupMixin, APITestCase):

    def test_get_job_status(self):
        job = AsyncJob.objects.create(
            task_name="inventory.tasks.expire_reservations",
            status=JobStatus.SUCCESS,
            result={"expired_count": 3},
            created_by=self.user,
        )
        response = self.client.get(f"/api/v1/jobs/{job.id}/status/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "success")
        self.assertEqual(response.data["result"]["expired_count"], 3)
        self.assertEqual(response.data["task_name"], "inventory.tasks.expire_reservations")

    def test_get_pending_job(self):
        job = AsyncJob.objects.create(
            task_name="inventory.tasks.process_bulk_operation",
            status=JobStatus.PENDING,
            created_by=self.user,
        )
        response = self.client.get(f"/api/v1/jobs/{job.id}/status/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "pending")
        self.assertIsNone(response.data["result"])

    def test_get_failed_job(self):
        job = AsyncJob.objects.create(
            task_name="inventory.tasks.process_import",
            status=JobStatus.FAILURE,
            error="Import validation failed",
            created_by=self.user,
        )
        response = self.client.get(f"/api/v1/jobs/{job.id}/status/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "failure")
        self.assertEqual(response.data["error"], "Import validation failed")

    def test_nonexistent_job_returns_404(self):
        response = self.client.get(
            "/api/v1/jobs/00000000-0000-0000-0000-000000000001/status/"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_returns_401(self):
        job = AsyncJob.objects.create(
            task_name="test", status=JobStatus.PENDING,
        )
        self.client.credentials()
        response = self.client.get(f"/api/v1/jobs/{job.id}/status/")
        self.assertIn(response.status_code, [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ])


class JobListAPITests(JobAPISetupMixin, APITestCase):

    def test_list_own_jobs(self):
        AsyncJob.objects.create(
            task_name="task-a", status=JobStatus.SUCCESS, created_by=self.user,
        )
        AsyncJob.objects.create(
            task_name="task-b", status=JobStatus.PENDING, created_by=self.user,
        )
        other_user = User.objects.create_user(
            username="other", password="pass123", is_staff=True,
        )
        AsyncJob.objects.create(
            task_name="task-c", status=JobStatus.SUCCESS, created_by=other_user,
        )

        response = self.client.get("/api/v1/jobs/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

    def test_superuser_sees_all_jobs(self):
        admin = User.objects.create_superuser(
            username="admin", password="admin123", email="a@b.com",
        )
        admin_token = Token.objects.create(user=admin)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {admin_token.key}")

        AsyncJob.objects.create(
            task_name="task-a", status=JobStatus.SUCCESS, created_by=self.user,
        )
        AsyncJob.objects.create(
            task_name="task-b", status=JobStatus.SUCCESS, created_by=admin,
        )

        response = self.client.get("/api/v1/jobs/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)
