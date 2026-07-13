import re
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify
from odf import style, text
from odf.opendocument import OpenDocumentText
from odf.style import (
    ParagraphProperties,
    TableCellProperties,
    TableColumnProperties,
    TableRowProperties,
    TextProperties,
)
from odf.table import CoveredTableCell, Table, TableCell, TableColumn, TableRow

from florapy.models import Locality
from pylogenyapp.models import Taxon


class Command(BaseCommand):
    help = "Export locality data and texts to LibreOffice Writer ODT document."

    body_text_style_name = "Text_20_body"

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

    def get_output_path(self, locality, output_path):
        if output_path:
            path = Path(output_path)

            if path.suffix:
                return path.with_suffix(".odt")

            return path.with_suffix(".odt")

        locality_slug = slugify(locality.name)

        if not locality_slug:
            locality_slug = f"locality-{locality.id}"

        return Path(f"{locality_slug}.odt")

    def clean_generated_text(self, value):
        if not value:
            return ""

        return str(value).replace(
            "GENEROVÁNO AI:",
            "",
        ).strip()

    def create_styles(self, document):
        body_text_style = style.Style(
            name=self.body_text_style_name,
            displayname="Tělo textu",
            family="paragraph",
            parentstylename="Standard",
        )
        body_text_style.addElement(
            TextProperties(
                fontsize="11pt",
            )
        )
        body_text_style.addElement(
            ParagraphProperties(
                margintop="0cm",
                marginbottom="0.21cm",
                lineheight="120%",
            )
        )
        document.styles.addElement(body_text_style)

        bold_style = style.Style(
            name="BoldText",
            family="text",
        )
        bold_style.addElement(
            TextProperties(
                fontweight="bold",
            )
        )
        document.styles.addElement(bold_style)

        italic_style = style.Style(
            name="ItalicText",
            family="text",
        )
        italic_style.addElement(
            TextProperties(
                fontstyle="italic",
            )
        )
        document.styles.addElement(italic_style)

        bold_italic_style = style.Style(
            name="BoldItalicText",
            family="text",
        )
        bold_italic_style.addElement(
            TextProperties(
                fontweight="bold",
                fontstyle="italic",
            )
        )
        document.styles.addElement(bold_italic_style)

        table_cell_style = style.Style(
            name="TableCell",
            family="table-cell",
        )
        table_cell_style.addElement(
            TableCellProperties(
                border="0.05pt solid #999999",
                padding="0.04cm",
                verticalalign="middle",
            )
        )
        document.styles.addElement(table_cell_style)

        table_row_style = style.Style(
            name="TableRow",
            family="table-row",
        )
        table_row_style.addElement(
            TableRowProperties(
                rowheight="0.45cm",
                useoptimalrowheight=True,
            )
        )
        document.automaticstyles.addElement(table_row_style)

        table_text_style = style.Style(
            name="TableText",
            family="paragraph",
        )
        table_text_style.addElement(
            TextProperties(
                fontsize="8pt",
            )
        )
        table_text_style.addElement(
            ParagraphProperties(
                textalign="start",
            )
        )
        document.styles.addElement(table_text_style)

        table_center_text_style = style.Style(
            name="TableCenterText",
            family="paragraph",
        )
        table_center_text_style.addElement(
            TextProperties(
                fontsize="8pt",
            )
        )
        table_center_text_style.addElement(
            ParagraphProperties(
                textalign="center",
            )
        )
        document.styles.addElement(table_center_text_style)

        table_header_style = style.Style(
            name="TableHeaderText",
            family="paragraph",
        )
        table_header_style.addElement(
            TextProperties(
                fontsize="8pt",
                fontweight="bold",
            )
        )
        table_header_style.addElement(
            ParagraphProperties(
                textalign="center",
            )
        )
        document.styles.addElement(table_header_style)

        table_scientific_column_style = style.Style(
            name="TableScientificColumn",
            family="table-column",
        )
        table_scientific_column_style.addElement(
            TableColumnProperties(
                columnwidth="5.0cm",
            )
        )
        document.automaticstyles.addElement(table_scientific_column_style)

        table_czech_column_style = style.Style(
            name="TableCzechColumn",
            family="table-column",
        )
        table_czech_column_style.addElement(
            TableColumnProperties(
                columnwidth="4.0cm",
            )
        )
        document.automaticstyles.addElement(table_czech_column_style)

        table_value_column_style = style.Style(
            name="TableValueColumn",
            family="table-column",
        )
        table_value_column_style.addElement(
            TableColumnProperties(
                columnwidth="0.8cm",
            )
        )
        document.automaticstyles.addElement(table_value_column_style)

        protection_table_text_style = style.Style(
            name="ProtectionTableText",
            family="paragraph",
        )
        protection_table_text_style.addElement(
            TextProperties(
                fontsize="7.5pt",
            )
        )
        protection_table_text_style.addElement(
            ParagraphProperties(
                textalign="start",
            )
        )
        document.styles.addElement(protection_table_text_style)

        protection_table_center_text_style = style.Style(
            name="ProtectionTableCenterText",
            family="paragraph",
        )
        protection_table_center_text_style.addElement(
            TextProperties(
                fontsize="7.5pt",
            )
        )
        protection_table_center_text_style.addElement(
            ParagraphProperties(
                textalign="center",
            )
        )
        document.styles.addElement(protection_table_center_text_style)

        protection_table_header_style = style.Style(
            name="ProtectionTableHeaderText",
            family="paragraph",
        )
        protection_table_header_style.addElement(
            TextProperties(
                fontsize="7.5pt",
                fontweight="bold",
            )
        )
        protection_table_header_style.addElement(
            ParagraphProperties(
                textalign="center",
            )
        )
        document.styles.addElement(protection_table_header_style)

        protection_scientific_column_style = style.Style(
            name="ProtectionScientificColumn",
            family="table-column",
        )
        protection_scientific_column_style.addElement(
            TableColumnProperties(
                columnwidth="4.4cm",
            )
        )
        document.automaticstyles.addElement(protection_scientific_column_style)

        protection_czech_column_style = style.Style(
            name="ProtectionCzechColumn",
            family="table-column",
        )
        protection_czech_column_style.addElement(
            TableColumnProperties(
                columnwidth="3.0cm",
            )
        )
        document.automaticstyles.addElement(protection_czech_column_style)

        protection_red_list_column_style = style.Style(
            name="ProtectionRedListColumn",
            family="table-column",
        )
        protection_red_list_column_style.addElement(
            TableColumnProperties(
                columnwidth="1.5cm",
            )
        )
        document.automaticstyles.addElement(protection_red_list_column_style)

        protection_legal_column_style = style.Style(
            name="ProtectionLegalColumn",
            family="table-column",
        )
        protection_legal_column_style.addElement(
            TableColumnProperties(
                columnwidth="1.5cm",
            )
        )
        document.automaticstyles.addElement(protection_legal_column_style)

        protection_origin_column_style = style.Style(
            name="ProtectionOriginColumn",
            family="table-column",
        )
        protection_origin_column_style.addElement(
            TableColumnProperties(
                columnwidth="2.2cm",
            )
        )
        document.automaticstyles.addElement(protection_origin_column_style)

        protection_invasive_column_style = style.Style(
            name="ProtectionInvasiveColumn",
            family="table-column",
        )
        protection_invasive_column_style.addElement(
            TableColumnProperties(
                columnwidth="2.2cm",
            )
        )
        document.automaticstyles.addElement(protection_invasive_column_style)

    def append_heading(self, document, title, level=1):
        level = max(
            1,
            min(
                int(level),
                6,
            ),
        )

        heading = text.H(
            outlinelevel=level,
            stylename=f"Heading {level}",
        )
        heading.addText(title)
        document.text.addElement(heading)

    def append_inline_markdown_to_paragraph(self, paragraph, value):
        if not value:
            return

        pattern = re.compile(
            r"(\*\*\*[^*]+?\*\*\*|\*\*[^*]+?\*\*|\*[^*]+?\*)"
        )

        position = 0

        for match in pattern.finditer(value):
            if match.start() > position:
                paragraph.addText(
                    value[position:match.start()]
                )

            token = match.group(0)

            if token.startswith("***") and token.endswith("***"):
                span = text.Span(
                    stylename="BoldItalicText",
                )
                span.addText(token[3:-3])
                paragraph.addElement(span)

            elif token.startswith("**") and token.endswith("**"):
                span = text.Span(
                    stylename="BoldText",
                )
                span.addText(token[2:-2])
                paragraph.addElement(span)

            elif token.startswith("*") and token.endswith("*"):
                span = text.Span(
                    stylename="ItalicText",
                )
                span.addText(token[1:-1])
                paragraph.addElement(span)

            position = match.end()

        if position < len(value):
            paragraph.addText(
                value[position:]
            )

    def append_markdown_paragraph(self, document, value):
        paragraph = text.P(
            stylename=self.body_text_style_name,
        )
        self.append_inline_markdown_to_paragraph(
            paragraph,
            value,
        )
        document.text.addElement(paragraph)

    def append_bullet_paragraph(self, document, value):
        paragraph = text.P(
            stylename=self.body_text_style_name,
        )
        paragraph.addText("• ")
        self.append_inline_markdown_to_paragraph(
            paragraph,
            value,
        )
        document.text.addElement(paragraph)

    def append_numbered_paragraph(self, document, number, value):
        paragraph = text.P(
            stylename=self.body_text_style_name,
        )
        paragraph.addText(f"{number}. ")
        self.append_inline_markdown_to_paragraph(
            paragraph,
            value,
        )
        document.text.addElement(paragraph)

    def append_markdown_block(self, document, value):
        cleaned_text = self.clean_generated_text(value)

        if not cleaned_text:
            return

        for line in cleaned_text.splitlines():
            line = line.strip()

            if not line:
                continue

            heading_match = re.match(
                r"^(#{1,6})\s+(.+)$",
                line,
            )

            if heading_match:
                self.append_heading(
                    document,
                    heading_match.group(2).strip(),
                    level=len(heading_match.group(1)),
                )
                continue

            bullet_match = re.match(
                r"^[-*]\s+(.+)$",
                line,
            )

            if bullet_match:
                self.append_bullet_paragraph(
                    document,
                    bullet_match.group(1).strip(),
                )
                continue

            numbered_match = re.match(
                r"^(\d+)\.\s+(.+)$",
                line,
            )

            if numbered_match:
                self.append_numbered_paragraph(
                    document,
                    numbered_match.group(1),
                    numbered_match.group(2).strip(),
                )
                continue

            self.append_markdown_paragraph(
                document,
                line,
            )

    def append_section(self, document, title, value):
        cleaned_text = self.clean_generated_text(value)

        if not cleaned_text:
            return

        self.append_heading(
            document,
            title,
            level=2,
        )
        self.append_markdown_block(
            document,
            cleaned_text,
        )

    def add_scientific_name(self, paragraph, scientific_name):
        words = scientific_name.split(" ")

        for index, word in enumerate(words):
            if index > 0:
                paragraph.addText(" ")

            if word in ("agg.", "sect."):
                paragraph.addText(word)
            else:
                paragraph.addElement(
                    text.Span(
                        stylename="ItalicText",
                        text=word,
                    )
                )

    def add_header_cell(self, row, value):
        cell = TableCell(
            stylename="TableCell",
        )
        paragraph = text.P(
            stylename="TableHeaderText",
        )
        paragraph.addText(str(value))
        cell.addElement(paragraph)
        row.addElement(cell)

    def add_text_cell(self, row, value, centered=False):
        cell = TableCell(
            stylename="TableCell",
        )
        paragraph = text.P(
            stylename="TableCenterText" if centered else "TableText",
        )
        paragraph.addText(str(value) if value is not None else "")
        cell.addElement(paragraph)
        row.addElement(cell)

    def add_bold_text_cell(self, row, value, centered=True):
        cell = TableCell(
            stylename="TableCell",
        )
        paragraph = text.P(
            stylename="TableHeaderText" if centered else "TableText",
        )
        paragraph.addText(str(value) if value is not None else "")
        cell.addElement(paragraph)
        row.addElement(cell)

    def add_spanned_bold_text_cell(self, row, value, columns):
        cell = TableCell(
            stylename="TableCell",
            numbercolumnsspanned=columns,
        )
        paragraph = text.P(
            stylename="TableHeaderText",
        )
        paragraph.addText(str(value) if value is not None else "")
        cell.addElement(paragraph)
        row.addElement(cell)

        for _ in range(columns - 1):
            row.addElement(
                CoveredTableCell()
            )

    def add_protection_header_cell(self, row, value):
        cell = TableCell(
            stylename="TableCell",
        )
        paragraph = text.P(
            stylename="ProtectionTableHeaderText",
        )
        paragraph.addText(str(value))
        cell.addElement(paragraph)
        row.addElement(cell)

    def add_protection_text_cell(self, row, value, centered=False):
        cell = TableCell(
            stylename="TableCell",
        )
        paragraph = text.P(
            stylename=(
                "ProtectionTableCenterText"
                if centered
                else "ProtectionTableText"
            ),
        )
        paragraph.addText(str(value) if value is not None else "")
        cell.addElement(paragraph)
        row.addElement(cell)

    def get_ellenberg_value(self, taxon, field_name):
        if taxon.ellenberg_indicator_values is None:
            return None

        return getattr(
            taxon.ellenberg_indicator_values,
            field_name,
        )

    def get_czech_red_list_code(self, taxon):
        if taxon.czech_red_list is None:
            return "-"

        return taxon.czech_red_list.code or "-"

    def get_czech_legal_protection(self, taxon):
        if taxon.czech_legal_protection is None:
            return "-"

        return taxon.czech_legal_protection.paragraph or "-"

    def get_czech_taxon_origin(self, taxon):
        if taxon.czech_taxon_origin is None:
            return ""

        return taxon.czech_taxon_origin.origin or ""

    def get_invasive_status(self, taxon):
        if taxon.invasive_status is None:
            return ""

        return taxon.invasive_status.status or ""

    def format_average(self, values):
        if not values:
            return ""

        average = sum(values) / len(values)

        return f"{average:.2f}"

    def get_locality_taxa(self, locality):
        taxa = Taxon.objects.filter(
            locality_visits__locality=locality,
        ).select_related(
            "authorship",
            "taxonomic_rank",
            "ellenberg_indicator_values",
            "czech_red_list",
            "czech_legal_protection",
            "czech_taxon_origin",
            "invasive_status",
        ).distinct()

        return sorted(
            taxa,
            key=lambda taxon: taxon.scientific_name.lower(),
        )

    def append_ellenberg_table(self, document, locality):
        taxa = self.get_locality_taxa(locality)

        if not taxa:
            return

        table = Table(
            name="Taxa Ellenberg",
        )

        table.addElement(
            TableColumn(
                stylename="TableScientificColumn",
            )
        )
        table.addElement(
            TableColumn(
                stylename="TableCzechColumn",
            )
        )

        for _ in range(6):
            table.addElement(
                TableColumn(
                    stylename="TableValueColumn",
                )
            )

        header_row = TableRow(
            stylename="TableRow",
        )
        self.add_header_cell(header_row, "Vědecké jméno")
        self.add_header_cell(header_row, "České jméno")
        self.add_header_cell(header_row, "L")
        self.add_header_cell(header_row, "T")
        self.add_header_cell(header_row, "M")
        self.add_header_cell(header_row, "R")
        self.add_header_cell(header_row, "N")
        self.add_header_cell(header_row, "S")
        table.addElement(header_row)

        light_values = []
        temperature_values = []
        moisture_values = []
        reaction_values = []
        nutrients_values = []
        salinity_values = []

        for taxon in taxa:
            row = TableRow(
                stylename="TableRow",
            )

            scientific_cell = TableCell(
                stylename="TableCell",
            )
            scientific_paragraph = text.P(
                stylename="TableText",
            )

            self.add_scientific_name(
                scientific_paragraph,
                taxon.scientific_name,
            )

            if taxon.authorship:
                scientific_paragraph.addText(
                    f", {taxon.authorship.text}"
                )

            scientific_cell.addElement(scientific_paragraph)
            row.addElement(scientific_cell)

            self.add_text_cell(
                row,
                taxon.name_cs,
            )

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

            self.add_text_cell(row, light, centered=True)
            self.add_text_cell(row, temperature, centered=True)
            self.add_text_cell(row, moisture, centered=True)
            self.add_text_cell(row, reaction, centered=True)
            self.add_text_cell(row, nutrients, centered=True)
            self.add_text_cell(row, salinity, centered=True)

            table.addElement(row)

        average_row = TableRow(
            stylename="TableRow",
        )

        self.add_spanned_bold_text_cell(
            average_row,
            "Průměr",
            2,
        )
        self.add_bold_text_cell(
            average_row,
            self.format_average(light_values),
        )
        self.add_bold_text_cell(
            average_row,
            self.format_average(temperature_values),
        )
        self.add_bold_text_cell(
            average_row,
            self.format_average(moisture_values),
        )
        self.add_bold_text_cell(
            average_row,
            self.format_average(reaction_values),
        )
        self.add_bold_text_cell(
            average_row,
            self.format_average(nutrients_values),
        )
        self.add_bold_text_cell(
            average_row,
            self.format_average(salinity_values),
        )

        table.addElement(average_row)

        document.text.addElement(table)

    def append_protection_table(self, document, locality):
        taxa = self.get_locality_taxa(locality)

        if not taxa:
            return

        table = Table(
            name="Taxa Protection",
        )

        table.addElement(
            TableColumn(
                stylename="ProtectionScientificColumn",
            )
        )
        table.addElement(
            TableColumn(
                stylename="ProtectionCzechColumn",
            )
        )
        table.addElement(
            TableColumn(
                stylename="ProtectionRedListColumn",
            )
        )
        table.addElement(
            TableColumn(
                stylename="ProtectionLegalColumn",
            )
        )
        table.addElement(
            TableColumn(
                stylename="ProtectionOriginColumn",
            )
        )
        table.addElement(
            TableColumn(
                stylename="ProtectionInvasiveColumn",
            )
        )

        header_row = TableRow(
            stylename="TableRow",
        )
        self.add_protection_header_cell(header_row, "Vědecké jméno")
        self.add_protection_header_cell(header_row, "České jméno")
        self.add_protection_header_cell(header_row, "Červený seznam")
        self.add_protection_header_cell(header_row, "Zákonná ochrana")
        self.add_protection_header_cell(header_row, "Původnost v ČR")
        self.add_protection_header_cell(header_row, "Invazní status")
        table.addElement(header_row)

        for taxon in taxa:
            row = TableRow(
                stylename="TableRow",
            )

            scientific_cell = TableCell(
                stylename="TableCell",
            )
            scientific_paragraph = text.P(
                stylename="ProtectionTableText",
            )

            self.add_scientific_name(
                scientific_paragraph,
                taxon.scientific_name,
            )

            if taxon.authorship:
                scientific_paragraph.addText(
                    f", {taxon.authorship.text}"
                )

            scientific_cell.addElement(scientific_paragraph)
            row.addElement(scientific_cell)

            self.add_protection_text_cell(
                row,
                taxon.name_cs,
            )
            self.add_protection_text_cell(
                row,
                self.get_czech_red_list_code(taxon),
                centered=True,
            )
            self.add_protection_text_cell(
                row,
                self.get_czech_legal_protection(taxon),
                centered=True,
            )
            self.add_protection_text_cell(
                row,
                self.get_czech_taxon_origin(taxon),
            )
            self.add_protection_text_cell(
                row,
                self.get_invasive_status(taxon),
            )

            table.addElement(row)

        document.text.addElement(table)

    def append_ecological_indicator_assessment_section(self, document, locality):
        has_text = bool(
            self.clean_generated_text(
                locality.ecological_indicator_assessment,
            )
        )
        has_taxa = bool(
            self.get_locality_taxa(locality)
        )

        if not has_text and not has_taxa:
            return

        self.append_heading(
            document,
            "Ekologické indikační hodnoty",
            level=2,
        )

        self.append_ellenberg_table(
            document,
            locality,
        )

        if has_text:
            self.append_markdown_block(
                document,
                locality.ecological_indicator_assessment,
            )

    def append_conservation_issues_section(self, document, locality):
        has_text = bool(
            self.clean_generated_text(
                locality.conservation_issues,
            )
        )
        has_taxa = bool(
            self.get_locality_taxa(locality)
        )

        if not has_text and not has_taxa:
            return

        self.append_heading(
            document,
            "Biologické a ochranářské aspekty",
            level=2,
        )

        self.append_protection_table(
            document,
            locality,
        )

        if has_text:
            self.append_markdown_block(
                document,
                locality.conservation_issues,
            )

    def create_odt_document(self, locality):
        document = OpenDocumentText()

        self.create_styles(document)

        self.append_heading(
            document,
            locality.name,
            level=1,
        )

        self.append_section(
            document,
            "Geografická charakteristika",
            locality.geographical_location_description,
        )

        self.append_ecological_indicator_assessment_section(
            document,
            locality,
        )

        self.append_conservation_issues_section(
            document,
            locality,
        )

        return document

    def handle(self, *args, **options):
        locality_id = options["locality_id"]

        locality = Locality.objects.filter(
            id=locality_id,
        ).select_related(
            "project",
        ).first()

        if locality is None:
            raise CommandError(
                f"Locality with ID {locality_id} does not exist."
            )

        output_path = self.get_output_path(
            locality,
            options["output"],
        )

        document = self.create_odt_document(locality)

        document.save(
            str(output_path),
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Created {output_path} for locality "
                f"{locality.id}: {locality.name}."
            )
        )