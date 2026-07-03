from django.core.management.base import BaseCommand
from odf.opendocument import OpenDocumentText
from odf.style import Style, TextProperties
from odf.table import Table, TableCell, TableColumn, TableRow
from odf.text import P, Span

from pylogenyapp.models import Taxon


class Command(BaseCommand):
    help = "Export all taxa used in LocalityVisit to LibreOffice Writer document."

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            default="locality_visit_taxa.odt",
            help="Output ODT file.",
        )

    def add_scientific_name(self, paragraph, scientific_name, italic_style):
        words = scientific_name.split(" ")

        for index, word in enumerate(words):
            if index > 0:
                paragraph.addText(" ")

            if word in ("agg.", "sect."):
                paragraph.addText(word)
            else:
                paragraph.addElement(
                    Span(
                        stylename=italic_style,
                        text=word,
                    )
                )

    def handle(self, *args, **options):
        taxa = Taxon.objects.filter(
            locality_visits__isnull=False,
        ).select_related(
            "authorship",
        ).distinct()

        output_path = options["output"]

        document = OpenDocumentText()

        italic_style = Style(
            name="Italic",
            family="text",
        )
        italic_style.addElement(
            TextProperties(
                fontstyle="italic",
            )
        )
        document.styles.addElement(italic_style)

        bold_style = Style(
            name="Bold",
            family="text",
        )
        bold_style.addElement(
            TextProperties(
                fontweight="bold",
            )
        )
        document.styles.addElement(bold_style)

        table = Table(name="Taxa")
        table.addElement(TableColumn())
        table.addElement(TableColumn())

        header_row = TableRow()

        scientific_header_cell = TableCell()
        scientific_header_paragraph = P()
        scientific_header_paragraph.addElement(
            Span(
                stylename=bold_style,
                text="Vědecké jméno",
            )
        )
        scientific_header_cell.addElement(scientific_header_paragraph)
        header_row.addElement(scientific_header_cell)

        czech_header_cell = TableCell()
        czech_header_paragraph = P()
        czech_header_paragraph.addElement(
            Span(
                stylename=bold_style,
                text="České jméno",
            )
        )
        czech_header_cell.addElement(czech_header_paragraph)
        header_row.addElement(czech_header_cell)

        table.addElement(header_row)

        for taxon in taxa:
            row = TableRow()

            scientific_cell = TableCell()
            scientific_paragraph = P()

            self.add_scientific_name(
                scientific_paragraph,
                taxon.scientific_name,
                italic_style,
            )

            if taxon.authorship:
                scientific_paragraph.addText(f" {taxon.authorship.text}")

            scientific_cell.addElement(scientific_paragraph)
            row.addElement(scientific_cell)

            czech_cell = TableCell()
            czech_cell.addElement(
                P(
                    text=taxon.name_cs,
                )
            )
            row.addElement(czech_cell)

            table.addElement(row)

        document.text.addElement(table)
        document.save(output_path)

        self.stdout.write(
            self.style.SUCCESS(
                f"Created {output_path} with {taxa.count()} taxa."
            )
        )