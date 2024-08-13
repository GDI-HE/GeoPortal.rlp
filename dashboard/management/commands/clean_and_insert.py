import csv
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from dashboard.models import SESSION_USER
from pathlib import Path
from django.db import connection

class Command(BaseCommand):
    help = 'Clean and insert data from session.log.csv into the database'

    def handle(self, *args, **kwargs):
        file_path = Path(settings.BASE_DIR) / 'dashboard' / 'data' / 'session.log.csv'
        batch_size = 1000  # Adjust the batch size as needed
        session_user_objects = []

        # Truncate the table
        with connection.cursor() as cursor:
            cursor.execute('TRUNCATE TABLE dashboard_session_user RESTART IDENTITY CASCADE')

        # Read the file and remove null characters
        with open(file_path, 'r') as file:
            content = file.read().replace('\0', '')

        # Use StringIO to simulate a file object for the cleaned content
        from io import StringIO
        cleaned_file = StringIO(content)

        with cleaned_file as file:
            reader = csv.reader(file, delimiter=';')
            for row in reader:
                date_str = row[0].strip()
                time_str = row[1].strip()
                session_number = int(row[2].strip())
                datetime_str = f"{date_str} {time_str}"
                datetime_obj = datetime.strptime(datetime_str, '%Y%m%d %H:%M:%S')
                
                session_user_objects.append(SESSION_USER(datetime=datetime_obj, session_number=session_number))
                
                if len(session_user_objects) >= batch_size:
                    SESSION_USER.objects.bulk_create(session_user_objects)
                    session_user_objects = []

        # Insert any remaining objects
        if session_user_objects:
            SESSION_USER.objects.bulk_create(session_user_objects)
        
        self.stdout.write(self.style.SUCCESS('Data successfully cleaned and inserted into the database'))