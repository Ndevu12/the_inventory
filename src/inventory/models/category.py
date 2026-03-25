from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import UniqueConstraint
from treebeard.mp_tree import MP_Node
from wagtail.admin.panels import FieldPanel, FieldRowPanel, MultiFieldPanel, TabbedInterface
from wagtail.models import Locale, TranslatableMixin
from wagtail.search import index

from .base import TimeStampedModel


class Category(TranslatableMixin, TimeStampedModel, MP_Node):
    """Hierarchical product category using treebeard materialised path."""

    # wagtail-localize + TranslatableMixin copy must not duplicate treebeard paths.
    default_exclude_fields_in_copy = ["path", "depth", "numchild"]

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

        For locale copies (wagtail-localize admin **Translate** or API helpers), the
        clone has no tree fields yet but must mirror the source node's depth: root
        rows become roots; children attach under the translated parent.
        """
        if self.depth:
            super().save(*args, **kwargs)
            return

        siblings = (
            type(self)
            .objects.filter(
                translation_key=self.translation_key,
                tenant_id=self.tenant_id,
            )
            .exclude(locale_id=self.locale_id)
        )
        if self.pk:
            siblings = siblings.exclude(pk=self.pk)

        if not siblings.exists():
            type(self).add_root(instance=self)
            return

        default = Locale.get_default()
        source = siblings.filter(locale_id=default.id).first() or siblings.first()
        if source.depth == 1:
            type(self).add_root(instance=self)
            return

        parent = source.get_parent()
        parent_t = parent.get_translation_or_none(self.locale)
        if parent_t is None:
            raise ValidationError(
                "Translate the parent category into this locale first, then translate this category."
            )
        parent_t.add_child(instance=self)

    class Meta:
        verbose_name_plural = "categories"
        constraints = [
            UniqueConstraint(
                fields=["translation_key", "locale"],
                name="unique_translation_key_locale_inventory_category",
            ),
            UniqueConstraint(
                fields=["tenant", "slug", "locale"],
                name="unique_category_slug_per_tenant_locale",
            ),
        ]
