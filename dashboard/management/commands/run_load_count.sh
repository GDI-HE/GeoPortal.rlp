#!/bin/bash

# Navigate to the directory containing virtual environment
cd /data/env/

# Activate the virtual environment
source bin/activate

# Navigate to the directory containing your Python script
#cd /data2/geoportal_analytics/hessen_analytics/boris/management/commands

# Run your Python script
python /data/Geoportal.rlp/manage.py load_count 