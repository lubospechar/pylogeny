import csv
from io import BytesIO, StringIO

from decouple import config
from django.core.management.base import BaseCommand, CommandError
from openai import OpenAI, OpenAIError

from florapy.models import Locality
from pylogenyapp.models import Taxon


class Command(BaseCommand):
    help = "Generate conservation issues assessment using the OpenAI API."

    def add_arguments(self, parser):
        parser.add_argument(
            "locality_id",
            type=int,
            help="ID of locality.",
        )

    def get_czech_red_list_code(self, taxon):
        if taxon.czech_red_list is None:
            return ""

        return taxon.czech_red_list.code or ""

    def get_czech_legal_protection(self, taxon):
        if taxon.czech_legal_protection is None:
            return ""

        return taxon.czech_legal_protection.paragraph or ""

    def get_czech_taxon_origin(self, taxon):
        if taxon.czech_taxon_origin is None:
            return ""

        return taxon.czech_taxon_origin.origin or ""

    def get_invasive_status(self, taxon):
        if taxon.invasive_status is None:
            return ""

        return taxon.invasive_status.status or ""

    def create_taxa_protection_csv(self, locality_id):
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
                "Červený seznam",
                "Zákonná ochrana",
                "Původnost v ČR",
                "Invazní status",
            ]
        )

        for taxon in taxa:
            writer.writerow(
                [
                    taxon.scientific_name,
                    taxon.name_cs,
                    self.get_czech_red_list_code(taxon),
                    self.get_czech_legal_protection(taxon),
                    self.get_czech_taxon_origin(taxon),
                    self.get_invasive_status(taxon),
                ]
            )

        return csv_file.getvalue()

    def create_csv_file_for_openai(self, taxa_protection_csv):
        csv_bytes = taxa_protection_csv.encode("utf-8")
        csv_file = BytesIO(csv_bytes)
        csv_file.name = "taxa_protection.csv"

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

        taxa_protection_csv = self.create_taxa_protection_csv(locality_id)
        csv_file = self.create_csv_file_for_openai(taxa_protection_csv)

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
                    "Na základě přiloženého CSV souboru s údaji o ochranářsky "
                    "významných vlastnostech taxonů zhodnoť ochranářské aspekty lokality. "
                    "Zaměř se zejména na druhy uvedené v červeném seznamu, "
                    "zákonem chráněné druhy, původnost taxonů v ČR a invazní status. "
                    "Nevymýšlej si nepodložené informace. "
                    "Pokud v datech nejsou žádné ohrožené, chráněné nebo invazní taxony, "
                    "uveď to věcně a stručně. "
                    "Nedělej nadpis. "
                    "Používej Markdown. "
                    "Používej české názvy taxonů a za nimi v závorce kurzívou vědecké názvy taxonů."
                    "Nemluv o dodaném souboru. "
                    "Nemluv o ochranářských aspektech, čistě biologický text."
                    "Nemluv bězných druzích. "
                    "Nemluv o managementu. "
                    "Neuváděj věty druhem. "
                    "Nepůvodní a neinvazní nezmiňuj. "
                    "Nedělej odrážky ale odstavce "
                    "Nepopisuj rozpory mezi invazí, respektive neofyt či archeofyt a červeným seznamem. Napřiklad: U žádného z těchto invazních taxonů není uvedena kategorie červeného seznamu ani zákonná ochrana. - toto ne."

                ),
                input=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": (
                                    f"Název lokality: {locality.name}\n\n"
                                    "Zhodnoť ochranářské aspekty lokality "
                                    "podle přiloženého CSV souboru s taxony, "
                                    "jejich kategoriemi červeného seznamu, "
                                    "zákonnou ochranou, původností v ČR "
                                    "a invazním statusem."
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

        locality.conservation_issues = (
            f"GENEROVÁNO AI: {response.output_text}"
        )
        locality.save()

        self.stdout.write(
            self.style.SUCCESS(
                f"Conservation issues assessment was generated and saved "
                f"for locality {locality.id}: {locality.name}."
            )
        )
        self.stdout.write("")
        self.stdout.write(f"Uploaded CSV file ID: {uploaded_file.id}")
        self.stdout.write("")