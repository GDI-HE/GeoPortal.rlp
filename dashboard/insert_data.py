import psycopg2
from datetime import datetime, timedelta
import random
import string

# Function to generate a random date between start_date and end_date
def random_date(start_date, end_date):
	delta = end_date - start_date
	random_days = random.randint(0, delta.days)
	return start_date + timedelta(days=random_days)

# Function to generate a random string of given length
def random_string(length):
	letters = string.ascii_letters
	return ''.join(random.choice(letters) for i in range(length))

# Function to generate a random email
def random_email():
	domains = ["example.com", "test.com", "sample.org"]
	return f"{random_string(5)}@{random.choice(domains)}"

# Database connection parameters
conn_params = {
	'dbname': 'mapbender',
	'user': 'postgres',
	'password': 'postgres',
	'host': 'localhost',
}

# Connect to the PostgreSQL database
conn = psycopg2.connect(**conn_params)
cur = conn.cursor()

# Define the date range
start_date = datetime(2018, 12, 1)
end_date = datetime(2020, 3, 1)

# Insert 100 new entries
for _ in range(500):
	timestamp_create = random_date(start_date, end_date)
	name = random_string(10)
	email = random_email()
	other_column_value = random.randint(1, 100)  # Replace with actual logic for other columns

	# Generate a unique user_id greater than 100
	while True:
		user_id = random.randint(101, 1900)
		cur.execute("SELECT COUNT(*) FROM \"mapbender\".\"mb_user\" WHERE mb_user_id = %s", (user_id,))
		if cur.fetchone()[0] == 0:
			break

	# Insert the data into the table
	cur.execute("""
		INSERT INTO "mapbender"."mb_user" (mb_user_id, mb_user_name, mb_user_email, timestamp_create)
		VALUES (%s, %s, %s, %s)
	""", (user_id, name, email, timestamp_create))

# Commit the transaction and close the connection
conn.commit()
cur.close()
conn.close()