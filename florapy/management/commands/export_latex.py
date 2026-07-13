from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify
from pylatex import Document, NoEscape, Package, Section
from pylatex.utils import escape_latex

from florapy.models import Locality


class Command(BaseCommand):
    help = "Export locality data and texts to LaTeX document."

    def add_arguments(self, parser):
        parser.add_argument(
            "locality_id",
            type=int,
            help="ID of locality.",
        )
        parser.add_argument(
            "--output",
            default=None,
            help="Output TEX file. If omitted, filename is generated from locality name.",
        )

    def get_output_path_without_suffix(self, locality, output_path):
        if output_path:
            path = Path(output_path)
            if path.suffix == ".tex":
                return path.with_suffix("")
            return path

        locality_slug = slugify(locality.name)

        if not locality_slug:
            locality_slug = f"locality-{locality.id}"

        return Path(locality_slug)

    def clean_generated_text(self, text):
        if not text:
            return ""

        return text.replace(
            "GENEROVÁNO AI:",
            "",
        ).strip()

    def markdown_to_latex(self, text):
        if not text:
            return ""

        text = self.clean_generated_text(text)

        escaped_text = escape_latex(text)

        escaped_text = escaped_text.replace(
            r"\textasteriskcentered{}\textasteriskcentered{}",
            r"\textbf{",
        )

        lines = escaped_text.splitlines()
        converted_lines = []

        bold_open = False

        for line in lines:
            while r"\textbf{" in line:
                if bold_open:
                    line = line.replace(
                        r"\textbf{",
                        "}",
                        1,
                    )
                    bold_open = False
                else:
                    bold_open = True
                    break

            if bold_open and line.endswith(r"\textbf{"):
                converted_lines.append(line)
                continue

            converted_lines.append(line)

        converted_text = "\n\n".join(
            line for line in converted_lines if line.strip()
        )

        converted_text = converted_text.replace(
            r"\textbackslash{}",
            r"\textbackslash{}",
        )

        return converted_text

    def append_text_section(self, document, title, text):
        latex_text = self.markdown_to_latex(text)

        if not latex_text:
            return

        with document.create(
                Section(
                    title,
                    numbering=False,
                )
        ):
            document.append(
                NoEscape(latex_text)
            )

    def create_latex_document(self, locality):
        document = Document(
            documentclass="article",
            document_options=[
                "12pt",
                "a4paper",
            ],
        )

        document.packages.append(
            Package(
                "babel",
                options=[
                    "czech",
                ],
            )
        )

        document.packages.append(
            Package(
                "geometry",
                options=[
                    "margin=2.5cm",
                ],
            )
        )

        with document.create(
                Section(
                    escape_latex(locality.name),
                    numbering=False,
                )
        ):
            pass


        self.append_text_section(
            document,
            "Geografická poloha",
            locality.geographical_location_description,
        )

        self.append_text_section(
            document,
            "Ekologické indikační hodnoty",
            locality.ecological_indicator_assessment,
        )

        self.append_text_section(
            document,
            "Biologické a ochranářské aspekty",
            locality.conservation_issues,
        )

        return document

    def handle(self, *args, **options):
        locality_id = options["locality_id"]

        locality = Locality.objects.filter(
            id=locality_id,
        ).first()

        if locality is None:
            raise CommandError(
                f"Locality with ID {locality_id} does not exist."
            )

        output_path = self.get_output_path_without_suffix(
            locality,
            options["output"],
        )

        document = self.create_latex_document(locality)

        document.generate_tex(
            str(output_path),
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Created {output_path}.tex for locality "
                f"{locality.id}: {locality.name}."
            )
        )