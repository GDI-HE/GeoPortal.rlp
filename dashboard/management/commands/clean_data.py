from django.core.management.base import BaseCommand
import pandas as pd
from django.conf import settings
from pathlib import Path

class Command(BaseCommand):
    help = 'Clean and read a CSV file'

    def calculate_actual_load(self, df):
        # Initialize a variable to keep track of the previous day's load for each wmc_id
        previous_loads = {} 

        # Convert the 'date' column to datetime
        df['date'] = pd.to_datetime(df['date'])

        # Sort the DataFrame by 'date' in ascending order
        df.sort_values(by=['date'], inplace=True)

        # Remove duplicates based on 'wmc_id' and 'date'
        df.drop_duplicates(subset=['wmc_serial_id', 'date'], keep='first', inplace=True)

        # Iterate over rows in the DataFrame
        for index, row in df.iterrows():
            date = row['date']
            wmc_id = row['wmc_serial_id']
            load = row['load_count']

            # Check if the date is a Monday (weekday() == 0)
            if date.weekday() != 0:
                # Not a Monday, calculate actual load as the difference between
                # today's load and the previous day's load
                if wmc_id in previous_loads:
                    actual_load = load - previous_loads[wmc_id]
                    df.at[index, 'actual_load'] = int(actual_load)
                else:
                    df.at[index, 'actual_load'] = int(load)
            else:
                # On Mondays, the actual load is the same as the load count
                df.at[index, 'actual_load'] = int(load)

            # Update the previous load for the current wmc_id
            previous_loads[wmc_id] = load

        return df

    def handle(self, *args, **kwargs):
        # Define the path to your CSV file
        csv_file_path = Path(settings.BASE_DIR) / 'dashboard' / 'data' / 'loadcountdaily_wmc.csv'

        # Specify the expected encoding of your CSV file (e.g., UTF-8)
        expected_encoding = "utf-8"
        exception_count = 0

        # Create a new file to store the cleaned data
        cleaned_csv_file_path = Path(settings.BASE_DIR) / 'dashboard' / 'data' / 'cleaned_loadcountdaily_wmc.csv'

        try:
            # Open the original CSV file for reading
            with open(csv_file_path, mode='r', encoding=expected_encoding) as infile:
                # Open the cleaned CSV file for writing
                with open(cleaned_csv_file_path, mode='w', encoding=expected_encoding) as outfile:
                    for line in infile:
                        # Remove '\,' from each line and write it to the cleaned CSV file
                        cleaned_line = line.replace(r'\,', '')
                        outfile.write(cleaned_line)

            # Read the cleaned CSV file using Pandas
            df = pd.read_csv(cleaned_csv_file_path, sep=',', encoding=expected_encoding)

            # Calculate the 'actual_load' column
            df = self.calculate_actual_load(df)

            # Save the cleaned DataFrame to a new CSV file
            df.to_csv(cleaned_csv_file_path, sep=',', encoding=expected_encoding, index=False, float_format='%0.0f')

        except Exception as e:
            self.stderr.write(f"Error: {e}")
            exception_count += 1