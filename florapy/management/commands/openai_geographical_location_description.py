from decouple import config
from django.core.management.base import BaseCommand, CommandError
from openai import OpenAI, OpenAIError

from florapy.models import Locality


class Command(BaseCommand):
    help = "Generate geographical location description using the OpenAI API."

    def add_arguments(self, parser):
        parser.add_argument(
            "locality_id",
            type=int,
            help="ID of locality.",
        )

    def handle(self, *args, **options):
        client = OpenAI(
            api_key=config("OPENAI_KEY"),
        )

        locality_id = options["locality_id"]

        try:
            locality = Locality.objects.get(id=locality_id)
        except Locality.DoesNotExist as error:
            raise CommandError(
                f"Locality with ID {locality_id} does not exist."
            ) from error

        direction = locality.direction_centroid_from_reference_point()

        instructions = (
            "Odpovídej odbornou a srozumitelnou češtinou.",
            "Nevymýšlej si nepodložené informace.",
            "Napiš základní geografický popis lokality.",
            "Používej MarkDown",
            f"Název lokality: {locality.name}.",
            f"Charakter zaměřené lokality: {locality.polygon_description or 'neuvedeno'}.",
            f"Plocha lokality: {locality.formatted_polygon_area() or 'neuvedeno'}.",
            f"Vzdálenost od referenčního bodu: cca {locality.formatted_distance_centroid_to_reference_point() or 'neuvedeno'}.",
            f"Popis referenčního bodu: {locality.reference_point_description or 'neuvedeno'}.",
            f"Směr plochy od referenčního bodu: {direction['label'] if direction else 'neuvedeno'}.",
            "Příklad 1: Lokalita **Srnčí rybník** o rozloze přibližně 0,8 ha se nachází asi 1,2 km jihovýchodně od centra Říčan u Prahy.",
            "Příklad 2: Lokalita **Milešovský potok** se nachází přibližně **1,7 km severozápadně od obecního úřadu v Malých Žernosekách**. Jedná se o území o ploše přibližně **10,7 ha**",
        )

        try:
            response = client.responses.create(
                model=config(
                    "OPENAI_MODEL",
                    default="gpt-5.6-sol",
                ),
                instructions=" ".join(instructions),
                input="Vytvoř geografický popis lokality podle zadaných údajů.",
            )
        except OpenAIError as error:
            raise CommandError(f"OpenAI API error: {error}") from error

        locality.geographical_location_description = f'GENEROVÁNO AI: {response.output_text}'
        locality.save()
        self.stdout.write(
            self.style.SUCCESS(
                f"Geographical location description was generated and saved "
                f"for locality {locality.id}: {locality.name}."
            )
        )