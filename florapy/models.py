import math
from django.contrib.gis.db import models
from django.utils.translation import gettext_lazy as _
from pylogenyapp.models import Taxon

class Project(models.Model):
    project_name = models.CharField(
        max_length=255,
        unique=True,
        verbose_name="Project name",
    )

    description = models.TextField(
        verbose_name="Description",
        blank=True,
    )

    year = models.PositiveSmallIntegerField()

    class Meta:
        verbose_name = "Project"
        verbose_name_plural = "Projects"
        ordering = ["project_name"]

    def __str__(self):
        return self.project_name

class Locality(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True, blank=True, related_name="localities", verbose_name="Project")

    name = models.CharField(
        max_length=255,
        unique=True,
        verbose_name="Locality name",
    )
    polygon = models.PolygonField(
        verbose_name="Polygon",
    )

    polygon_description = models.CharField(
        max_length=255,
        verbose_name=_("Polygon description"),
        blank=True,
        null=True,
    )

    reference_point = models.PointField(
        verbose_name=_("Reference point"),
        null=True,
        blank=True,
    )

    reference_point_description = models.CharField(
        verbose_name=_("Reference point description"),
        max_length=255,
        blank=True,
    )

    geographical_location_description = models.TextField(
        verbose_name="Geographical location description",
        blank=True,
    )

    habitat_description = models.TextField(
        verbose_name="Habitat description",
        blank=True,
    )

    conservation_issues = models.TextField(
        verbose_name="Conservation issues",
        blank=True,
    )

    ecological_indicator_assessment = models.TextField(
        verbose_name="Ecological indicator assessment",
        blank=True,
    )

    def distance_centroid_to_reference_point_m(self):
        if not self.polygon or not self.reference_point:
            return None

        centroid = self.polygon.centroid

        centroid_m = centroid.transform(3857, clone=True)
        reference_point_m = self.reference_point.transform(3857, clone=True)

        return centroid_m.distance(reference_point_m)

    def formatted_distance_centroid_to_reference_point(self):
        distance = self.distance_centroid_to_reference_point_m()

        if distance is None:
            return None

        if distance > 10000:
            return f"{round(distance / 1000)} km"

        if distance > 1000:
            return f"{distance / 1000:.1f} km"

        rounded_distance = int(round(distance / 100) * 100)

        return f"{rounded_distance} m"

    class Meta:
        verbose_name = "Locality"
        verbose_name_plural = "Localities"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def direction_centroid_from_reference_point(self):
        if not self.polygon or not self.reference_point:
            return None

        centroid = self.polygon.centroid

        centroid_m = centroid.transform(3857, clone=True)
        reference_point_m = self.reference_point.transform(3857, clone=True)

        dx = centroid_m.x - reference_point_m.x
        dy = centroid_m.y - reference_point_m.y

        if dx == 0 and dy == 0:
            return None

        angle = math.degrees(math.atan2(dx, dy))
        bearing = (angle + 360) % 360

        directions = [
            {"code": "N", "label": _("north")},
            {"code": "NNE", "label": _("north-northeast")},
            {"code": "NE", "label": _("northeast")},
            {"code": "ENE", "label": _("east-northeast")},
            {"code": "E", "label": _("east")},
            {"code": "ESE", "label": _("east-southeast")},
            {"code": "SE", "label": _("southeast")},
            {"code": "SSE", "label": _("south-southeast")},
            {"code": "S", "label": _("south")},
            {"code": "SSW", "label": _("south-southwest")},
            {"code": "SW", "label": _("southwest")},
            {"code": "WSW", "label": _("west-southwest")},
            {"code": "W", "label": _("west")},
            {"code": "WNW", "label": _("west-northwest")},
            {"code": "NW", "label": _("northwest")},
            {"code": "NNW", "label": _("north-northwest")},
        ]

        index = round(bearing / 22.5) % 16

        return directions[index]

    def polygon_area_m2(self):
        if not self.polygon:
            return None

        polygon_m = self.polygon.transform(3857, clone=True)

        return polygon_m.area

    def formatted_polygon_area(self):
        area_m2 = self.polygon_area_m2()

        if area_m2 is None:
            return None

        if (area_m2 >= 1000):
            area_ha = area_m2 / 10000
            return f"{area_ha:.1f} ha"

        return f"{round(area_m2)} m²"

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