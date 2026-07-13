from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from florapy.models import Locality


class Command(BaseCommand):
    help = "Run all OpenAI generation commands for selected locality."

    def add_arguments(self, parser):
        parser.add_argument(
            "locality_id",
            type=int,
            help="ID of locality.",
        )

    def handle(self, *args, **options):
        locality_id = options["locality_id"]

        locality = Locality.objects.filter(
            id=locality_id,
        ).first()

        if locality is None:
            raise CommandError(
                f"Locality with ID {locality_id} does not exist."
            )

        commands = [
            (
                "openai_geographical_location_description",
                "geographical location description",
            ),
            (
                "openai_ecological_indicator_assessment",
                "ecological indicator assessment",
            ),
            (
                "openai_conservation_issues",
                "conservation issues",
            ),
        ]

        self.stdout.write(
            self.style.SUCCESS(
                f"Running all OpenAI commands for locality "
                f"{locality.id}: {locality.name}."
            )
        )
        self.stdout.write("")

        for index, command in enumerate(commands, start=1):
            command_name, description = command

            self.stdout.write(
                self.style.NOTICE(
                    f"{index}/{len(commands)} Running {description}..."
                )
            )

            call_command(
                command_name,
                locality_id,
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f"{index}/{len(commands)} Finished {description}."
                )
            )
            self.stdout.write("")

        self.stdout.write(
            self.style.SUCCESS(
                f"All OpenAI commands finished for locality "
                f"{locality.id}: {locality.name}."
            )
        )