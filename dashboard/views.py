from django.shortcuts import render, redirect
from useroperations.models import MbUser, Wms, Wfs, Wmc
from Geoportal.utils import utils, php_session_data, mbConfReader
from Geoportal.settings import SESSION_NAME
from django.contrib import messages
from django.db.models.functions import TruncMonth
import plotly.graph_objs as go
from datetime import datetime, timedelta
from collections import defaultdict
import datetime as tm
import csv
from .forms import UploadFileForm
from .models import SessionData
import os
from django.utils import timezone
from django.utils.timezone import make_aware
import pytz
import json
import time
from django.http import HttpResponse, JsonResponse

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
            
            if request.is_ajax():
                return JsonResponse({'reporting_date_list': reporting_date_list})
    else:
        form = UploadFileForm()

    # Render the dashboard.html with the reporting_date_list
    #return render(request, 'dashboard.html', {'form': form, 'reporting_date_list': reporting_date_list})
    return reporting_date_list

def read_reporting_dates_from_csv(file):
    reporting_date_list = []
    csv_data = []
    csv_reader = csv.DictReader(file.read().decode('utf-8').splitlines())
    for row in csv_reader:
        date = tm.datetime.strptime(row['reporting_date'], '%Y-%m-%d')
        reporting_date_list.append(date)
        csv_data.append(row)
    return reporting_date_list, csv_data

def get_session_data(sessions, start_date=None, end_date=None):
    if not start_date:
        start_date = timezone.now() - timedelta(hours=72)
    elif start_date and isinstance(start_date, str):
        start_date = timezone.make_aware(datetime.strptime(start_date, '%Y-%m-%d'), timezone.get_current_timezone())
    
    if not end_date:
        end_date = timezone.now()
    if end_date and isinstance(end_date, str):
        end_date = timezone.make_aware(datetime.strptime(end_date, '%Y-%m-%d'), timezone.get_current_timezone())

    session_data = []
    for session in sessions:
        if start_date and session.timestamp_create < start_date:
            continue
        if end_date and session.timestamp_create > end_date:
            continue
        session_data.append({
            'timestamp_create': session.timestamp_create,
            'number_of_user': session.number_of_user
        })
    timestamps = [session['timestamp_create'] for session in session_data]
    user_counts = [session['number_of_user'] for session in session_data]

    fig_session = go.Figure()
    fig_session.add_trace(go.Scatter
    (
        x=timestamps,
        y=user_counts,
        mode='lines',
        name='User Sessions',
        text=user_counts,
        textposition='top center'
    ))
    fig_session.update_layout(
        xaxis=dict(
            title='Timestamp',
            tickformat='%Y-%m-%d %H:%M:%S',  # Format the ticks as Year-Month-Day
            tickangle=45  # Rotate the tick labels for better readability
        ),
        legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="center",
        x=0.5
    ),
        yaxis=dict(
            title='Number of Users'
        ),
        title='User Sessions Report'
    )
    image_path_session = 'static/images/plotly_image_session.png'
    full_image_path_session = os.path.join(os.path.dirname(__file__), image_path_session)
    fig_session.write_image(full_image_path_session)
    fig_html_session = fig_session.to_html(full_html=False, include_plotlyjs='cdn')
    return fig_html_session, image_path_session



def get_data_counts(model, timestamp_field, start_date, end_date):
    start_date_unix = int(time.mktime(start_date.timetuple()))
    end_date_unix = int(time.mktime(end_date.timetuple()))
    users_before_start_date_count = model.objects.filter(**{f"{timestamp_field}__lt": start_date_unix}).count()
    data_all = model.objects.filter(**{f"{timestamp_field}__range": [start_date_unix, end_date_unix]})
    data_counts = defaultdict(int)

    for data in data_all:
        data_datetime = datetime.fromtimestamp(getattr(data, timestamp_field))
        month_year_data = data_datetime.strftime('%Y-%m')
        data_counts[month_year_data] += 1

    sorted_months_data = sorted(data_counts.keys())
    sorted_counts_data = [data_counts[month] for month in sorted_months_data]

    # Calculate cumulative counts
    cumulative_counts_data = []
    cumulative_sum_data = users_before_start_date_count
    for count in sorted_counts_data:
        cumulative_sum_data += count
        cumulative_counts_data.append(cumulative_sum_data)

    return sorted_months_data, sorted_counts_data, cumulative_counts_data

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

    start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)

    # Get WMS data counts
    sorted_months_wms, sorted_counts_wms, cumulative_counts_wms = get_data_counts(Wms, 'wms_timestamp_create', start_date, end_date)

    # Get WFS data counts
    sorted_months_wfs, sorted_counts_wfs, cumulative_counts_wfs = get_data_counts(Wfs, 'wfs_timestamp_create', start_date, end_date)

    # Get WMC data counts
    sorted_months_wmc, sorted_counts_wmc, cumulative_counts_wmc = get_data_counts(Wmc, 'wmc_timestamp', start_date, end_date)

    # Now you can use sorted_months_wms, sorted_counts_wms, cumulative_counts_wms, sorted_months_wfs, sorted_counts_wfs, and cumulative_counts_wfs as needed
    return sorted_months_wms, sorted_counts_wms, cumulative_counts_wms, sorted_months_wfs, sorted_counts_wfs, cumulative_counts_wfs, sorted_months_wmc, sorted_counts_wmc, cumulative_counts_wmc

def render_template(request, template_name):
     # Default date range: last one year
     #if request.get contains contentType === 'fig_html_report', the return json response separately
     
    end_date_default = datetime.now()
    start_date_default = end_date_default - timedelta(days=365)

    start_date_report = datetime(2011, 1, 1)
    end_date_report = datetime(2028, 12, 31)

    # Get date range from request parameters
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    # Parse dates or use defaults
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d') if start_date_str else start_date_default
    except ValueError:
        start_date = start_date_default

    try:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str else end_date_default
    except ValueError:
        end_date = end_date_default
    
    keyword = request.GET.get('keyword', 'default')
    #once call the generate_wms_plot function on loading the page
    #generate_wms_plot(request, start_date, end_date) 
    if not request.is_ajax():
        fig_html, image_path = generate_user_plot(start_date, end_date)
        fig_wms_html, image_path_wms = generate_wms_plot(request, start_date, end_date)
        fig_wfs_html, image_path_wfs = generate_wfs_plot(request, start_date, end_date)
        fig_wmc_html, image_path_wmc = generate_wmc_plot(request, start_date, end_date)
        fig_report_html, image_path_report = generate_user_report(request, start_date_report, end_date_report)
        session_data, image_path_session = get_filtered_session_data(request)
    else:
        if keyword == 'fig_html':
            fig_html, image_path = generate_user_plot(start_date, end_date)
            fig_wms_html, image_path_wms = None, None
            fig_wfs_html, image_path_wfs = None, None
            fig_wmc_html, image_path_wmc = None, None
            fig_report_html, image_path_report = None, None
            session_data, image_path_session = None, None
        elif keyword == 'fig_wms':
            fig_html, image_path = None, None
            fig_wms_html, image_path_wms = generate_wms_plot(request, start_date, end_date)
            fig_wfs_html, image_path_wfs = None, None
            fig_wmc_html, image_path_wmc = None, None
            fig_report_html, image_path_report = None, None
            session_data, image_path_session = None, None
        elif keyword == 'fig_wfs':
            fig_html, image_path = None, None
            fig_wms_html, image_path_wms = None, None
            fig_wfs_html, image_path_wfs = generate_wfs_plot(request, start_date, end_date)
            fig_wmc_html, image_path_wmc = None, None
            fig_report_html, image_path_report = None, None
            session_data, image_path_session = None, None
        elif keyword == 'fig_wmc':
            fig_html, image_path = None, None
            fig_wms_html, image_path_wms = None, None
            fig_wfs_html, image_path_wfs = None, None
            fig_wmc_html, image_path_wmc = generate_wmc_plot(request, start_date, end_date)
            fig_report_html, image_path_report = None, None
            session_data, image_path_session = None, None
        elif keyword == 'session_data':
            fig_html, image_path = None, None
            fig_wms_html, image_path_wms = None, None
            fig_wfs_html, image_path_wfs = None, None
            fig_wmc_html, image_path_wmc = None, None
            fig_report_html, image_path_report = None, None
            session_data, image_path_session = get_filtered_session_data(request)
        else:
            fig_html, image_path = generate_user_plot(start_date, end_date)
            fig_wms_html, image_path_wms = generate_wms_plot(request, start_date, end_date)
            fig_wfs_html, image_path_wfs = generate_wfs_plot(request, start_date, end_date)
            fig_wmc_html, image_path_wmc = generate_wmc_plot(request, start_date, end_date)
            fig_report_html, image_path_report = generate_user_report(request, start_date_report, end_date_report)
            session_data, image_path_session = get_filtered_session_data(request)
    
    user = None

    #users_before_start_date_count = MbUser.objects.filter(timestamp_create__lt=start_date).count()

    import time
    user_count = MbUser.objects.count()
    wms_count = Wms.objects.count()
    wfs_count = Wfs.objects.count()
    #session_count = SessionData.objects.count()
    wmc_count = Wmc.objects.count()
    
    context = {
        'fig_html': fig_html,
        'fig_wms': fig_wms_html,
        'fig_wfs': fig_wfs_html,
        'fig_html_report': fig_report_html,
        'session_data': session_data,
        'fig_wmc': fig_wmc_html,

        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'user_count': user_count,
        'wms_count': wms_count,
        'wfs_count': wfs_count,
        'wmc_count': wmc_count,
        #'today_date': today_date,
        'form': UploadFileForm(),
        'image_path': '/' + image_path if image_path else '',
        'image_path_wms': '/' + image_path_wms if image_path_wms else '',
        'image_path_wfs': '/' + image_path_wfs if image_path_wfs else '',
        'image_path_report': '/' + image_path_report if image_path_report else '',
        'image_path_session': '/' + image_path_session if image_path_session else '',
        'image_path_wmc': '/' + image_path_wmc if image_path_wmc else '',
    }
    if context is None:
        context = {}
    image_path = context.get('image_path')
    if image_path is None:
        context['image_path'] = ''
    if request.is_ajax():
        return JsonResponse({'fig_html': fig_html, 'fig_wms': fig_wms_html, 'fig_wfs': fig_wfs_html, 'fig_html_report': fig_report_html, 'session_data':session_data, 'fig_wmc': fig_wmc_html})

    return render(request, template_name, context)

def dashboard(request):
   return render_template(request, 'dashboard.html')

def filter(request):
    return render_template(request, 'filter.html')


def generate_user_plot(start_date, end_date):
    users_before_start_date_count = MbUser.objects.filter(timestamp_create__lt=start_date).count()
    users = MbUser.objects.filter(timestamp_create__range=[start_date, end_date])
    user_creation_counts = defaultdict(int)

    for user in users:
        month_year = user.timestamp_create.strftime('%Y-%m')
        user_creation_counts[month_year] += 1

    sorted_months = sorted(user_creation_counts.keys())
    sorted_counts = [user_creation_counts[month] for month in sorted_months]

    cumulative_counts = []
    cumulative_sum = users_before_start_date_count
    for count in sorted_counts:
        cumulative_sum += count
        cumulative_counts.append(cumulative_sum)

    fig = go.Figure()
    fig.add_trace(go.Bar(x=sorted_months, y=sorted_counts, name='New Users per Month', yaxis='y2', marker=dict(color='rgba(255, 99, 132, 1)')))
    fig.add_trace(go.Scatter(x=sorted_months, y=cumulative_counts, mode='lines+markers', name='Cumulative New Users', line=dict(color='rgba(54, 162, 235, 1)')))

    fig.update_layout(
        title_text='New and Cumulative New Users per Month',
        xaxis_title='Month',
        yaxis=dict(
            title='Cumulative Number of Users',
            titlefont=dict(color='rgba(54, 162, 235, 1)'),
            tickfont=dict(color='rgba(54, 162, 235, 1)')
        ),
        yaxis2=dict(
            title='New Users per Month',
            titlefont=dict(color='rgba(255, 99, 132, 1)'),
            tickfont=dict(color='rgba(255, 99, 132, 1)'),
            overlaying='y',
            side='right'
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        )
    )
    image_path = 'static/images/plotly_image.png'
    full_image_path = os.path.join(os.path.dirname(__file__), image_path)
    fig.write_image(full_image_path)
    fig_html = fig.to_html(full_html=False, include_plotlyjs='cdn')
    return fig_html, image_path



def download_csv(request):
    is_ajax = request.GET.get('is_ajax')
    keyword = request.GET.get('keyword', 'default')

    if keyword == 'fig_wms':
        sorted_months, sorted_counts, cumulative_counts, _, _, _, _, _, _ = process_request(request)
    elif keyword == 'fig_wfs':
        _, _, _, sorted_months, sorted_counts, cumulative_counts, _, _, _ = process_request(request)
    elif keyword == "fig_html":
        #TODO
        pass
    elif keyword == "session_data":
        pass
        #TODO
    elif keyword == 'fig_html_report':
        pass
    elif keyword == 'fig_wmc':
        _, _, _, _, _, _, sorted_months, sorted_counts, cumulative_counts = process_request(request)
    else:
        return HttpResponse(status=400, content="Invalid keyword")
    
    clean_keyword = keyword.replace('fig_', '').upper()
    # Create the CSV data
    csv_data = []
    csv_data.append(['Month', f'{clean_keyword} per Month', f'Cumulative {clean_keyword}'])
    for month, count, cumulative in zip(sorted_months, sorted_counts, cumulative_counts):
        csv_data.append([month, count, cumulative])

    if is_ajax:
        # Return the CSV data as a string for AJAX requests
        response = HttpResponse(content_type='text/csv')
        writer = csv.writer(response)
        for row in csv_data:
            writer.writerow(row)
        return response
    else:
        # Return the CSV data as a file download for non-AJAX requests
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="wms_data.csv"'
        writer = csv.writer(response)
        for row in csv_data:
            writer.writerow(row)
        return response

def generate_wms_plot(request, start_date, end_date):
        
        sorted_months_wms, sorted_counts_wms, cumulative_counts_wms, _, _, _,_,_,_ = process_request(request)
        fig_wms = go.Figure()
        fig_wms.add_trace(go.Bar(x=sorted_months_wms, y=sorted_counts_wms, name='WMS per Month', yaxis='y2', marker=dict(color='rgba(255, 99, 132, 1)'), text=sorted_counts_wms, textposition='outside'))
        fig_wms.add_trace(go.Scatter(x=sorted_months_wms, y=cumulative_counts_wms, mode='lines+markers+text', name='Cumulative WMS', line=dict(color='rgba(54, 162, 235, 1)')))
        fig_wms.update_layout(
            title_text='WMS per Month',
            xaxis_title='Month',
            xaxis=dict(
                title='Month',
                tickangle=45
            ),
            yaxis=dict(
                title='Cumulative Number of WMS',
                titlefont=dict(color='rgba(54, 162, 235, 1)'),
                tickfont=dict(color='rgba(54, 162, 235, 1)')
            ),
            yaxis2=dict(
                title='WMS per Month',
                titlefont=dict(color='rgba(255, 99, 132, 1)'),
                tickfont=dict(color='rgba(255, 99, 132, 1)'),
                overlaying='y',
                side='right'
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5
            )
        )
        image_path_wms = 'static/images/plotly_image_wms.png'
        full_image_path_wms = os.path.join(os.path.dirname(__file__), image_path_wms)
        fig_wms.write_image(full_image_path_wms)
        fig_wms_html = fig_wms.to_html(full_html=False, include_plotlyjs='cdn')
        return fig_wms_html, image_path_wms

def generate_wfs_plot(request, start_date, end_date):
        
        _, _, _, sorted_months_wfs, sorted_counts_wfs, cumulative_counts_wfs, _, _, _ = process_request(request)
        fig_wfs = go.Figure()
        fig_wfs.add_trace(go.Bar(x=sorted_months_wfs, y=sorted_counts_wfs, name='WFS per Month', yaxis='y2', marker=dict(color='rgba(255, 99, 132, 1)'), text=sorted_counts_wfs, textposition='outside'))
        fig_wfs.add_trace(go.Scatter(x=sorted_months_wfs, y=cumulative_counts_wfs, mode='lines+markers+text', name='Cumulative WFS', line=dict(color='rgba(54, 162, 235, 1)')))
        fig_wfs.update_layout(
            title_text='WFS per Month',
            xaxis_title='Month',
            xaxis=dict(
                title='Month',
                tickangle=45
            ),
            yaxis=dict(
                title='Cumulative Number of WFS',
                titlefont=dict(color='rgba(54, 162, 235, 1)'),
                tickfont=dict(color='rgba(54, 162, 235, 1)')
            ),
            yaxis2=dict(
                title='WFS per Month',
                titlefont=dict(color='rgba(255, 99, 132, 1)'),
                tickfont=dict(color='rgba(255, 99, 132, 1)'),
                overlaying='y',
                side='right'
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5
            )
        )
        image_path_wfs = 'static/images/plotly_image_wfs.png'
        full_image_path_wfs = os.path.join(os.path.dirname(__file__), image_path_wfs)
        fig_wfs.write_image(full_image_path_wfs)
        fig_wfs_html = fig_wfs.to_html(full_html=False, include_plotlyjs='cdn')
        return fig_wfs_html, image_path_wfs

def generate_wmc_plot(request, start_date, end_date):
        
        _, _, _,_, _, _, sorted_months_wmc, sorted_counts_wmc, cumulative_counts_wmc = process_request(request)
        fig_wmc = go.Figure()
        fig_wmc.add_trace(go.Bar(x=sorted_months_wmc, y=sorted_counts_wmc, name='wmc per Month', yaxis='y2', marker=dict(color='rgba(255, 99, 132, 1)'), text=sorted_counts_wmc, textposition='outside'))
        fig_wmc.add_trace(go.Scatter(x=sorted_months_wmc, y=cumulative_counts_wmc, mode='lines+markers+text', name='Cumulative wmc', line=dict(color='rgba(54, 162, 235, 1)')))
        fig_wmc.update_layout(
            title_text='wmc per Month',
            xaxis_title='Month',
            xaxis=dict(
                title='Month',
                tickangle=45
            ),
            yaxis=dict(
                title='Cumulative Number of wmc',
                titlefont=dict(color='rgba(54, 162, 235, 1)'),
                tickfont=dict(color='rgba(54, 162, 235, 1)')
            ),
            yaxis2=dict(
                title='wmc per Month',
                titlefont=dict(color='rgba(255, 99, 132, 1)'),
                tickfont=dict(color='rgba(255, 99, 132, 1)'),
                overlaying='y',
                side='right'
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5
            )
        )
        image_path_wmc = 'static/images/plotly_image_wmc.png'
        full_image_path_wmc = os.path.join(os.path.dirname(__file__), image_path_wmc)
        fig_wmc.write_image(full_image_path_wmc)
        fig_wmc_html = fig_wmc.to_html(full_html=False, include_plotlyjs='cdn')
        return fig_wmc_html, image_path_wmc


def generate_user_report(request, start_date_report, end_date_report):
    users_report = MbUser.objects.filter(timestamp_create__range=[start_date_report, end_date_report])
    
    reporting_date_list = upload_file(request)
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
    user_creation_counts = defaultdict(int)
    
    first_start_date = reporting_date_list[0]
    count = 0
    for user in users_report:
        if user.timestamp_create < first_start_date:
            count += 1
    user_creation_counts[first_start_date] = count
    
    for i in range(len(reporting_date_list) - 1):
        start_date = reporting_date_list[i]
        end_date = reporting_date_list[i+1]
        count = 0
        for user in users_report:
            if start_date <= user.timestamp_create < end_date:
                count += 1
        user_creation_counts[end_date] = count
    
    sorted_months = sorted(user_creation_counts.keys())
    sorted_counts = [user_creation_counts[month] for month in sorted_months]
    
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
        name='User per interval',
        text=sorted_counts,
        textposition='top center'
    ))
    fig_report.add_trace(go.Scatter(
        x=sorted_months,
        y=cumulative_counts,
        mode='lines+markers+text',
        name='Total Users',
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
            title='Number of Users'
        ),
        title='User Creation Report'
    )
    
    image_path_report = 'static/images/plotly_image_report.png'
    full_image_path_report = os.path.join(os.path.dirname(__file__), image_path_report)
    fig_report.write_image(full_image_path_report)
    
    fig_html_report = fig_report.to_html(full_html=False, include_plotlyjs='cdn', config={'modeBarButtonsToRemove': ['zoom2d', 'pan2d', 'select2d', 'lasso2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d', 'hoverClosestCartesian', 'hoverCompareCartesian'], 'modeBarButtonsToAdd': ['toImage']})
    
    return fig_html_report, image_path_report

def get_filtered_session_data(request):
    latest_timestamp = timezone.now()
    start_time = latest_timestamp - timedelta(hours=120)

    # Get date range from GET parameters if available
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    if start_date_str and end_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')

        # Make dates timezone-aware
        start_date = timezone.make_aware(datetime.combine(start_date, datetime.min.time()), timezone.get_current_timezone())
        end_date = timezone.make_aware(datetime.combine(end_date, datetime.min.time()), timezone.get_current_timezone())
    else:
        start_date = start_time
        end_date = latest_timestamp
 
    # Get all session data
    sessions = SessionData.objects.all()

    # Filter sessions within the date range
    sessions = sessions.filter(timestamp_create__range=[start_date, end_date])
    sessions = sessions.order_by('timestamp_create')

    session_data, image_path_session = get_session_data(sessions, start_date=start_date, end_date=end_date)
    
    return session_data, image_path_session