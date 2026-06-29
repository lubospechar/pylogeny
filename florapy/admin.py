from leaflet.admin import LeafletGeoAdmin

from django.contrib import admin

from pylogenyapp.models import TaxonomicRank

from .models import Locality, LocalityVisit


class TaxonomicRankFilter(admin.SimpleListFilter):
    title = "Taxonomic rank"
    parameter_name = "taxonomic_rank"

    def lookups(self, request, model_admin):
        return (
            (rank.pk, rank.code)
            for rank in TaxonomicRank.objects.all()
        )

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(
                taxa__taxonomic_rank_id=self.value()
            ).distinct()
        return queryset


@admin.register(Locality)
class LocalityAdmin(LeafletGeoAdmin):
    list_display = (
        "name",
    )
    search_fields = (
        "name",
    )
    ordering = (
        "name",
    )
    fields = (
        "name",
        "polygon",
    )


@admin.register(LocalityVisit)
class LocalityVisitAdmin(admin.ModelAdmin):
    list_display = (
        "locality",
        "visited_at",
        "taxa_count",
        "taxa_list",
    )
    list_filter = (
        "visited_at",
        "locality",
        TaxonomicRankFilter,
    )
    search_fields = (
        "locality__name",
        "taxa__scientific_name",
        "taxa__name_cs",
    )
    autocomplete_fields = (
        "locality",
    )

    filter_horizontal = (
        "taxa",
    )
    date_hierarchy = "visited_at"
    ordering = (
        "-visited_at",
        "locality",
    )
    fieldsets = (
        (
            "Visit",
            {
                "fields": (
                    "locality",
                    "visited_at",
                ),
            },
        ),
        (
            "Observed taxa",
            {
                "fields": (
                    "taxa",
                ),
            },
        ),
    )

    @admin.display(description="Taxa count")
    def taxa_count(self, obj):
        return obj.taxa.count()

    @admin.display(description="Taxa")
    def taxa_list(self, obj):
        return ", ".join(
            taxon.scientific_name for taxon in obj.taxa.all()
        )