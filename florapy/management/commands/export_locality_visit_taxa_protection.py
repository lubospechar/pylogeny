from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify
from odf.opendocument import OpenDocumentText
from odf.style import Style, TextProperties
from odf.table import Table, TableCell, TableColumn, TableRow
from odf.text import P, Span

from florapy.models import Locality
from pylogenyapp.models import Taxon


class Command(BaseCommand):
    help = "Export taxa used in LocalityVisit for selected locality to LibreOffice Writer document."

    def add_arguments(self, parser):
        parser.add_argument(
            "locality_id",
            type=int,
            help="ID of locality.",
        )
        parser.add_argument(
            "--output",
            default=None,
            help="Output ODT file. If omitted, filename is generated from locality name.",
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

    def get_family_name(self, taxon):
        family = taxon.get_ancestors(
            include_self=True,
        ).filter(
            taxonomic_rank__code="family",
        ).first()

        if family is None:
            return ""

        return family.scientific_name

    def get_output_path(self, locality, output_path):
        if output_path:
            return output_path

        locality_slug = slugify(locality.name)

        if not locality_slug:
            locality_slug = f"locality-{locality.id}"

        return f"{locality_slug}_taxony.odt"

    def add_header_cell(self, row, text, bold_style):
        cell = TableCell()
        paragraph = P()
        paragraph.addElement(
            Span(
                stylename=bold_style,
                text=text,
            )
        )
        cell.addElement(paragraph)
        row.addElement(cell)

    def add_text_cell(self, row, text):
        cell = TableCell()
        cell.addElement(
            P(
                text=text or "",
            )
        )
        row.addElement(cell)

    def handle(self, *args, **options):
        locality_id = options["locality_id"]

        locality = Locality.objects.filter(
            id=locality_id,
        ).first()

        if locality is None:
            raise CommandError(
                f"Locality with ID {locality_id} does not exist."
            )

        output_path = self.get_output_path(
            locality,
            options["output"],
        )

        taxa = Taxon.objects.filter(
            locality_visits__locality_id=locality_id,
        ).select_related(
            "authorship",
            "taxonomic_rank",
            "czech_red_list",
            "czech_legal_protection",
            "czech_taxon_origin",
            "invasive_status",
        ).distinct()

        taxa_with_family = []

        for taxon in taxa:
            family_name = self.get_family_name(taxon)
            taxa_with_family.append(
                (
                    family_name,
                    taxon,
                )
            )

        taxa_with_family.sort(
            key=lambda item: (
                item[0].lower(),
                item[1].scientific_name.lower(),
            )
        )

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
        table.addElement(TableColumn())
        table.addElement(TableColumn())
        table.addElement(TableColumn())
        table.addElement(TableColumn())
        table.addElement(TableColumn())

        header_row = TableRow()
        self.add_header_cell(header_row, "Čeleď", bold_style)
        self.add_header_cell(header_row, "Vědecké jméno", bold_style)
        self.add_header_cell(header_row, "České jméno", bold_style)
        self.add_header_cell(header_row, "Červený seznam", bold_style)
        self.add_header_cell(header_row, "Zákonná ochrana", bold_style)
        self.add_header_cell(header_row, "Původnost v ČR", bold_style)
        self.add_header_cell(header_row, "Invazní status", bold_style)
        table.addElement(header_row)

        for family_name, taxon in taxa_with_family:
            row = TableRow()

            self.add_text_cell(row, family_name)

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

            self.add_text_cell(row, taxon.name_cs)

            self.add_text_cell(
                row,
                taxon.czech_red_list.code if taxon.czech_red_list else "-",
            )
            self.add_text_cell(
                row,
                (
                    taxon.czech_legal_protection.paragraph
                    if taxon.czech_legal_protection
                    else "-"
                ),
            )
            self.add_text_cell(
                row,
                taxon.czech_taxon_origin.origin if taxon.czech_taxon_origin else "",
            )
            self.add_text_cell(
                row,
                taxon.invasive_status.status if taxon.invasive_status else "",
            )

            table.addElement(row)

        document.text.addElement(table)
        document.save(output_path)

        self.stdout.write(
            self.style.SUCCESS(
                f"Created {output_path} with {taxa.count()} taxa "
                f"for locality {locality.id}: {locality.name}."
            )
        )