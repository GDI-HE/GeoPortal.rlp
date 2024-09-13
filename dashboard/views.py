from django.shortcuts import render, redirect
from useroperations.models import MbUser, Wms, Wfs, Wmc, WfsAvailability, MbGroup, MbUserMbGroup
from Geoportal.utils import utils, php_session_data, mbConfReader
from Geoportal.settings import SESSION_NAME, ALLOWED_GROUPS
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
from django.middleware.csrf import get_token
import requests

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
    dropdown_value = request.GET.get('dropdown', 'default')
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
            fig_html, image_path = generate_user_plot(start_date, end_date, dropdown_value)
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

    session_cookie = request.COOKIES.get(SESSION_NAME)
    if session_cookie is not None:
        session_data_mapbender = php_session_data.get_mapbender_session_by_memcache(session_cookie)
        if session_data_mapbender is not None:
            if b'mb_user_id' in session_data_mapbender and session_data_mapbender[b'mb_user_name'] != b'guest':
                userid = session_data_mapbender[b'mb_user_id']
                try:
                    user = MbUser.objects.get(mb_user_id=userid)
                except MbUser.DoesNotExist:
                    # Handle the case where the user does not exist in the database
                    messages.add_message(request, messages.ERROR, ("The page is unavailable!"))
                    return redirect('useroperations:index')

                # Check if the user belongs to the allowed group(s)
                allowed_groups = ALLOWED_GROUPS
                user_groups = MbGroup.objects.filter(
                    mb_group_id__in=MbUserMbGroup.objects.filter(fkey_mb_user_id=userid).values_list('fkey_mb_group_id', flat=True)
                ).values_list('mb_group_name', flat=True)
                if not any(group in allowed_groups for group in user_groups):
                    messages.add_message(request, messages.ERROR, ("You do not have the necessary permissions to access this page."))
                    return redirect('useroperations:index')

            else:
                messages.add_message(request, messages.ERROR, ("The page is unavailable!"))
                return redirect('useroperations:index')

            if user is None:
                # We expect it to be read out of the session data until this point!!
                messages.add_message(request, messages.ERROR, ("The user could not be found. Please contact an administrator!"))
                return redirect('useroperations:index')

    #users_before_start_date_count = MbUser.objects.filter(timestamp_create__lt=start_date).count()

    import time
    user_count = MbUser.objects.count()
    wms_count = Wms.objects.count()
    wfs_count = Wfs.objects.count()
    #session_count = SessionData.objects.count()
    wmc_count = Wmc.objects.count()
    csrf_token = get_token(request)
    
    context = {
        'fig_html': fig_html,
        'fig_wms': fig_wms_html,
        'fig_wfs': fig_wfs_html,
        'fig_html_report': fig_report_html,
        'session_data': session_data,
        'fig_wmc': fig_wmc_html,
        'csrf_token': csrf_token,

        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'dropdown_value': dropdown_value,
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


def generate_user_plot(start_date, end_date, dropdown_value = 'monthly'):
    users_before_start_date_count = MbUser.objects.filter(timestamp_create__lt=start_date).count()
    users = MbUser.objects.filter(timestamp_create__range=[start_date, end_date])
    user_creation_counts = defaultdict(int)

    for user in users:
        if dropdown_value == 'daily':
            time_period = user.timestamp_create.strftime('%Y-%m-%d')
        elif dropdown_value == 'weekly':
            time_period = f"{user.timestamp_create.isocalendar()[0]}-W{user.timestamp_create.isocalendar()[1]:02d}"
        elif dropdown_value == 'biyearly':
            if user.timestamp_create.month <= 6:
                time_period = f"{user.timestamp_create.year}-H1"
            else:
                time_period = f"{user.timestamp_create.year}-H2"
        elif dropdown_value == '6months':
            if user.timestamp_create.month <= 6:
                time_period = f"{user.timestamp_create.year}-H1"
            else:
                time_period = f"{user.timestamp_create.year}-H2"
        elif dropdown_value == 'yearly':
            time_period = user.timestamp_create.strftime('%Y')
        else:  # default to monthly
            time_period = user.timestamp_create.strftime('%Y-%m')
    
        user_creation_counts[time_period] += 1

    sorted_periods = sorted(user_creation_counts.keys())
    sorted_counts = [user_creation_counts[period] for period in sorted_periods]

    cumulative_counts = []
    cumulative_sum = users_before_start_date_count
    for count in sorted_counts:
        cumulative_sum += count
        cumulative_counts.append(cumulative_sum)

    fig = go.Figure()
    fig.add_trace(go.Bar(x=sorted_periods, y=sorted_counts, name=f'New Users per {dropdown_value.capitalize()}', yaxis='y2', marker=dict(color='rgba(255, 99, 132, 1)')))
    fig.add_trace(go.Scatter(x=sorted_periods, y=cumulative_counts, mode='lines+markers', name=f'Cumulative New Users', line=dict(color='rgba(54, 162, 235, 1)')))

    fig.update_layout(
        title_text=f'New and Cumulative New Users per {dropdown_value.capitalize()}',
        xaxis_title=dropdown_value.capitalize(),
        yaxis=dict(
            title='Cumulative Number of Users',
            titlefont=dict(color='rgba(54, 162, 235, 1)'),
            tickfont=dict(color='rgba(54, 162, 235, 1)')
        ),
        yaxis2=dict(
            title=f'New Users per {dropdown_value.capitalize()}',
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
#TODO refactor generate_wms_plot, generate_wfs_plot, generate_wmc_plot to make one function later
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

from django.shortcuts import render
from django.utils.translation import gettext as _
from datetime import datetime

from django.shortcuts import render, get_object_or_404

def display_service_quality(request, resource_id):
    # Fetch the service quality data from the database
    service_quality = get_object_or_404(WfsAvailability, pk=resource_id)
    resource_metadata = {
        'timestamp': service_quality.fkey_upload_id,  # Assuming this is a timestamp
        'serviceid': service_quality.fkey_wfs_id
    }

    html = ""
    table_begin = "<table>"

    html += table_begin

    if resource_id != 'wmc':
        last_status = service_quality.last_status
        availability = service_quality.availability
        fkey_upload_id = service_quality.fkey_upload_id
        feature_content = service_quality.feature_content
        status_comment = service_quality.status_comment
        average_resp_time = service_quality.average_resp_time
        upload_url = service_quality.upload_url
        feature_urls = service_quality.feature_urls
        cap_diff = service_quality.cap_diff
        monitor_count = service_quality.monitor_count

        if last_status == 1:
            html += f"<tr><td>{_('status')}</td><td><img src='../img/trafficlights/go.bmp' height='24px' width='24px' alt='{_('statusOK')}' title='{_('statusOK')}'></td></tr>"
        elif last_status == 0:
            html += f"<tr><td>{_('status')}</td><td><img src='../img/trafficlights/wait.bmp' height='24px' width='24px' alt='{_('statusChanged')}' title='{_('statusChanged')}'></td></tr>"
            if availability is not None:
                html += f"<tr><td>{_('changes')}</td><td><input type='button' value='{_('show')}' onclick=\"var newWindow = window.open('../php/mod_showCapDiff.php?serviceType={service_quality.service_type}&id={resource_metadata['serviceid']}','Capabilities Diff','width=700,height=300,scrollbars');newWindow.focus();\"></td></tr>"
        elif last_status == -1:
            html += f"<tr><td>{_('status')}</td><td><img src='../img/trafficlights/stop.bmp' height='24px' width='24px' alt='{_('statusProblem')}' title='{_('statusChanged')}'></td></tr>"

        if fkey_upload_id is not None:
            date_service = datetime.fromtimestamp(int(resource_metadata['timestamp']))  # Assuming fkey_upload_id is a timestamp
            date_monitoring = datetime.fromtimestamp(int(fkey_upload_id))  # Assuming fkey_upload_id is a timestamp
            interval = date_service - date_monitoring
            html += f"<tr><td>{_('metadataAge')}</td><td>{interval.days} {_('days')}</td></tr>"

        if availability is not None:
            html += f"<tr><td>{_('availability')}</td><td>{availability} %</td></tr>"
        else:
            html += f"<tr><td>{_('availability')}</td><td>{_('notMonitored')}</td></tr>"

        html += f"<tr><td>{_('featureContent')}</td><td>{feature_content}</td></tr>"
        html += f"<tr><td>{_('statusComment')}</td><td>{status_comment}</td></tr>"
        html += f"<tr><td>{_('averageResponseTime')}</td><td>{average_resp_time} ms</td></tr>"
        html += f"<tr><td>{_('uploadURL')}</td><td>{upload_url}</td></tr>"
        html += f"<tr><td>{_('featureURLs')}</td><td>{feature_urls}</td></tr>"
        html += f"<tr><td>{_('capDiff')}</td><td>{cap_diff}</td></tr>"
        html += f"<tr><td>{_('monitorCount')}</td><td>{monitor_count}</td></tr>"

        try:
            response = requests.get(upload_url)
            if response.status_code == 200:
                html += f"<tr><td>{_('serviceStatus')}</td><td>{_('serviceStatusOK')}</td></tr>"
            else:
                html += f"<tr><td>{_('serviceStatus')}</td><td>{_('serviceStatusProblem')}</td></tr>"
        except requests.exceptions.RequestException as e:
            html += f"<tr><td>{_('serviceStatus')}</td><td>{_('Error')}</td></tr>"
    else:
        html += f"<tr><td colspan='2'>{_('wmcQualityText')}</td></tr>"
    # TODO
    #non_working_urls = check_all_upload_urls(request)
    #take only first 20 non working urls
    #non_working_urls = non_working_urls[:20]

    # html += f"<tr><td colspan='2'>{_('nonWorkingUrls')}</td></tr>"
    # for url in non_working_urls:
    #     html += f"<tr><td colspan='2'>{url}</td></tr>"


    # html += "</table>"

    return render(request, 'test.html', {'html': html})

def check_all_upload_urls(request):
    all_services = WfsAvailability.objects.all()
    #take 100-200 services
    all_services = all_services[400:500]
    non_working_urls = []

    for service in all_services:
        try:
            response = requests.get(service.upload_url)
            if response.status_code !=200:
                non_working_urls.append(service.upload_url)
        except requests.exceptions.RequestException:
            non_working_urls.append(service.upload_url)
    return non_working_urls

   
from useroperations.models import Wms, Layer, LayerKeyword
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render
from django.db.models import Q, Exists, OuterRef, F, Case, When, BooleanField, Value, IntegerField
from django.db.models.functions import Length
import logging

# Configure logging
#logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('my_custom_logger') 

def get_layer_statistics(layers):
    # Count layers without abstracts
    layers_without_abstract = layers.filter(Q(layer_abstract__isnull=True) | Q(layer_abstract=''))
    layers_without_abstract_count = layers_without_abstract.count()
    layers_without_abstract_names = list(layers_without_abstract.values_list('layer_name', flat=True))

    # Annotate layers with a boolean indicating if they have keywords
    layers_with_keyword_annotation = layers.annotate(
        has_keyword=Exists(
            LayerKeyword.objects.filter(fkey_layer=OuterRef('pk'))
        )
    )


    # Filter layers to get only those without keywords
    layers_without_keywords = layers_with_keyword_annotation.filter(has_keyword=False)
    layers_without_keyword_count = layers_without_keywords.count()
    layers_without_keyword_names = list(layers_without_keywords.values_list('layer_name', flat=True))

    # Count layers where abstract matches the title (case-sensitive and trimmed)
    layers_abstract_matches_title = layers.annotate(
        abstract_matches_title=Case(
            When(
                Q(layer_abstract=F('layer_title')),
                then=Value(True)
            ),
            default=Value(False),
            output_field=BooleanField()
        )
    ).filter(abstract_matches_title=True)
    layers_abstract_matches_title_count = layers_abstract_matches_title.count()
    layers_abstract_matches_title_names = list(layers_abstract_matches_title.values_list('layer_title', flat=True))

    # Count layers with short abstracts (less than 50 characters)
    layers_with_short_abstract = layers.annotate(
        abstract_length=Length('layer_abstract', output_field=IntegerField())
    ).filter(abstract_length__lt=50)
    layers_with_short_abstract_count = layers_with_short_abstract.count()
    layers_with_short_abstract_info = list(layers_with_short_abstract.values_list('layer_title', 'layer_abstract'))

    # Get the total layer count directly from the database
    total_layers = layers.count()

    # Check if all layers have abstracts and keywords
    all_layers_have_abstract = layers_without_abstract_count == 0
    all_layers_have_keywords = layers_without_keyword_count == 0

    # Collect keywords
    keywords_present = list(
        LayerKeyword.objects.filter(fkey_layer__in=layers).values_list('fkey_keyword__keyword', flat=True)
    )
    logger.debug(f"Keywords Present: {keywords_present}")
    

    layers_with_abstract = layers.exclude(Q(layer_abstract__isnull=True) | Q(layer_abstract=''))

    abstracts_present = list(layers_with_abstract.values_list('layer_abstract', flat=True))

    # Determine if each layer's abstract matches its title
    layers_abstract_match = layers.annotate(
        abstract_matches_title=Case(
            When(
                Q(layer_abstract=F('layer_title')),
                then=Value(True)
            ),
            default=Value(False),
            output_field=BooleanField()
        )
    ).values_list('abstract_matches_title', flat=True)

    # Get all layer names
    layer_names = list(layers.values_list('layer_title', flat=True))

    return {
        'total_layers': total_layers,
        'layers_without_abstract_count': layers_without_abstract_count,
        'layers_without_abstract_names': layers_without_abstract_names,
        'layers_without_keyword_count': layers_without_keyword_count,
        'layers_without_keyword_names': layers_without_keyword_names,
        'layers_abstract_matches_title_count': layers_abstract_matches_title_count,
        'layers_abstract_matches_title_names': layers_abstract_matches_title_names,
        'layers_with_short_abstract_count': layers_with_short_abstract_count,
        'layers_with_short_abstract_info': layers_with_short_abstract_info,
        'all_layers_have_abstract': all_layers_have_abstract,
        'all_layers_have_keywords': all_layers_have_keywords,
        'keywords_present': keywords_present,
        'abstracts_present': abstracts_present,
        'layers_abstract_match': ['Y' if match else 'N' for match in layers_abstract_match],
        'layer_names': layer_names
    }

def check_layer_abstracts_and_keywords(request):
    search_query = request.GET.get('search', '')

    # Filter WMS services based on the search query
    if search_query:
        wms_services = Wms.objects.filter(
            Q(wms_id__icontains=search_query) | Q(wms_title__icontains=search_query)
        ).order_by('wms_id')
    else:
        wms_services = Wms.objects.all().order_by('wms_id')

    # Aggregate data across all pages
    all_layers = Layer.objects.filter(fkey_wms_id__in=wms_services).distinct()

    total_layers_without_abstract = all_layers.filter(Q(layer_abstract__isnull=True) | Q(layer_abstract='')).count()
    total_layers_without_keyword = all_layers.annotate(
        has_keyword=Exists(
            LayerKeyword.objects.filter(fkey_layer=OuterRef('pk'))
        )
    ).filter(has_keyword=False).count()
    total_layers_abstract_matches_title = all_layers.annotate(
        abstract_matches_title=Case(
            When(
                Q(layer_abstract=F('layer_title')),
                then=Value(True)
            ),
            default=Value(False),
            output_field=BooleanField()
        )
    ).filter(abstract_matches_title=True).count()
    total_layers_with_short_abstract = all_layers.annotate(
        abstract_length=Length('layer_abstract', output_field=IntegerField())
    ).filter(abstract_length__lt=50).count()

    # Paginate the WMS services
    paginator = Paginator(wms_services, 10)  # Show 10 WMS services per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    results = []

    for wms in page_obj:
        # Get all unique layers for this WMS
        layers = Layer.objects.filter(fkey_wms_id=wms).distinct()
        layer_stats = get_layer_statistics(layers)

        results.append({
            'wms_id': wms.wms_id,
            'wms_title': wms.wms_title,
            'total_layers': layer_stats['total_layers'],
            'layers_without_abstract': layer_stats['layers_without_abstract_count'],
            'layers_without_keywords': layer_stats['layers_without_keyword_count'],
            'all_layers_have_abstract': layer_stats['all_layers_have_abstract'],
            'all_layers_have_keywords': layer_stats['all_layers_have_keywords'],
            'keywords_present': layer_stats['keywords_present'],
            'abstracts_present': layer_stats['abstracts_present'],
            'layers_without_abstract_names': layer_stats['layers_without_abstract_names'],
            'layers_without_keyword_names': layer_stats['layers_without_keyword_names'],
            'layers_abstract_matches_title_count': layer_stats['layers_abstract_matches_title_count'],
            'layers_abstract_matches_title_names': layer_stats['layers_abstract_matches_title_names'],
            'layers_with_short_abstract_count': layer_stats['layers_with_short_abstract_count'],
            'layers_with_short_abstract_info': layer_stats['layers_with_short_abstract_info'],
            'layers_abstract_match': layer_stats['layers_abstract_match'],
            'layer_names': layer_stats['layer_names']
        })

    context = {
        'results': results,
        'page_obj': page_obj,
        'total_layers_without_abstract': total_layers_without_abstract,
        'total_layers_without_keyword': total_layers_without_keyword,
        'total_layers_abstract_matches_title': total_layers_abstract_matches_title,
        'total_layers_with_short_abstract': total_layers_with_short_abstract
    }

    return render(request, 'check_abstract.html', context)

def load_more_data(request):
    page_number = request.GET.get('page', 1)
    search_query = request.GET.get('search', '')

    # Filter WMS services based on the search query
    if search_query:
        wms_services = Wms.objects.filter(
            Q(wms_id__icontains=search_query) | Q(wms_title__icontains=search_query)
        ).order_by('wms_id')
    else:
        wms_services = Wms.objects.all().order_by('wms_id')

    paginator = Paginator(wms_services, 10)  # Show 10 WMS services per page
    page_obj = paginator.get_page(page_number)

    results = []

    for wms in page_obj:
        # Get all unique layers for this WMS
        layers = Layer.objects.filter(fkey_wms_id=wms).distinct()
        layer_stats = get_layer_statistics(layers)

        results.append({
            'wms_id': wms.wms_id,
            'wms_title': wms.wms_title,
            'total_layers': layer_stats['total_layers'],
            'layers_without_abstract': layer_stats['layers_without_abstract_count'],
            'layers_without_keywords': layer_stats['layers_without_keyword_count'],
            'all_layers_have_abstract': layer_stats['all_layers_have_abstract'],
            'all_layers_have_keywords': layer_stats['all_layers_have_keywords'],
            'keywords_present': layer_stats['keywords_present'],
            'abstracts_present': layer_stats['abstracts_present'],
            'layers_without_abstract_names': layer_stats['layers_without_abstract_names'],
            'layers_without_keyword_names': layer_stats['layers_without_keyword_names'],
            'layers_abstract_matches_title_count': layer_stats['layers_abstract_matches_title_count'],
            'layers_abstract_matches_title_names': layer_stats['layers_abstract_matches_title_names'],
            'layers_with_short_abstract_count': layer_stats['layers_with_short_abstract_count'],
            'layers_with_short_abstract_info': layer_stats['layers_with_short_abstract_info'],
            'layers_abstract_match': layer_stats['layers_abstract_match'],
            'layer_names': layer_stats['layer_names']
        })

    return JsonResponse({
        'results': results,
        'has_next': page_obj.has_next()
    })

def search_data(request):
    search_query = request.GET.get('query', '')

    # Filter WMS services based on the search query
    wms_services = Wms.objects.filter(
        Q(wms_id__icontains=search_query) | Q(wms_title__icontains=search_query)
    ).order_by('wms_id')

    results = []

    for wms in wms_services:
        # Get all unique layers for this WMS
        layers = Layer.objects.filter(fkey_wms_id=wms).distinct()
        layer_stats = get_layer_statistics(layers)

        results.append({
            'wms_id': wms.wms_id,
            'wms_title': wms.wms_title,
            'total_layers': layer_stats['total_layers'],
            'layers_without_abstract': layer_stats['layers_without_abstract_count'],
            'layers_without_keywords': layer_stats['layers_without_keyword_count'],
            'all_layers_have_abstract': layer_stats['all_layers_have_abstract'],
            'all_layers_have_keywords': layer_stats['all_layers_have_keywords'],
            'keywords_present': layer_stats['keywords_present'],
            'abstracts_present': layer_stats['abstracts_present'],
            'layers_without_abstract_names': layer_stats['layers_without_abstract_names'],
            'layers_without_keyword_names': layer_stats['layers_without_keyword_names'],
            'layers_abstract_matches_title_count': layer_stats['layers_abstract_matches_title_count'],
            'layers_abstract_matches_title_names': layer_stats['layers_abstract_matches_title_names'],
            'layers_with_short_abstract_count': layer_stats['layers_with_short_abstract_count'],
            'layers_with_short_abstract_info': layer_stats['layers_with_short_abstract_info'],
            'layers_abstract_match': layer_stats['layers_abstract_match'],
            'layer_names': layer_stats['layer_names']
        })

    return JsonResponse({'results': results})
# from useroperations.models import Keyword, Layer    
# def get_layer_keywords(request, layer_id):
#     try:
#         layer = Layer.objects.get(layer_id=layer_id)
#         keywords = Keyword.objects.filter(layerkeyword__fkey_layer=layer)
        
#         context = {
#             'layer': layer,
#             'keywords': keywords,
#         }
#         return render(request, 'layer_keywords.html', context)
#     except Layer.DoesNotExist:
#         return render(request, 'layer_not_found.html')
