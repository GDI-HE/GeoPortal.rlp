from django.core.management.base import BaseCommand
import pandas as pd
from django.conf import settings
from pathlib import Path
from statsmodels.tsa.arima.model import ARIMA
import numpy as np

class Command(BaseCommand):
    help = 'Clean and read a CSV file'

    def calculate_actual_load(self, df):
        previous_loads = {} 
        df['date'] = pd.to_datetime(df['date'])
        df.sort_values(by=['date'], inplace=True)
        df.drop_duplicates(subset=['wmc_serial_id', 'date'], keep='first', inplace=True)

        start_problem_date = pd.to_datetime('2020-10-02')
        end_problem_date = pd.to_datetime('2020-11-09')
        problem_data = df[(df['date'] >= start_problem_date) & (df['date'] <= end_problem_date)]
        df = df[~((df['date'] >= start_problem_date) & (df['date'] <= end_problem_date))]

        for wmc_id in problem_data['wmc_serial_id'].unique():
            previous_month_data = df[(df['wmc_serial_id'] == wmc_id) & (df['date'] < start_problem_date)]
            previous_month_data = previous_month_data.tail(30)

            if len(previous_month_data) < 30:
                continue

            previous_month_data.set_index('date', inplace=True)
            model = ARIMA(previous_month_data['load_count'], order=(5, 1, 0))
            model_fit = model.fit()
            forecast = model_fit.forecast(steps=len(problem_data[problem_data['wmc_serial_id'] == wmc_id]))
            problem_data.loc[problem_data['wmc_serial_id'] == wmc_id, 'load_count'] = forecast.astype(int).values

        df = pd.concat([df, problem_data])
        df.sort_values(by=['date'], inplace=True)

        for index, row in df.iterrows():
            date = row['date']
            wmc_id = row['wmc_serial_id']
            load = row['load_count']

            if date < start_problem_date:
                if date.weekday() == 1:  # Tuesday
                    df.at[index, 'actual_load'] = int(load)
                else:
                    if wmc_id in previous_loads:
                        actual_load = load - previous_loads[wmc_id]
                        actual_load = max(actual_load, 0)
                        df.at[index, 'actual_load'] = int(actual_load)
                    else:
                        df.at[index, 'actual_load'] = int(load)
            else:
                if date.weekday() == 0:  # Monday
                    df.at[index, 'actual_load'] = int(load)
                else:
                    if wmc_id in previous_loads:
                        actual_load = load - previous_loads[wmc_id]
                        actual_load = max(actual_load, 0)
                        df.at[index, 'actual_load'] = int(actual_load)
                    else:
                        df.at[index, 'actual_load'] = int(load)

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