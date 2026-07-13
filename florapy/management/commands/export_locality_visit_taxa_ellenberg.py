from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify
from odf.opendocument import OpenDocumentText
from odf.style import Style, TextProperties
from odf.table import CoveredTableCell, Table, TableCell, TableColumn, TableRow
from odf.text import P, Span

from florapy.models import Locality
from pylogenyapp.models import Taxon


class Command(BaseCommand):
    help = "Export taxa with Ellenberg indicator values for selected locality to LibreOffice Writer document."

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

    def get_output_path(self, locality, output_path):
        if output_path:
            return output_path

        locality_slug = slugify(locality.name)

        if not locality_slug:
            locality_slug = f"locality-{locality.id}"

        return f"{locality_slug}_ellenberg.odt"

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
                text=str(text) if text is not None else "",
            )
        )
        row.addElement(cell)

    def add_bold_text_cell(self, row, text, bold_style):
        cell = TableCell()
        paragraph = P()
        paragraph.addElement(
            Span(
                stylename=bold_style,
                text=str(text) if text is not None else "",
            )
        )
        cell.addElement(paragraph)
        row.addElement(cell)

    def add_spanned_bold_text_cell(self, row, text, bold_style, columns):
        cell = TableCell(
            numbercolumnsspanned=columns,
        )
        paragraph = P()
        paragraph.addElement(
            Span(
                stylename=bold_style,
                text=str(text) if text is not None else "",
            )
        )
        cell.addElement(paragraph)
        row.addElement(cell)

        for _ in range(columns - 1):
            row.addElement(CoveredTableCell())

    def get_ellenberg_value(self, taxon, field_name):
        if taxon.ellenberg_indicator_values is None:
            return None

        return getattr(
            taxon.ellenberg_indicator_values,
            field_name,
        )

    def format_average(self, values):
        if not values:
            return ""

        average = sum(values) / len(values)

        return f"{average:.2f}"

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
            "ellenberg_indicator_values",
        ).distinct()

        taxa = sorted(
            taxa,
            key=lambda taxon: taxon.scientific_name.lower(),
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

        table = Table(name="Taxa Ellenberg")
        table.addElement(TableColumn())
        table.addElement(TableColumn())
        table.addElement(TableColumn())
        table.addElement(TableColumn())
        table.addElement(TableColumn())
        table.addElement(TableColumn())
        table.addElement(TableColumn())
        table.addElement(TableColumn())

        header_row = TableRow()
        self.add_header_cell(header_row, "Vědecké jméno", bold_style)
        self.add_header_cell(header_row, "České jméno", bold_style)
        self.add_header_cell(header_row, "L", bold_style)
        self.add_header_cell(header_row, "T", bold_style)
        self.add_header_cell(header_row, "M", bold_style)
        self.add_header_cell(header_row, "R", bold_style)
        self.add_header_cell(header_row, "N", bold_style)
        self.add_header_cell(header_row, "S", bold_style)
        table.addElement(header_row)

        light_values = []
        temperature_values = []
        moisture_values = []
        reaction_values = []
        nutrients_values = []
        salinity_values = []

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
                scientific_paragraph.addText(f", {taxon.authorship.text}")

            scientific_cell.addElement(scientific_paragraph)
            row.addElement(scientific_cell)

            self.add_text_cell(row, taxon.name_cs)

            light = self.get_ellenberg_value(taxon, "light")
            temperature = self.get_ellenberg_value(taxon, "temperature")
            moisture = self.get_ellenberg_value(taxon, "moisture")
            reaction = self.get_ellenberg_value(taxon, "reaction")
            nutrients = self.get_ellenberg_value(taxon, "nutrients")
            salinity = self.get_ellenberg_value(taxon, "salinity")

            if light is not None:
                light_values.append(light)
            if temperature is not None:
                temperature_values.append(temperature)
            if moisture is not None:
                moisture_values.append(moisture)
            if reaction is not None:
                reaction_values.append(reaction)
            if nutrients is not None:
                nutrients_values.append(nutrients)
            if salinity is not None:
                salinity_values.append(salinity)

            self.add_text_cell(row, light)
            self.add_text_cell(row, temperature)
            self.add_text_cell(row, moisture)
            self.add_text_cell(row, reaction)
            self.add_text_cell(row, nutrients)
            self.add_text_cell(row, salinity)

            table.addElement(row)

        average_row = TableRow()
        self.add_spanned_bold_text_cell(
            average_row,
            "Průměr",
            bold_style,
            2,
        )
        self.add_bold_text_cell(
            average_row,
            self.format_average(light_values),
            bold_style,
        )
        self.add_bold_text_cell(
            average_row,
            self.format_average(temperature_values),
            bold_style,
        )
        self.add_bold_text_cell(
            average_row,
            self.format_average(moisture_values),
            bold_style,
        )
        self.add_bold_text_cell(
            average_row,
            self.format_average(reaction_values),
            bold_style,
        )
        self.add_bold_text_cell(
            average_row,
            self.format_average(nutrients_values),
            bold_style,
        )
        self.add_bold_text_cell(
            average_row,
            self.format_average(salinity_values),
            bold_style,
        )
        table.addElement(average_row)

        document.text.addElement(table)
        document.save(output_path)

        self.stdout.write(
            self.style.SUCCESS(
                f"Created {output_path} with {len(taxa)} taxa "
                f"for locality {locality.id}: {locality.name}."
            )
        )