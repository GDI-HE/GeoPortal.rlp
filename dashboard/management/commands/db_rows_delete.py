
from django.core.management.base import BaseCommand
from dashboard.models import WMC

class Command(BaseCommand):
    help = 'Delete the last 6 rows from the database'

    def handle(self, *args, **kwargs):
        # Query the last 6 rows in reverse order
        rows_to_delete = WMC.objects.all().order_by('-id')[:10]

        # Loop through the selected rows and delete them
        for row in rows_to_delete:
            row.delete()

        self.stdout.write(self.style.SUCCESS(f'Successfully deleted {len(rows_to_delete)} rows.'))
