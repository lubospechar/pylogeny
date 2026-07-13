from decouple import config
from django.core.management.base import BaseCommand, CommandError
from openai import OpenAI, OpenAIError


class Command(BaseCommand):
    help = "Test the OpenAI API."

    def add_arguments(self, parser):
        parser.add_argument(
            "prompt",
            nargs="?",
            default="Napiš jednou větou, proč jsou mokřady důležité.",
        )

    def handle(self, *args, **options):
        client = OpenAI(
            api_key=config("OPENAI_KEY"),
        )

        try:
            response = client.responses.create(
                model=config(
                    "OPENAI_MODEL",
                    default="gpt-5.6-luna",
                ),
                instructions=(
                    "Odpovídej odbornou a srozumitelnou češtinou. "
                    "Nevymýšlej si nepodložené informace."
                ),
                input=options["prompt"],
            )
        except OpenAIError as error:
            raise CommandError(f"OpenAI API error: {error}") from error

        self.stdout.write(response.output_text)