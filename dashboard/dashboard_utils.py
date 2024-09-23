from useroperations.models import MbUser
from datetime import datetime
from collections import defaultdict
import time

def convert_to_datetime(date):
    if isinstance(date, str):
        try:
            # Try parsing with date and time
            date_obj = datetime.strptime(date, '%Y-%m-%d %H:%M:%S.%f')
        except ValueError:
            # Fallback to date only
            date_obj = datetime.strptime(date, '%Y-%m-%d')
    elif isinstance(date, datetime):
        date_obj = date
    else:
        raise TypeError("Date must be a string or datetime object")
    
    return date_obj

def get_data_counts(model, timestamp_field, start_date, end_date, dropdown_value, fetch_deleted_data_func=None):
    start_date_obj = convert_to_datetime(start_date)
    end_date_obj = convert_to_datetime(end_date)
    
    if model == MbUser:
        users_before_start_date_count = model.objects.filter(**{f"{timestamp_field}__lt": start_date_obj}).count()
        data_all = model.objects.filter(**{f"{timestamp_field}__range": [start_date_obj, end_date_obj]})
    else:
        start_date_unix = int(time.mktime(start_date_obj.timetuple()))
        end_date_unix = int(time.mktime(end_date_obj.timetuple()))
        
        users_before_start_date_count = model.objects.filter(**{f"{timestamp_field}__lt": start_date_unix}).count()
        data_all = model.objects.filter(**{f"{timestamp_field}__range": [start_date_unix, end_date_unix]})
    
    data_counts = defaultdict(int)

    for data in data_all:
        if model == MbUser:
            data_datetime = getattr(data, timestamp_field)
        else:
            data_datetime = datetime.fromtimestamp(getattr(data, timestamp_field))
        
        time_period = get_time_period(data_datetime, dropdown_value)
        data_counts[time_period] += 1
    
    sorted_periods = sorted(data_counts.keys())
    sorted_counts = [data_counts[period] for period in sorted_periods]

    # Calculate cumulative counts
    cumulative_counts_data = []
    cumulative_sum_data = users_before_start_date_count
    for count in sorted_counts:
        cumulative_sum_data += count
        cumulative_counts_data.append(cumulative_sum_data)

    # Handle deletions if a fetch_deleted_data_func is provided
    sorted_deleted_counts = []
    if fetch_deleted_data_func:
        deleted_dates, deleted_counts = fetch_deleted_data_func()
        deleted_data_counts = defaultdict(int)

        for date, count in zip(deleted_dates, deleted_counts):
            time_period = get_time_period(date, dropdown_value)
            deleted_data_counts[time_period] += count
        all_time_periods = set(sorted_periods).union(set(deleted_data_counts.keys()))
        sorted_periods = sorted(all_time_periods)
        sorted_deleted_counts = [-deleted_data_counts[period] for period in sorted_periods]  # Make deleted counts negative

    return sorted_periods, sorted_counts, cumulative_counts_data, sorted_deleted_counts


def get_time_period(date, dropdown_value):
    if dropdown_value == 'daily':
        return date.strftime('%Y-%m-%d')
    elif dropdown_value == 'weekly':
        return f"{date.isocalendar()[0]}-W{date.isocalendar()[1]:02d}"
    elif dropdown_value in ['biyearly', '6months']:
        if date.month <= 6:
            return f"{date.year}-H1"
        else:
            return f"{date.year}-H2"
    elif dropdown_value == 'yearly':
        return date.strftime('%Y')
    else:  # default to monthly
        return date.strftime('%Y-%m')
    
