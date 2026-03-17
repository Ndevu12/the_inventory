from django.db import models
from django.db.models import UniqueConstraint
from treebeard.mp_tree import MP_Node
from wagtail.admin.panels import FieldPanel, FieldRowPanel, MultiFieldPanel, TabbedInterface
from wagtail.search import index
from wagtail.snippets.models import register_snippet

from .base import TimeStampedModel


@register_snippet
class Category(TimeStampedModel, MP_Node):
    """Hierarchical product category using treebeard materialised path."""

    name = models.CharField(
        max_length=255,
        help_text="The display name of this category (e.g., 'Electronics', 'Furniture')",
    )
    slug = models.SlugField(
        max_length=255,
        help_text="URL-friendly name. Auto-generated from name if left blank.",
    )
    description = models.TextField(
        blank=True,
        help_text="Optional description to explain what products belong in this category.",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Inactive categories are hidden from frontend displays but preserved in the database.",
    )

    # treebeard: alphabetical ordering within each tree level
    node_order_by = ["name"]

    panels = [
        TabbedInterface([
            MultiFieldPanel(
                [
                    FieldRowPanel([
                        FieldPanel("name", classname="col6"),
                        FieldPanel("slug", classname="col6"),
                    ]),
                    FieldPanel("description"),
                    FieldPanel("is_active"),
                ],
                heading="Basic Info",
            ),
            MultiFieldPanel(
                [
                    FieldPanel("slug"),
                ],
                heading="Organization",
                classname="collapsed",
            ),
        ])
    ]

    search_fields = [
        index.SearchField("name"),
        index.FilterField("is_active"),
        index.FilterField("slug"),
    ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Override save to handle treebeard MP_Node creation.

        When a new node is created via admin/form (no depth set yet),
        use add_root() to properly initialize treebeard fields.
        """
        if not self.depth:
            type(self).add_root(instance=self)
            return
        super().save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "categories"
        constraints = [
            UniqueConstraint(
                fields=["tenant", "slug"],
                name="unique_category_slug_per_tenant",
            ),
        ]
