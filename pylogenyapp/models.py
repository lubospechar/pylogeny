from django.db import models
from django.utils.translation import gettext_lazy as _
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel


class EllenbergIndicatorValue(models.Model):
    light = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Light"),
        help_text=_("L: Indicator values for light"),
    )
    temperature = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Temperature"),
        help_text=_("T: Indicator values for temperature"),
    )
    moisture = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Moisture"),
        help_text=_("M: Indicator values for moisture"),
    )
    reaction = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Reaction"),
        help_text=_("R: Indicator values for reaction"),
    )
    nutrients = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Nutrients"),
        help_text=_("N: Indicator values for nutrients"),
    )
    salinity = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Salinity"),
        help_text=_("S: Indicator values for salinity"),
    )

    class Meta:
        verbose_name = _("Ellenberg indicator value")
        verbose_name_plural = _("Ellenberg indicator values")

    def __str__(self):
        return (
            f"{self.taxon.scientific_name}: "
            f"L: {self.light}, "
            f"T: {self.temperature}, "
            f"M: {self.moisture}, "
            f"R: {self.reaction}, "
            f"N: {self.nutrients}, "
            f"S: {self.salinity}"
        )

class CzechTaxonOrigin(models.Model):
    origin = models.CharField(
        max_length=255,
        unique=True,
        verbose_name=_("Origin"),
    )

    class Meta:
        verbose_name = _("Taxon origin in Czechia")
        verbose_name_plural = _("Taxon origins in Czechia")
        ordering = ["origin"]

    def __str__(self):
        return self.origin


class InvasiveStatus(models.Model):
    status = models.CharField(
        max_length=255,
        unique=True,
        verbose_name=_("Status"),
    )

    class Meta:
        verbose_name = _("Invasive status")
        verbose_name_plural = _("Invasive statuses")
        ordering = ["status"]

    def __str__(self):
        return self.status


class CzechRedList(models.Model):
    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_("Code"),
    )
    description = models.CharField(
        max_length=255,
        verbose_name=_("Description"),
    )

    class Meta:
        verbose_name = _("Czech red list")
        verbose_name_plural = _("Czech red lists")
        ordering = ["code"]

    def __str__(self):
        return self.code

class CzechLegalProtection(models.Model):
    paragraph = models.CharField(
        _("paragraph"),
        max_length=10,
        unique=True,
        help_text=_("Legal protection category paragraph, e.g. §1, §2, §3."),
    )
    description = models.CharField(
        _("description"),
        max_length=255,
        help_text=_("Description of the legal protection category."),
    )

    class Meta:
        verbose_name = _("Czech legal protection category")
        verbose_name_plural = _("Czech legal protection categories")
        ordering = ["paragraph"]

    def __str__(self):
        return self.paragraph

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


class NameAuthorship(models.Model):
    text = models.CharField(
        _("name authorship"),
        max_length=255,
    )

    year = models.PositiveSmallIntegerField(
        _("year of publication"),
        null=True,
        blank=True,
    )

    note = models.TextField(
        _("note"),
        blank=True,
    )

    class Meta:
        verbose_name = _("name authorship")
        verbose_name_plural = _("name authorships")
        ordering = ["text", "year"]
        unique_together = ("text", "year")

    def __str__(self):
        if self.year:
            return f"{self.text}, {self.year}"
        return self.text

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

    authorship = models.ForeignKey(
        NameAuthorship,
        verbose_name=_("name authorship"),
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="taxa",
    )

    parent = TreeForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
        verbose_name=_("Parent taxon"),
    )

    czech_red_list = models.ForeignKey(CzechRedList, null=True, blank=True, on_delete=models.PROTECT)
    czech_legal_protection = models.ForeignKey(CzechLegalProtection, null=True, blank=True, on_delete=models.PROTECT)
    czech_taxon_origin = models.ForeignKey(CzechTaxonOrigin, null=True, blank=True, on_delete=models.PROTECT)
    invasive_status = models.ForeignKey(InvasiveStatus, null=True, blank=True, on_delete=models.PROTECT)
    ellenberg_indicator_values = models.OneToOneField(
        EllenbergIndicatorValue,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    def save(self, *args, **kwargs):
        if self.name_cs:
            self.name_cs = self.name_cs.lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.scientific_name} ({self.taxonomic_rank}), {self.name_cs}'

    def formatted_name(self):
        return f"<i>{self.scientific_name}</i>, {self.name_cs}"

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

