import psycopg2
from datetime import datetime, timedelta
import random

# Database connection parameters
conn_params = {
    'dbname': 'mapbender',
    'user': 'postgres',
    'password': 'postgres',
    'host': 'localhost',
}

# Function to generate a random timestamp between 2016 and 2024
def generate_random_timestamp(start_year=2014, end_year=2024):
    start_date = datetime(start_year, 1, 1)
    end_date = datetime(end_year, 12, 31)
    random_date = start_date + (end_date - start_date) * random.random()
    return int(random_date.timestamp())

# Function to update the wms_timestamp column with random timestamps
def update_wms_timestamps():
    try:
        # Connect to the database
        conn = psycopg2.connect(**conn_params)
        cur = conn.cursor()

        # Select all wms_ids from the wms table
        cur.execute("SELECT wms_id FROM mapbender.wms;")
        wms_ids = cur.fetchall()

        # Update each wms_id with a random timestamp
        for wms_id in wms_ids:
            random_timestamp = generate_random_timestamp()
            update_query = """
            UPDATE mapbender.wms
            SET wms_timestamp_create = %s
            WHERE wms_id = %s;
            """
            cur.execute(update_query, (random_timestamp, wms_id[0]))
            print(f"Updated wms_id {wms_id[0]} with timestamp {random_timestamp}")

        # Commit the transaction
        conn.commit()

        # Close the cursor and connection
        cur.close()
        conn.close()

        print("Successfully updated wms_timestamp for all rows.")

    except Exception as e:
        print(f"Failed to update wms_timestamp\nError: {e}")

# Main function
if __name__ == "__main__":
    update_wms_timestamps()