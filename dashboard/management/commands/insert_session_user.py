# insert_session_data.py

import sys
import os
import django
from django.utils import timezone

# Set the correct path to your Django settings
sys.path.append('/data/GeoPortal.rlp')  # Add the base project directory to the Python path
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Geoportal.settings")  # Correct path to settings module (small "p")
django.setup()

from dashboard.models import SESSION_USER

from django.db import transaction

def insert_session_data(datetime, session_number):
    datetime_obj = timezone.datetime.strptime(datetime, "%Y%m%d %H:%M:%S")

    with transaction.atomic():
        session, created = SESSION_USER.objects.update_or_create(
            datetime=datetime_obj,
            defaults={"session_number": session_number}
        )

        if created:
            print(f"Inserted new session: {session}")
        else:
            print(f"Updated existing session: {session}")

if __name__ == "__main__":
    # The datetime (date + time) and session number come as command line arguments from the bash script
    datetime = sys.argv[1]  # datetime as "YYYYMMDD HH:MM:SS"
    session_number = sys.argv[2]  # session count

    # Call the function to insert the data into the database
    insert_session_data(datetime, session_number)
