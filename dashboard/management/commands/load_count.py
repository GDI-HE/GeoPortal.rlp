import csv
from django.core.management.base import BaseCommand
from dashboard.models import WMC
from itertools import islice
from django.conf import settings
from pathlib import Path

class Command(BaseCommand):
    help = 'Load count data from loadcountdaily csv file'

    def handle(self, *args, **kwargs):
        # Truncate the table
        WMC.objects.all().delete()
        
        datafile = Path(settings.BASE_DIR) / 'dashboard' / 'data' / 'cleaned_loadcountdaily_wmc.csv'
        batch_size = 1000  # Adjust as needed

        with open(datafile, newline='') as csvfile:
            reader = csv.DictReader(islice(csvfile, 0, None))
            wmc_list = []

            for row in reader:
                wmc = WMC(
                    date=row['date'],
                    wmc_id=row['wmc_serial_id'],
                    wmc_title=row['wmc_title'],
                    load_count=row['load_count'],
                    wmc_public=row['wmc_public'],
                    mb_group_name=row['mb_group_name'],
                    actual_load=row['actual_load']
                )
                wmc_list.append(wmc)

                # Insert records in batches
                if len(wmc_list) >= batch_size:
                    self.insert_wmc_records(wmc_list)
                    wmc_list = []

            # Insert any remaining records
            if wmc_list:
                self.insert_wmc_records(wmc_list)

    def insert_wmc_records(self, wmc_list):
        try:
            WMC.objects.bulk_create(wmc_list)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error inserting records: {str(e)}"))