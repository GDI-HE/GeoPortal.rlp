from django.core.management.base import BaseCommand
from dashboard.models import WMC
from django.db import connection, transaction
import pandas as pd
import sys
import os
import django
import time

# Set the correct path to your Django settings
#sys.path.append('/data/GeoPortal.rlp')  # Add the base project directory to the Python path
sys.path.insert(0, '/data/GeoPortal.rlp')  # Ensure Python finds the project

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Geoportal.settings")  # Correct path to settings module
django.setup()

class Command(BaseCommand):
    help = 'Fetch and insert WMC data from the database and compute actual_load'

    def get_wmc_data_from_db(self):
        """
        Fetches WMC data from the database using a corrected SQL query.
        """
        query = """
        SELECT (CURRENT_DATE) AS current_date,  
               wmc_load_count.fkey_wmc_serial_id AS wmc_serial_id,
               mb_user_wmc.wmc_title, 
               mb_group.mb_group_name, 
               wmc_load_count.load_count 
        FROM wmc_load_count
        INNER JOIN mb_user_wmc 
            ON wmc_load_count.fkey_wmc_serial_id = mb_user_wmc.wmc_serial_id
        INNER JOIN mb_user_mb_group 
            ON mb_user_wmc.fkey_user_id = mb_user_mb_group.fkey_mb_user_id
        INNER JOIN mb_group 
            ON mb_user_mb_group.fkey_mb_group_id = mb_group.mb_group_id 
        WHERE NOT (mb_group.mb_group_name = 'Bereichsadmin' OR mb_user_mb_group.mb_user_mb_group_type = 1) 
        ORDER BY mb_group.mb_group_name ASC;
        """
        with connection.cursor() as cursor:
            cursor.execute(query)
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

        # Convert the rows to a DataFrame for easier handling
        df = pd.DataFrame(rows, columns=columns)
        return df
    def process_data(self, df):
        """
        Processes the raw data to calculate the 'actual_load' field.
        If the new load_count is less than or equal to the previous day's load_count, 
        set the load_count and actual_load to be the same.
        Otherwise, calculate the actual_load as the difference between the current and previous day's load_count.
        """
        # Convert 'current_date' to datetime and store as 'date'
        df['date'] = pd.to_datetime(df['current_date'])
        
        # Sort by wmc_serial_id and date to ensure records are processed chronologically
        df = df.sort_values(by=['wmc_serial_id', 'date'])
        
        # Preload previous load_count for each wmc_serial_id from the WMC table.
        previous_loads = {}
        wmc_ids = df['wmc_serial_id'].unique()
        for wmc_id in wmc_ids:
            last_record = WMC.objects.filter(wmc_id=wmc_id).order_by('-date').first()
            if last_record:
                previous_loads[wmc_id] = last_record.load_count

        # Initialize actual_load column in the new DataFrame.
        df['actual_load'] = 0

        for index, row in df.iterrows():
            wmc_id = row['wmc_serial_id']
            current_load = row['load_count']
            
            # Check if the new load_count is less than or equal to the previous day's load_count
            if wmc_id in previous_loads:
                previous_load = previous_loads[wmc_id]
                
                # If current load is less than or equal to the previous load, set actual_load = load_count
                if current_load < previous_load:
                    actual_load = current_load
                else:
                    # Else, calculate the difference (actual_load)
                    actual_load = current_load - previous_load
                
                # Update the 'actual_load' column
                df.at[index, 'actual_load'] = int(actual_load)
            else:
                # If no previous record, treat as baseline (actual_load = load_count)
                df.at[index, 'actual_load'] = int(current_load)
            
            # Update previous_loads with current value for any subsequent records in the same batch.
            previous_loads[wmc_id] = current_load

        return df

    def insert_new_wmc_data(self, df):
        """
        Inserts new WMC records into the database without updating existing ones.
        """
        batch_size = 1000  # Adjust batch size as needed
        wmc_list = []

        for _, row in df.iterrows():
            wmc_serial_id = row['wmc_serial_id']
            date = row['date']

            # Check if the record already exists
            if WMC.objects.filter(wmc_id=wmc_serial_id, date=date).exists():
                continue  # Skip insertion if the record already exists

            # Create a new WMC object (do not include `id` to let Django generate it)
            wmc = WMC(
                date=row['date'],
                wmc_id=row['wmc_serial_id'],
                wmc_title=row['wmc_title'],
                load_count=row['load_count'],
                mb_group_name=row['mb_group_name'],
                actual_load=row['actual_load'],
                wmc_public=False  # Default value for wmc_public
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
        """
        Inserts a batch of WMC records into the database.
        """
        try:
            with transaction.atomic():
                WMC.objects.bulk_create(wmc_list, ignore_conflicts=True)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error inserting records: {str(e)}"))

    def handle(self, *args, **options):
        """
        Main entry point for the command.
        """
        start_time = time.time()  # Start timer
        try:
            
            # Step 1: Retrieve new data from the database
            df = self.get_wmc_data_from_db()

            # Step 2: Process the data to compute actual_load using the previous baseline if available
            processed_df = self.process_data(df)

            # Step 3: Insert new data into the WMC model
            self.insert_new_wmc_data(processed_df)

            self.stdout.write(self.style.SUCCESS('Data successfully processed and inserted.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred: {str(e)}"))
        finally:
            end_time = time.time()  # End timer
            elapsed_time = end_time - start_time
            self.stdout.write(self.style.SUCCESS(f"Execution time: {elapsed_time:.2f} seconds"))
