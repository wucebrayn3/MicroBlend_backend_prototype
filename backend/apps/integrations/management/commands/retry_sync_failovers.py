from django.core.management.base import BaseCommand

from apps.integrations.services import retry_due_sync_events


class Command(BaseCommand):
    help = "Moves due retry-scheduled sync events back to pending for failover delivery attempts."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=200, help="Max number of due events to process.")

    def handle(self, *args, **options):
        limit = int(options["limit"])
        retried = retry_due_sync_events(limit=limit)
        self.stdout.write(self.style.SUCCESS(f"Retry queue processed. retried_events={retried}"))
