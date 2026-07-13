import csv
from io import BytesIO, StringIO

from decouple import config
from django.core.management.base import BaseCommand, CommandError
from openai import OpenAI, OpenAIError

from florapy.models import Locality
from pylogenyapp.models import Taxon


class Command(BaseCommand):
    help = "Generate ecological indicator assessment using the OpenAI API."

    def add_arguments(self, parser):
        parser.add_argument(
            "locality_id",
            type=int,
            help="ID of locality.",
        )

    def get_ellenberg_value(self, taxon, field_name):
        if taxon.ellenberg_indicator_values is None:
            return ""

        value = getattr(
            taxon.ellenberg_indicator_values,
            field_name,
        )

        return value if value is not None else ""

    def format_average(self, values):
        if not values:
            return ""

        average = sum(values) / len(values)

        return f"{average:.2f}"

    def create_ellenberg_csv(self, locality_id):
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

        csv_file = StringIO()
        writer = csv.writer(csv_file)

        writer.writerow(
            [
                "Vědecké jméno",
                "České jméno",
                "L",
                "T",
                "M",
                "R",
                "N",
                "S",
            ]
        )

        light_values = []
        temperature_values = []
        moisture_values = []
        reaction_values = []
        nutrients_values = []
        salinity_values = []

        for taxon in taxa:
            light = self.get_ellenberg_value(taxon, "light")
            temperature = self.get_ellenberg_value(taxon, "temperature")
            moisture = self.get_ellenberg_value(taxon, "moisture")
            reaction = self.get_ellenberg_value(taxon, "reaction")
            nutrients = self.get_ellenberg_value(taxon, "nutrients")
            salinity = self.get_ellenberg_value(taxon, "salinity")

            if light != "":
                light_values.append(light)
            if temperature != "":
                temperature_values.append(temperature)
            if moisture != "":
                moisture_values.append(moisture)
            if reaction != "":
                reaction_values.append(reaction)
            if nutrients != "":
                nutrients_values.append(nutrients)
            if salinity != "":
                salinity_values.append(salinity)

            writer.writerow(
                [
                    taxon.scientific_name,
                    taxon.name_cs,
                    light,
                    temperature,
                    moisture,
                    reaction,
                    nutrients,
                    salinity,
                ]
            )

        writer.writerow(
            [
                "Průměr",
                "",
                self.format_average(light_values),
                self.format_average(temperature_values),
                self.format_average(moisture_values),
                self.format_average(reaction_values),
                self.format_average(nutrients_values),
                self.format_average(salinity_values),
            ]
        )

        return csv_file.getvalue()

    def create_csv_file_for_openai(self, ellenberg_csv):
        csv_bytes = ellenberg_csv.encode("utf-8")
        csv_file = BytesIO(csv_bytes)
        csv_file.name = "ellenberg_indicator_values.csv"

        return csv_file

    def handle(self, *args, **options):
        locality_id = options["locality_id"]

        locality = Locality.objects.filter(
            id=locality_id,
        ).first()

        if locality is None:
            raise CommandError(
                f"Locality with ID {locality_id} does not exist."
            )

        ellenberg_csv = self.create_ellenberg_csv(locality_id)
        csv_file = self.create_csv_file_for_openai(ellenberg_csv)

        client = OpenAI(
            api_key=config("OPENAI_KEY"),
        )

        try:
            uploaded_file = client.files.create(
                file=csv_file,
                purpose="user_data",
            )

            response = client.responses.create(
                model=config(
                    "OPENAI_MODEL",
                    default="gpt-5.6-sol",
                ),
                instructions=(
                    "Odpovídej odbornou a srozumitelnou češtinou. "
                    "Na základě přiloženého CSV souboru s Ellenbergovými "
                    "indikačními hodnotami zhodnoť ekologické poměry lokality. "
                    "Zaměř se zejména na světelné, teplotní, vlhkostní, "
                    "půdní reakční, živinové a salinitní poměry. "
                    "Použij průměrné hodnoty z řádku Průměr jako hlavní "
                    "souhrnnou informaci. "
                    "Nevymýšlej si nepodložené informace. "
                    "Nepoužívej slovo čerstvé (v kontextu čerstvé až vlhké) "
                    "Nedělej nadpis "
                    "Používej MarkDown. "
                    "Používej české názvy taxonu a za nimi v závorce kurzívou věděcké názvy taxonů. "
                    "Nedělej odrážky ale odstavce "
                ),
                input=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": (
                                    f"Název lokality: {locality.name}\n\n"
                                    "Zhodnoť ekologické indikační hodnoty "
                                    "taxonů z této lokality podle přiloženého "
                                    "CSV souboru."
                                ),
                            },
                            {
                                "type": "input_file",
                                "file_id": uploaded_file.id,
                            },
                        ],
                    },
                ],
            )


        except OpenAIError as error:
            raise CommandError(f"OpenAI API error: {error}") from error

        locality.ecological_indicator_assessment = (
            f"GENEROVÁNO AI: {response.output_text}"
        )
        locality.save()

        self.stdout.write(
            self.style.SUCCESS(
                f"Ecological indicator assessment was generated and saved "
                f"for locality {locality.id}: {locality.name}."
            )
        )
        self.stdout.write("")
        self.stdout.write(f"Uploaded CSV file ID: {uploaded_file.id}")
        self.stdout.write("")