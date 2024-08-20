import csv
import psycopg2
# to test
# Connection parameters
conn_params = {
	'dbname': 'mapbender',
	'user': 'postgres',
	'password': 'postgres',
	'host': 'localhost',
}

# Function to insert data into the database
def insert_data_from_csv(csv_file_path):
	# Connect to the PostgreSQL database
	conn = psycopg2.connect(**conn_params)
	cur = conn.cursor()

	# Get the current maximum value of sn
	cur.execute('SELECT COALESCE(MAX(sn), 0) FROM "mapbender"."session_data"')
	max_sn = cur.fetchone()[0]
	
	# Initialize the primary key counter
	sn_counter = max_sn + 1

	# Open the CSV file and remove null bytes
	with open(csv_file_path, 'r', newline='') as csvfile:
		csvreader = csv.reader((line.replace('\0', '') for line in csvfile), delimiter=';')
		
		# Iterate over each row in the CSV file
		for row in csvreader:
			date_str, time_str, number_of_user = row
			timestamp_create = f"{date_str} {time_str}"
			
			# Insert the data into the table with the primary key
			cur.execute("""
				INSERT INTO "mapbender"."session_data" (sn, timestamp_create, number_of_user)
				VALUES (%s, %s, %s)
			""", (sn_counter, timestamp_create, number_of_user))
			
			# Increment the primary key counter
			sn_counter += 1
	
	# Commit the transaction and close the connection
	conn.commit()
	cur.close()
	conn.close()

# Path to the CSV file
csv_file_path = 'session.log.csv'

# Insert data from the CSV file into the database
insert_data_from_csv(csv_file_path)