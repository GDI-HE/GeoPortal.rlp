from useroperations.models import MbUser, Wms, Wfs, Wmc
import plotly.graph_objs as go
from datetime import datetime
from collections import defaultdict
import datetime as tm
import csv
from .forms import UploadFileForm
import os
from django.utils.timezone import make_aware
import pytz
import json
import time
from django.http import JsonResponse
from dashboard.dashboard_utils import convert_to_datetime

def upload_file(request):
    reporting_date_list = []
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            reporting_date_list = read_reporting_dates_from_csv(file)
            # Ensure reporting_date_list contains datetime objects
            if all(isinstance(date, datetime) for date in reporting_date_list):
                # Convert naive datetime objects to timezone-aware datetime objects
                reporting_date_list = [make_aware(date, timezone=pytz.UTC) for date in reporting_date_list]
            #content_type = request.POST.get('contentType')
            if request.is_ajax() and reporting_date_list:
                return JsonResponse({'reporting_date_list': reporting_date_list})
        else:
            return JsonResponse({'error': 'Invalid form data.'})
    else:
        form = UploadFileForm()

    # Render the dashboard.html with the reporting_date_list
    #return render(request, 'dashboard.html', {'form': form, 'reporting_date_list': reporting_date_list})
    return reporting_date_list

def read_reporting_dates_from_csv(file):
    reporting_date_list = []
    csv_data = []
    csv_reader = csv.DictReader(file.read().decode('utf-8').splitlines())
    try:
        for row in csv_reader:
            date = tm.datetime.strptime(row['reporting_date'], '%Y-%m-%d')
            reporting_date_list.append(date)
            csv_data.append(row)
        return reporting_date_list, csv_data
    except KeyError:
        return JsonResponse({'error': 'reporting_date column not found in the CSV file.'})
    
def generate_report(request, start_date_report, end_date_report, model, title, yaxis_title, image_filename):
    start_date_obj = convert_to_datetime(start_date_report)
    end_date_obj = convert_to_datetime(end_date_report)
    reporting_date_list =[] 

    if model == MbUser:
        timestamp_field = 'timestamp_create'
        #users_before_start_date_count = model.objects.filter(**{f"{timestamp_field}__lt": start_date_obj}).count()
        items_report = model.objects.filter(**{f"{timestamp_field}__range": [start_date_obj, end_date_obj]})
    else:
        # Determine the correct timestamp field for the model
        if model == Wms:
            timestamp_field = 'wms_timestamp_create'
        elif model == Wfs:
            timestamp_field = 'wfs_timestamp_create'
        elif model == Wmc:
            timestamp_field = 'wmc_timestamp'
        # Add other models and their timestamp fields as needed
        else:
            raise ValueError("Unsupported model type")

        # Convert datetime objects to Unix timestamps
        start_date_unix = int(time.mktime(start_date_obj.timetuple()))
        end_date_unix = int(time.mktime(end_date_obj.timetuple()))

        #users_before_start_date_count = model.objects.filter(**{f"{timestamp_field}__lt": start_date_unix}).count()
        items_report = model.objects.filter(**{f"{timestamp_field}__range": [start_date_unix, end_date_unix]})

    # Process data_all as needed
    reporting_date_list = upload_file(request)
    
    #reporting_date_list = upload_file(request)
    if isinstance(reporting_date_list, JsonResponse):
        reporting_date_list = json.loads(reporting_date_list.content)
        reporting_date_list = reporting_date_list.get('reporting_date_list', [])
    
    if reporting_date_list:
        reporting_date_list = list(reporting_date_list[1])
        reporting_date_list = [d['reporting_date'] for d in reporting_date_list]
        reporting_date_list = [tm.datetime.strptime(date, '%Y-%m-%d') for date in reporting_date_list]
    else:
        default_dates = ['2014-03-01', '2014-07-01', '2015-07-01', '2015-03-01', '2016-02-01', '2016-12-01', '2017-01-01', '2017-06-01', '2018-01-01', '2018-06-01', '2019-01-01', '2019-06-01', '2020-01-01', '2020-06-01', '2021-01-01', '2021-06-01', '2022-01-01', '2022-06-01', '2023-01-01', '2023-06-01', '2024-01-01', '2024-06-01', '2025-01-01', '2025-06-01', '2026-01-01', '2029-12-01']
        reporting_date_list = [tm.datetime.strptime(date, '%Y-%m-%d') for date in default_dates]
    
    reporting_date_list = sorted(reporting_date_list)
    item_creation_counts = defaultdict(int)
    
    if model == MbUser:
        timestamp_field = 'timestamp_create'
    elif model == Wms:
        timestamp_field = 'wms_timestamp_create'
    elif model == Wfs:
        timestamp_field = 'wfs_timestamp_create'
    first_start_date = reporting_date_list[0]
    # Convert first_start_date to Unix timestamp if the model is not MbUser
    if model != MbUser:
        first_start_date_unix = int(time.mktime(first_start_date.timetuple()))
    else:
        first_start_date_unix = first_start_date

    count = 0
    for item in items_report:
        item_timestamp = getattr(item, timestamp_field)
        if model != MbUser:
            if item_timestamp < first_start_date_unix:
                count += 1
        else:
            if item_timestamp < first_start_date:
                count += 1
    item_creation_counts[first_start_date] = count
    
    for i in range(len(reporting_date_list) - 1):
        start_date = reporting_date_list[i]
        end_date = reporting_date_list[i+1]
        count = 0
    
        # Convert start_date and end_date to Unix timestamps if the model is not MbUser
        if model != MbUser:
            start_date_unix = int(time.mktime(start_date.timetuple()))
            end_date_unix = int(time.mktime(end_date.timetuple()))
        else:
            start_date_unix = start_date
            end_date_unix = end_date
    
        for item in items_report:
            item_timestamp = getattr(item, timestamp_field)
            if model != MbUser:
                if start_date_unix <= item_timestamp < end_date_unix:
                    count += 1
            else:
                if start_date <= item_timestamp < end_date:
                    count += 1
        item_creation_counts[end_date] = count
    
    sorted_months = sorted(item_creation_counts.keys())
    sorted_counts = [item_creation_counts[month] for month in sorted_months]
    
    cumulative_counts = []
    cumulative_sum = 0
    for count in sorted_counts:
        cumulative_sum += count
        cumulative_counts.append(cumulative_sum)
    
    fig_report = go.Figure()
    fig_report.add_trace(go.Scatter(
        x=sorted_months,
        y=sorted_counts,
        mode='lines+markers+text',
        name=f'{title} per interval',
        text=sorted_counts,
        textposition='top center'
    ))
    fig_report.add_trace(go.Scatter(
        x=sorted_months,
        y=cumulative_counts,
        mode='lines+markers+text',
        name=f'Total {title}',
        text=cumulative_counts,
        textposition='top center'
    ))
    
    fig_report.update_layout(
        xaxis=dict(
            title='Reporting Date',
            tickformat='%Y-%m-%d',
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        ),
        yaxis=dict(
            title=yaxis_title
        ),
        title=f'{title} Creation Report'
    )
    
    image_path_report = f'static/images/{image_filename}.png'
    full_image_path_report = os.path.join(os.path.dirname(__file__), image_path_report)
    fig_report.write_image(full_image_path_report)
    
    fig_html_report = fig_report.to_html(full_html=False, include_plotlyjs='cdn', config={'modeBarButtonsToRemove': ['zoom2d', 'pan2d', 'select2d', 'lasso2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d', 'hoverClosestCartesian', 'hoverCompareCartesian'], 'modeBarButtonsToAdd': ['toImage']})
    
    return fig_html_report, image_path_report
