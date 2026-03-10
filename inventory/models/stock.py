from django.db import models
from treebeard.mp_tree import MP_Node
from wagtail.admin.panels import FieldPanel
from wagtail.search import index
from wagtail.snippets.models import register_snippet

from .base import TimeStampedModel


@register_snippet
class StockLocation(TimeStampedModel, MP_Node):
    """Hierarchical physical location using treebeard materialised path.

    Examples: Main Warehouse → Aisle A → Shelf 3 → Bin 12.
    """

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    # treebeard: alphabetical ordering within each tree level
    node_order_by = ["name"]

    panels = [
        FieldPanel("name"),
        FieldPanel("description"),
        FieldPanel("is_active"),
    ]

    search_fields = [
        index.SearchField("name"),
        index.FilterField("is_active"),
    ]

    def __str__(self):
        return self.name
