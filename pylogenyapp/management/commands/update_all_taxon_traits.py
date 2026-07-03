from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Run all taxon trait update commands."

    UPDATE_COMMANDS = (
        "update_czech_red_list",
        "update_czech_legal_protection",
        "update_czech_taxon_origin",
        "update_invasive_status",
        "update_ellenberg_indicator_values",
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Only show what would be changed, without saving.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        for command_name in self.UPDATE_COMMANDS:
            self.stdout.write("")
            self.stdout.write(
                self.style.MIGRATE_HEADING(
                    f"Running {command_name}"
                )
            )

            call_command(
                command_name,
                dry_run=dry_run,
            )

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS("All taxon trait updates finished.")
        )