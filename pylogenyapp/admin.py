from django.contrib import admin
from django.utils.html import format_html
from mptt.admin import MPTTModelAdmin, DraggableMPTTAdmin

from pylogenyapp.models import TaxonomicRank, Taxon, NameAuthorship


@admin.register(TaxonomicRank)
class TaxonomicRankAdmin(admin.ModelAdmin):
    list_display = ("level", "code", "name_cs")
    list_display_links = ("code", "name_cs")
    search_fields = ("code", "name_cs")
    list_filter = ("level",)
    ordering = ("level",)

    fieldsets = (
        (
            None,
            {
                "fields": ("name_cs", "code", "level"),
            },
        ),
    )

@admin.register(NameAuthorship)
class NameAuthorshipAdmin(admin.ModelAdmin):
    list_display = (
        "text",
        "year",
    )

    search_fields = (
        "text",
    )

    list_filter = (
        "year",
    )

    ordering = (
        "text",
        "year",
    )

@admin.register(Taxon)
class TaxonAdmin(DraggableMPTTAdmin):


    list_display = (
        "tree_actions",
        "indented_title",
        "name_cs",
        "taxonomic_rank",
    )
    list_display_links = (
        "indented_title",
    )
    search_fields = (
        "scientific_name",
        "name_cs",
    )

    autocomplete_fields = (
        "parent",
    )

    list_filter = (
        "taxonomic_rank",
    )
    ordering = (
        "tree_id",
        "lft",
    )

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "parent",
                    "taxonomic_rank",
                    "scientific_name",
                    "authorship",
                    "name_cs",
                ),
            },
        ),
    )

    @admin.display(description="Scientific name")
    def indented_title(self, obj):
        return format_html(
            '<div style="text-indent: {indent}px">{title}</div>',
            indent=obj.get_level() * self.mptt_level_indent,
            title=obj.scientific_name,
        )

    indented_title.short_description = "Scientific name"