from django.db import models
from django.utils.translation import gettext_lazy as _
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel


class TaxonomicRank(models.Model):
    name_cs = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_("Name czech"),
    )
    code = models.SlugField(
        max_length=100,
        unique=True,
        verbose_name=_("Code"),
        help_text=_("For example: species, genus, family, order"),
    )
    level = models.PositiveSmallIntegerField(
        unique=True,
        verbose_name=_("Level"),
        help_text=_("Lower number means a more general rank."),
    )

    class Meta:
        verbose_name = _("Taxonomic rank")
        verbose_name_plural = _("Taxonomic ranks")
        ordering = ["level"]

    def __str__(self):
        return self.code


class Taxon(MPTTModel):
    name_cs = models.CharField(
        max_length=255,
        verbose_name=_("Name czech"),
    )
    scientific_name = models.CharField(
        max_length=255,
        verbose_name=_("Scientific name"),
    )
    taxonomic_rank = models.ForeignKey(
        TaxonomicRank,
        on_delete=models.PROTECT,
        related_name="taxa",
        verbose_name=_("Taxonomic rank"),
    )
    parent = TreeForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
        verbose_name=_("Parent taxon"),
    )

    def save(self, *args, **kwargs):
        if self.name_cs:
            self.name_cs = self.name_cs.lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.scientific_name} ({self.taxonomic_rank})'


    class MPTTMeta:
        order_insertion_by = ["scientific_name"]

    class Meta:
        verbose_name = _("Taxon")
        verbose_name_plural = _("Taxa")
        ordering = ["tree_id", "lft"]
        constraints = [
            models.UniqueConstraint(
                fields=["scientific_name", "taxonomic_rank", "parent"],
                name="unique_taxon_scientific_name_rank_parent",
            ),
        ]