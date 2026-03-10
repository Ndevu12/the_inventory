from django.db import models
from treebeard.mp_tree import MP_Node
from wagtail.admin.panels import FieldPanel
from wagtail.search import index
from wagtail.snippets.models import register_snippet

from .base import TimeStampedModel


@register_snippet
class Category(TimeStampedModel, MP_Node):
    """Hierarchical product category using treebeard materialised path."""

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    # treebeard: alphabetical ordering within each tree level
    node_order_by = ["name"]

    panels = [
        FieldPanel("name"),
        FieldPanel("slug"),
        FieldPanel("description"),
        FieldPanel("is_active"),
    ]

    search_fields = [
        index.SearchField("name"),
        index.FilterField("is_active"),
        index.FilterField("slug"),
    ]

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "categories"
