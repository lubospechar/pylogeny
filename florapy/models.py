from django.contrib.gis.db import models

from pylogenyapp.models import Taxon


class Locality(models.Model):
    name = models.CharField(
        max_length=255,
        unique=True,
        verbose_name="Locality name",
    )
    polygon = models.PolygonField(
        verbose_name="Polygon",
    )

    class Meta:
        verbose_name = "Locality"
        verbose_name_plural = "Localities"
        ordering = ["name"]

    def __str__(self):
        return self.name


class LocalityVisit(models.Model):
    locality = models.ForeignKey(
        Locality,
        on_delete=models.CASCADE,
        related_name="visits",
        verbose_name="Locality",
    )
    taxa = models.ManyToManyField(
        Taxon,
        related_name="locality_visits",
        verbose_name="Taxa",
        blank=True,
    )
    visited_at = models.DateField(
        verbose_name="Visit date",
    )