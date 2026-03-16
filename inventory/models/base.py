from django.conf import settings
from django.db import models
from wagtail.search import index


class TimeStampedModel(index.Indexed, models.Model):
    """Audit fields inherited by all inventory models.
    
    Inherits from Indexed to enable Wagtail search functionality.
    """

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_created",
    )

    class Meta:
        abstract = True
