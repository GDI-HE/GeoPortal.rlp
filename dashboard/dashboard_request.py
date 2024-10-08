from useroperations.models import MbUser, Wms, Wfs, Wmc
from datetime import datetime, timedelta
from dashboard.dashboard_utils import get_data_counts
from useroperations.models import MbUserDeletion, WmsDeletion, WfsDeletion, WmcDeletion
from django.db.models.functions import TruncDay
from django.db.models import Count

def fetch_deleted_data(deletion_model):
    deletions = deletion_model.objects.annotate(day=TruncDay('deleted_at')).values('day').annotate(count=Count('id')).order_by('day')
    
    dates = [deletion['day'] for deletion in deletions]
    counts = [deletion['count'] for deletion in deletions]
    
    return dates, counts

def fetch_deleted_users_data():
    return fetch_deleted_data(MbUserDeletion)

def fetch_deleted_wms_data():
    return fetch_deleted_data(WmsDeletion)

def fetch_deleted_wfs_data():
    return fetch_deleted_data(WfsDeletion)

def fetch_deleted_wmc_data():
    return fetch_deleted_data(WmcDeletion)

def process_request(request):
    # Initialize start_date and end_date with default values
    start_date = datetime.now() - timedelta(days=365)
    end_date = datetime.now()

    # Check if start_date and end_date are provided in the request
    if request.is_ajax():
        if request.GET.get('start_date') and request.GET.get('end_date'):
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
            dropdown_value = request.GET.get('dropdown')
        else:
            dropdown_value = 'monthly'
    else:
        dropdown_value = 'monthly'

    start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)

    # Get WMS data counts
    sorted_months_wms, sorted_counts_wms, cumulative_counts_wms, sorted_deleted_counts_wms = get_data_counts(Wms, 'wms_timestamp_create', start_date, end_date, dropdown_value, fetch_deleted_wms_data)

    # Get WFS data counts
    sorted_months_wfs, sorted_counts_wfs, cumulative_counts_wfs, sorted_deleted_counts_wfs = get_data_counts(Wfs, 'wfs_timestamp_create', start_date, end_date, dropdown_value, fetch_deleted_wfs_data) 

    # Get WMC data counts
    sorted_months_wmc, sorted_counts_wmc, cumulative_counts_wmc, sorted_deleted_counts_wmc = get_data_counts(Wmc, 'wmc_timestamp', start_date, end_date, dropdown_value, fetch_deleted_wmc_data)

    # Get the registered user counts
    sorted_months, sorted_counts, cumulative_counts, _ = get_data_counts(MbUser, 'timestamp_create', start_date, end_date, dropdown_value)

    # Now you can use sorted_months_wms, sorted_counts_wms, cumulative_counts_wms, sorted_months_wfs, sorted_counts_wfs, and cumulative_counts_wfs as needed
    return sorted_months_wms, sorted_counts_wms, cumulative_counts_wms, sorted_months_wfs, sorted_counts_wfs, cumulative_counts_wfs, sorted_months_wmc, sorted_counts_wmc, cumulative_counts_wmc, sorted_months, sorted_counts, cumulative_counts, sorted_deleted_counts_wms, sorted_deleted_counts_wfs, sorted_deleted_counts_wmc