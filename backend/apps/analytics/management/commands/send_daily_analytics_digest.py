from datetime import date

from django.core.management.base import BaseCommand, CommandError

from apps.analytics.services import send_daily_digest_to_admins


class Command(BaseCommand):
    help = "Generates a daily analytics report and sends digest notifications to active admins."

    def add_arguments(self, parser):
        parser.add_argument(
            "--date",
            dest="target_date",
            help="Target date in YYYY-MM-DD format. Defaults to today in local timezone.",
        )

    def handle(self, *args, **options):
        target_date_raw = options.get("target_date")
        target_date = None
        if target_date_raw:
            try:
                target_date = date.fromisoformat(target_date_raw)
            except ValueError as exc:
                raise CommandError("Invalid --date format. Use YYYY-MM-DD.") from exc

        report, admin_count = send_daily_digest_to_admins(target_date=target_date)
        self.stdout.write(
            self.style.SUCCESS(
                f"Daily digest sent to {admin_count} admin(s). report_id={report.id} date={report.start_at.date()}"
            )
        )
