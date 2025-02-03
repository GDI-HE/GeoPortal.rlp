from django.shortcuts import render, redirect, get_object_or_404
from useroperations.models import MbUser, Wms, Wfs, Wmc, WfsAvailability, MbGroup, MbUserMbGroup, MbUserDeletion, WmsDeletion, WfsDeletion, WmcDeletion
from Geoportal.utils import php_session_data
from Geoportal.settings import SESSION_NAME, ALLOWED_GROUPS
from django.contrib import messages
import plotly.graph_objs as go
from datetime import datetime, timedelta, date
import time
from collections import defaultdict
import datetime as tm
import csv
from .forms import UploadFileForm
import os
import io
import json
import base64
from django.http import HttpResponse, JsonResponse
from django.middleware.csrf import get_token
import requests
from django.db.models.functions import TruncDay
from django.db.models import Count, Sum, Avg, Max
from django.utils.translation import gettext as _
from dashboard.user_report import upload_file
from dashboard.dashboard_utils import convert_to_datetime
from dashboard.dashboard_request import process_request
from dashboard.dashboard_userplot import generate_user_plot
from dashboard.dashboard_session import get_filtered_session_data
from django.utils import timezone
from .models import WMC, SESSION_USER
from dateutil.relativedelta import relativedelta


def render_template(request, template_name):
     # Get the current time
    now = timezone.now()

    # Filter session data to include only entries from the last hour
    last_hour_sessions = SESSION_USER.objects.filter(datetime__gte=now - timedelta(hours=1)).order_by('datetime')

    # Prepare data for the chart
    labels = [session.datetime.strftime('%Y-%m-%d %H:%M') for session in last_hour_sessions]  # x-axis labels (time)
    data = [session.session_number for session in last_hour_sessions]  # y-axis data (session numbers)

    # Pass the labels and data to the template
    #end of session user applitation plot
    
     # Default date range: last one year
     #if request.get contains contentType === 'fig_html_report', the return json response separately
     
    end_date_default = datetime.now()
    start_date_default = end_date_default- timedelta(days=365)

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
    content_type = request.GET.get('contentType') 
    if content_type is None:
        content_type = 'session_data'
    fig_html = None
    fig_wms_html = None
    fig_wfs_html = None
    fig_wmc_html = None
    fig_report_html = None
    image_path = None
    image_path_wms = None
    image_path_wfs = None
    image_path_wmc = None
    image_path_report = None
    #once call the generate_wms_plot function on loading the page
    #generate_wms_plot(request, start_date, end_date) 
    if not request.is_ajax():
        fig_html, image_base64 = generate_user_plot(start_date, end_date)
        fig_wms_html, image_base64_wms = generate_wms_plot(request, start_date, end_date)
        fig_wfs_html, image_base64_wfs = generate_wfs_plot(request, start_date, end_date)
        fig_wmc_html, image_base64_wmc= generate_wmc_plot(request, start_date, end_date)
        if content_type == 'fig_html_report':
            fig_report_html, image_path_report = generate_user_report(request, start_date_report, end_date_report)
        elif content_type == 'fig_wms_report':
            fig_report_html, image_path_report = generate_wms_report(request, start_date_report, end_date_report)
        session_data, image_base64_session = get_filtered_session_data(request)
    else:
        if keyword == 'fig_html':
            fig_html, image_base64 = generate_user_plot(start_date, end_date, dropdown_value)
            fig_wms_html, image_path_wms = None, None
            fig_wfs_html, image_path_wfs = None, None
            fig_wmc_html, image_path_wmc = None, None
            fig_report_html, image_path_report = None, None
            session_data, image_path_session = None, None
            image_base64_wms, image_base64_wfs, image_base64_wmc, image_base64_session = None, None, None, None
        elif keyword == 'fig_wms':
            fig_html, image_path = None, None
            fig_wms_html, image_base64_wms = generate_wms_plot(request, start_date, end_date)
            fig_wfs_html, image_path_wfs = None, None
            fig_wmc_html, image_path_wmc = None, None
            fig_report_html, image_path_report = None, None
            session_data, image_path_session = None, None
            image_base64, image_base64_wfs, image_base64_wmc, image_base64_session = None, None, None, None
        elif keyword == 'fig_wfs':
            fig_html, image_path = None, None
            fig_wms_html, image_path_wms = None, None
            fig_wfs_html, image_base64_wfs = generate_wfs_plot(request, start_date, end_date)
            fig_wmc_html, image_path_wmc = None, None
            fig_report_html, image_path_report = None, None
            session_data, image_path_session = None, None
            image_base64, image_base64_wms, image_base64_wmc, image_base64_session = None, None, None, None
        elif keyword == 'fig_wmc':
            fig_html, image_path = None, None
            fig_wms_html, image_path_wms = None, None
            fig_wfs_html, image_path_wfs = None, None
            fig_wmc_html, image_base64_wmc = generate_wmc_plot(request, start_date, end_date)
            fig_report_html, image_path_report = None, None
            session_data = None
            image_base64, image_base64_wfs, image_base64_wms, image_base64_session = None, None, None, None
        elif keyword == 'session_data':
            fig_html, image_path = None, None
            fig_wms_html = None
            fig_wfs_html = None
            fig_wmc_html = None
            fig_report_html, image_path_report = None, None
            image_base64, image_base64_wfs, image_base64_wms, image_base64_wmc = None, None, None, None
            session_data, image_base64_session = get_filtered_session_data(request)
        else:
            #here is some problem
            #do something so that all the function will not be created when clicked on specific card
            fig_html, image_base64 = generate_user_plot(start_date, end_date)
            fig_wms_html, image_base64_wms = generate_wms_plot(request, start_date, end_date)
            fig_wfs_html,image_base64_wfs = generate_wfs_plot(request, start_date, end_date)
            fig_wmc_html,image_base64_wmc = generate_wmc_plot(request, start_date, end_date)
            session_data, image_base64_session = get_filtered_session_data(request)
            if content_type == 'fig_html_report':
                fig_report_html, image_path_report = generate_user_report(request, start_date_report, end_date_report)
            elif content_type == 'fig_wms_report':
                fig_report_html, image_path_report = generate_wms_report(request, start_date_report, end_date_report)
            elif content_type == 'fig_wfs_report':
                fig_report_html, image_path_report = generate_wfs_report(request, start_date_report, end_date_report)
            elif content_type == 'fig_wmc_report':
                fig_report_html, image_path_report = generate_wmc_report(request, start_date_report, end_date_report)
            #haven't worked for the session report download and report creation TODO
    
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
                    messages.add_message(request, messages.ERROR, _("The page is unavailable!"))
                    return redirect('useroperations:index')

                # Check if the user belongs to the allowed group(s)
                allowed_groups = ALLOWED_GROUPS
                user_groups = MbGroup.objects.filter(
                    mb_group_id__in=MbUserMbGroup.objects.filter(fkey_mb_user_id=userid).values_list('fkey_mb_group_id', flat=True)
                ).values_list('mb_group_name', flat=True)
                if not any(group in allowed_groups for group in user_groups):
                    messages.add_message(request, messages.ERROR, _("You do not have the necessary permissions to access this page."))
                    return redirect('useroperations:index')

            else:
                messages.add_message(request, messages.ERROR, _("The page is unavailable!"))
                return redirect('useroperations:index')

            if user is None:
                # We expect it to be read out of the session data until this point!!
                messages.add_message(request, messages.ERROR, _("You do not have the necessary permissions to access this page.!"))
                return redirect('useroperations:index')

    #users_before_start_date_count = MbUser.objects.filter(timestamp_create__lt=start_date).count()
    # Get yesterday's date
    yesterday = timezone.now().date() - timezone.timedelta(days=1)

    # Fetch the top 10 WMCs by actual_load from yesterday
    top_wmcs = WMC.objects.filter(date=yesterday).order_by('-actual_load')[:10]

    # Prepare data for the donut chart
    donut_chart_data = {
        'labels': [wmc.wmc_title for wmc in top_wmcs],
        'values': [wmc.actual_load for wmc in top_wmcs]
    }

    # Calculate the date range for the previous month
    today = date.today()
    first_day_of_current_month = today.replace(day=1)
    last_day_of_previous_month = first_day_of_current_month - timedelta(days=1)
    first_day_of_previous_month = last_day_of_previous_month.replace(day=1)
    last_day_of_second_last_month = first_day_of_previous_month - timedelta(days=1)
    first_day_of_second_last_month = last_day_of_second_last_month.replace(day=1)

    # Query the database for data within the previous month
    last_month_data = WMC.objects.filter(date__range=[first_day_of_previous_month, last_day_of_previous_month])

    # Retrieve data for the second last month
    second_last_month_data = WMC.objects.filter(
        date__range=[first_day_of_second_last_month, last_day_of_second_last_month])

    # Calculate the total load count for each wmc_id and wmc_title for both months
    load_counts = {}
    second_last_month_loads = {}
    
    for wmc_record in last_month_data:
        if wmc_record.wmc_id not in load_counts:
            load_counts[wmc_record.wmc_id] = {'total_load': 0, 'wmc_title': wmc_record.wmc_title}
        load_counts[wmc_record.wmc_id]['total_load'] += wmc_record.actual_load

    for wmc_record in second_last_month_data:
        if wmc_record.wmc_id not in second_last_month_loads:
            second_last_month_loads[wmc_record.wmc_id] = {'total_load': 0, 'wmc_title': wmc_record.wmc_title}
        second_last_month_loads[wmc_record.wmc_id]['total_load'] += wmc_record.actual_load
    # Create a list of dictionaries with wmc_id, wmc_title, total load, and month name for the previous month
    load_counts_list = [{'wmc_id': wmc_id, 'wmc_title': data['wmc_title'], 'total_actual_load': data['total_load'],
                         'month_name': last_day_of_previous_month.strftime('%B')}
                        for wmc_id, data in load_counts.items()]

    # Create a list of dictionaries with wmc_id, wmc_title, total load, and month name for the second last month
    load_counts_list_second_last_month = [{'wmc_id': wmc_id, 'wmc_title': data['wmc_title'], 'total_actual_load': data['total_load'],
                         'month_name': last_day_of_second_last_month.strftime('%B')}
                        for wmc_id, data in second_last_month_loads.items()]

    # Sort the list by total_actual_load count in descending order for the previous month
    load_counts_list.sort(key=lambda x: x['total_actual_load'], reverse=True)

    # Sort the list by total_actual_load count in descending order for the second last month
    load_counts_list_second_last_month.sort(key=lambda x: x['total_actual_load'], reverse=True)
    # Get the top four highest total_actual_load counts for the previous month
    top_four_loads = load_counts_list[:4]
    top_10_loads_last_month = load_counts_list[:5]
      # Get the top four highest total_actual_load counts of for the second last month
    top_four_loads_second_last_month = load_counts_list_second_last_month[:4]
    # Calculate the comparison percentage and determine the color for each top `wmc_id`
    top_four_wmc_ids = [item['wmc_id'] for item in top_four_loads]

        # Get the current date
    current_date = datetime.now()

    # Calculate last month's date
    last_month_date = current_date - relativedelta(months=1)

    # Calculate second last month's date
    second_last_month_date = current_date - relativedelta(months=2)

    # Extract the years
    current_year = current_date.year
    last_month_year = last_month_date.year
    second_last_month_year = second_last_month_date.year
    # Get the name of the second last month
    second_last_month_name = second_last_month_date.strftime('%B')

    comparison_data = []
    for wmc_id in top_four_wmc_ids:
        last_month_load = load_counts.get(wmc_id, {}).get('total_load', 0)
        second_last_month_load = second_last_month_loads.get(wmc_id, {}).get('total_load', 0)
        
        
        if second_last_month_load != 0:
            percentage_change = ((last_month_load - second_last_month_load) / second_last_month_load) * 100
        else:
            percentage_change = 0
        
        # Determine the color for the card
        card_color = 'green' if percentage_change >= 0 else 'red'
        
        # Include the second last month's name in the dictionary
        comparison_data.append({
            'wmc_id': wmc_id,
            'percentage_change': percentage_change,
            'card_color': card_color,
            'second_last_month_name': second_last_month_name,
            
        })

  
    user_count = MbUser.objects.count()
    wms_count = Wms.objects.count()
    wfs_count = Wfs.objects.count()
    #session_count = SessionData.objects.count()
    wmc_count = Wmc.objects.count()
    csrf_token = get_token(request)
    if content_type == 'fig_wms_report':
        fig_html = fig_wms_html
    elif content_type == 'fig_wfs_report':
        fig_html = fig_wfs_html
    elif content_type == 'fig_wmc_report':
        fig_html = fig_wmc_html
    elif content_type == 'fig_upload_report':
        fig_html = fig_report_html
    else:
        fig_html = fig_html  # Default case

    loadcount_chart = get_wmc_loadcount(request)
        # Get yesterday's date
    #yesterday = timezone.now().date() - timezone.timedelta(days=1)

    # Fetch the top 10 WMCs by actual_load from yesterday
    #top_wmcs = WMC.objects.filter(date=yesterday).order_by('-actual_load')[:10]

    # Fetch the top 4 WMCs by total actual load for comparison
    #top_four_loads = WMC.objects.values('wmc_id', 'wmc_title').annotate(total_actual_load=Sum('actual_load')).order_by('-total_actual_load')[:4]

    # Fetch actual_load data for the last three months for wmc_id=7107
    three_months_ago = timezone.now().date() - timezone.timedelta(days=360)
    wmc_data = WMC.objects.filter(wmc_id=7107, date__gte=three_months_ago).order_by('date')

    # Prepare data for the line chart
    line_chart_data = {
        'dates': [wmc.date.strftime('%Y-%m-%d') for wmc in wmc_data],
        'actual_loads': [wmc.actual_load for wmc in wmc_data]
    }

    # Fetch the top 5 WMCs by average load
    top_5_wmcs_avg_load = WMC.objects.values('wmc_id', 'wmc_title').annotate(avg_load=Avg('actual_load')).order_by('-avg_load')[:5]

    # Prepare data for the bar chart
    bar_chart_data = {
        'labels': [wmc['wmc_title'] for wmc in top_5_wmcs_avg_load],
        'values': [wmc['avg_load'] for wmc in top_5_wmcs_avg_load]
    }

    # Get today's date
    today = timezone.now().date()

    # Get the start of the current year
    start_of_year = timezone.now().replace(month=1, day=1)

    # Get the highest actual load for the current year
    highest_actual_load_year = WMC.objects.filter(date__gte=start_of_year).aggregate(max_load=Max('actual_load'))['max_load'] or 0

    # Get today's total load
    current_day_total_load = WMC.objects.filter(date=today).aggregate(total_load=Sum('actual_load'))['total_load'] or 0

    # Determine the max value for the gauge (highest of the year or today's load)
    gauge_max_value = max(highest_actual_load_year, current_day_total_load)

    # Prepare data for the gauge chart
    gauge_chart_data = {
        'value': current_day_total_load,
        'max': gauge_max_value  # Set max to the higher of the year's max or today's load
    }

# Current datetime and range definitions
    now = datetime.now()
    start_date_7_days = now - timedelta(days=7)
    start_date_14_days = now - timedelta(days=1)

    # Total session count for the last 7 days
    total_sessions_7_days = SESSION_USER.objects.filter(datetime__gte=start_date_7_days).aggregate(
        total=Sum('session_number')
    )['total'] or 0
     # Format the total session count with 'K'
    total_sessions_7_days_k = f"{total_sessions_7_days / 1000:.1f}K" if total_sessions_7_days >= 1000 else str(total_sessions_7_days)

    # Query session data for the last 14 days
    sessions_last_14_days = (
        SESSION_USER.objects.filter(datetime__gte=start_date_14_days)
        .values('datetime')  # Group by datetime (5-minute interval)
        .annotate(total_sessions=Sum('session_number'))
        .order_by('datetime')
    )

    # Prepare data for the graph
    chart_dates = [entry['datetime'].strftime('%Y-%m-%d %H:%M') for entry in sessions_last_14_days]
    data_14_days = [entry['total_sessions'] for entry in sessions_last_14_days]

 

    context = {
        'fig_html': fig_html,
        'fig_wms': fig_wms_html,
        'fig_wfs': fig_wfs_html,
        'fig_html_report': fig_report_html,
        'fig_wms_report': fig_report_html,
        'fig_wfs_report': fig_report_html,
        'fig_wmc_report': fig_report_html,
        'fig_upload_report': fig_report_html,
        'session_data': session_data,
        'fig_wmc': fig_wmc_html,
        'csrf_token': csrf_token,
        'image_base64_wms': image_base64_wms,
        'image_base64_wfs': image_base64_wfs,
        'image_base64_wmc': image_base64_wmc,
        'image_base64': image_base64,
        'image_base64_session': image_base64_session,

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
        'image_path_wmc': '/' + image_path_wmc if image_path_wmc else '',
        'donut_chart_data': donut_chart_data,
        'top_four_loads': top_four_loads,
        'top_four_loads_second_last_month': top_four_loads_second_last_month,
        'comparison_data': comparison_data,
        'loadcount_chart': loadcount_chart,
        'top_10_loads_last_month': top_10_loads_last_month,
        'last_month_year': timezone.now().year,
        'second_last_month_year': timezone.now().year - 1,
        'line_chart_data': line_chart_data,
        'bar_chart_data': bar_chart_data,
        'gauge_chart_data': gauge_chart_data,
        'labels': labels,
        'data': data,
        'total_sessions_7_days': total_sessions_7_days_k,  # Total for the last 7 days
        'chart_dates': chart_dates,  # 5-minute intervals for the last 14 days
        'data_14_days': data_14_days,  # Session counts for the graph
    }
    if context is None:
        context = {}
    image_path = context.get('image_path')
    if image_path is None:
        context['image_path'] = ''
    if request.is_ajax():

        return JsonResponse({'fig_html_report': fig_report_html, 'loadcount_chart': loadcount_chart,
                             'fig_wms_report': fig_report_html, 'fig_upload_report': fig_report_html, 
                             'fig_wfs_report': fig_report_html, 'fig_wmc_report': fig_report_html, 
                             'fig_html': fig_html, 'fig_wms': fig_wms_html, 'fig_wfs': fig_wfs_html, 
                             'session_data':session_data, 'fig_wmc': fig_wmc_html})

    return render(request, template_name, context)

def dashboard(request):
   

    return render_template(request, 'dashboard.html')

def filter(request):
    return render_template(request, 'filter.html')


def download_csv(request):
    is_ajax = request.GET.get('is_ajax')
    keyword = request.GET.get('keyword', 'default')
    dropdown = request.GET.get('dropdown')  # Extract the dropdown parameter  

    if keyword == 'fig_wms':
        sorted_months, sorted_counts, cumulative_counts, _, _, _, _, _, _, _, _, _, _,_,_= process_request(request)
    elif keyword == 'fig_wfs':
        _, _, _, sorted_months, sorted_counts, cumulative_counts, _, _, _,_,_,_, _,_,_ = process_request(request)
    elif keyword == "fig_wmc":
        _, _, _, _, _, _, sorted_months, sorted_counts, cumulative_counts, _,_,_,_,_,_= process_request(request)
        
    elif keyword == "session_data":
        pass
        #TODO
    elif keyword == 'fig_html_report':
        pass
    elif keyword == 'fig_html':
        _, _, _, _, _, _,_,_,_,sorted_months, sorted_counts, cumulative_counts,_,_,_ = process_request(request)
    else:
        return HttpResponse(status=400, content="Invalid keyword")
    
    clean_keyword = keyword.replace('fig_', '').upper()
    # Create the CSV data
    csv_data = []
    if dropdown == 'yearly':
        period_label = 'Year'
    elif dropdown == 'monthly':
        period_label = 'Month'
    elif dropdown == 'weekly':
        period_label = 'Week'
    elif dropdown == 'daily':
        period_label = 'Day'
    elif dropdown == '6-monthly':
        period_label = '6-Month Period'
    else:
        period_label = 'Period'
    csv_data.append([period_label, f'{clean_keyword} per {period_label}', f'Cumulative {clean_keyword}'])
    for period, count, cumulative in zip(sorted_months, sorted_counts, cumulative_counts):
        csv_data.append([period, count, cumulative])

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
        
        sorted_months_wms, sorted_counts_wms, cumulative_counts_wms, _, _, _,_,_,_,_,_,_,deleted_wms_count, _,_ = process_request(request)
        fig_wms_html, image_base64 = create_plotly_figure(
        sorted_months_wms, 
        sorted_counts_wms, 
        cumulative_counts_wms, 
        deleted_wms_count, 
        'WMS per Month', 
        'Month', 
        'Cumulative Number of WMS', 
        'WMS per Month', 
        'Deleted WMS per Month', 
        'plotly_image_wms'
          )
        return fig_wms_html, image_base64

def generate_wfs_plot(request, start_date, end_date):
        
        _, _, _, sorted_months_wfs, sorted_counts_wfs, cumulative_counts_wfs, _, _, _,_,_,_,_,deleted_wfs_count,_ = process_request(request)
        fig_wfs_html, image_base64 = create_plotly_figure(
            sorted_months_wfs, sorted_counts_wfs, cumulative_counts_wfs, deleted_wfs_count, 'WFS per Month', 'Month', 'Cumulative Number of WFS', 'WFS per Month', 'Deleted WFS per Month', 'plotly_image_wfs'
        )
        return fig_wfs_html, image_base64

def generate_wmc_plot(request, start_date, end_date):
        
        _, _, _,_, _, _, sorted_months_wmc, sorted_counts_wmc, cumulative_counts_wmc,_,_,_,_,_,deleted_wmc_count = process_request(request)
        fig_wmc_html, image_base64= create_plotly_figure(
        sorted_months_wmc, 
        sorted_counts_wmc, 
        cumulative_counts_wmc, 
        deleted_wmc_count, 
        'WMC per Month', 
        'Month', 
        'Cumulative Number of WMC', 
        'WMC per Month', 
        'Deleted WMC per Month', 
        'plotly_image_wmc'
        )
        return fig_wmc_html, image_base64

def create_plotly_figure(sorted_periods, sorted_counts, cumulative_counts, sorted_deleted_counts, title, xaxis_title, yaxis_title, yaxis2_title, yaxis3_title, image_filename):
    fig = go.Figure()

    # Add new users bar graph
    fig.add_trace(go.Bar(
        x=sorted_periods, 
        y=sorted_counts, 
        name=f'New Users per {title}', 
        yaxis='y2', 
        marker=dict(color='rgba(54, 162, 235, 1)'),
        offset=1 
    ))

    # Add cumulative new users line graph
    fig.add_trace(go.Scatter(
        x=sorted_periods, 
        y=cumulative_counts, 
        mode='lines+markers', 
        name=f'Cumulative New Users', 
        line=dict(color='rgba(255, 0, 0, 1)'),
    ))

    # Add deleted users bar graph
    fig.add_trace(go.Bar(
        x=sorted_periods, 
        y=sorted_deleted_counts, 
        name=f'Deleted Users per {title}', 
        yaxis='y3', 
        marker=dict(color='rgba(255, 159, 64, 1)'),
        visible='legendonly',
    ))

    # Update layout
    fig.update_layout(
        title=f'User Statistics per {title}',
        xaxis=dict(title=xaxis_title),
        yaxis=dict(
            title=yaxis_title,
            titlefont=dict(color='rgba(255, 0, 0, 1)'),
            tickfont=dict(color='rgba(255, 0, 0, 1)')
        ),
        yaxis2=dict(
            title=yaxis2_title,
            titlefont=dict(color='rgba(54, 162, 235, 1)'),
            tickfont=dict(color='rgba(54, 162, 235, 1)'),
            overlaying='y',
            side='right',
            position=0.97,
        ),
        yaxis3=dict(
            title=yaxis3_title,
            titlefont=dict(color='rgba(255, 159, 64, 1)'),
            tickfont=dict(color='rgba(255, 159, 64, 1)'),
            anchor='free',
            overlaying='y',
            side='right',
            position=1
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        ),
        barmode='group',
        #autosize=True,
        #margin=dict(l=50, r=100, t=50, b=50),  # Adjust margins for better fit on mobile
        #font = dict(size=9)

    )
    fig_html = fig.to_html(full_html=False, include_plotlyjs='cdn')
    # Save the figure as an image
    buffer = io.BytesIO()
    fig.write_image(buffer, format='png')
    buffer.seek(0)

    # Save the figure as an image file in static/images/
    #image_path = f'static/images/{image_filename}.png'
    #full_image_path = os.path.join(os.path.dirname(__file__), image_path)
    #fig.write_image(full_image_path)
    # Convert the in-memory image to base64
    image_base64 = base64.b64encode(buffer.read()).decode('utf-8')

    return fig_html, image_base64



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
    
    # Add bar graph for monthly data
    fig_report.add_trace(go.Bar(
        x=sorted_months,
        y=sorted_counts,
        name=f'{title} per interval',
        text=sorted_counts,
        textposition='outside',
        marker=dict(color='rgba(255, 99, 132, 1)'),
        yaxis='y2'  # Assign to y2 axis
    ))
    
    # Add scatter (line) graph for cumulative data
    fig_report.add_trace(go.Scatter(
        x=sorted_months,
        y=cumulative_counts,
        mode='lines+markers+text',
        name=f'Total {title}',
        text=cumulative_counts,
        textposition='top center',
        line=dict(color='rgba(54, 162, 235, 1)')
    ))
    
    # Update layout
    fig_report.update_layout(
        xaxis=dict(
            title='Reporting Date',
            tickformat='%Y-%m-%d',
        ),
        yaxis=dict(
            title='Cumulative Total',
            titlefont=dict(color='rgba(54, 162, 235, 1)'),
            tickfont=dict(color='rgba(54, 162, 235, 1)')
        ),
        yaxis2=dict(
            title=f'{title} per Interval',
            titlefont=dict(color='rgba(255, 99, 132, 1)'),
            tickfont=dict(color='rgba(255, 99, 132, 1)'),
            overlaying='y',
            side='right',
            position=1  # Adjust position to avoid overlap
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        ),
        title=f'{title} Creation Report',
        barmode='group'  # Ensure bars are grouped
    )
    
    
    image_path_report = f'static/images/{image_filename}.png'
    full_image_path_report = os.path.join(os.path.dirname(__file__), image_path_report)
    fig_report.write_image(full_image_path_report)
    
    fig_html_report = fig_report.to_html(full_html=False, include_plotlyjs='cdn', config={'modeBarButtonsToRemove': ['zoom2d', 'pan2d', 'select2d', 'lasso2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d', 'hoverClosestCartesian', 'hoverCompareCartesian'], 'modeBarButtonsToAdd': ['toImage']})
    
    return fig_html_report, image_path_report


def generate_user_report(request, start_date_report, end_date_report):
    return generate_report(request, start_date_report, end_date_report, MbUser, 'User', 'Number of Users', 'plotly_image_user_report')

def generate_wms_report(request, start_date_report, end_date_report):
    return generate_report(request, start_date_report, end_date_report, Wms, 'WMS', 'Number of WMS', 'plotly_image_wms_report')

def generate_wfs_report(request, start_date_report, end_date_report):
    return generate_report(request, start_date_report, end_date_report, Wfs, 'WFS', 'Number of WFS', 'plotly_image_wfs_report')

def generate_wmc_report(request, start_date_report, end_date_report):
    return generate_report(request, start_date_report, end_date_report, Wmc, 'WMC', 'Number of WMC', 'plotly_image_wmc_report')

#TODO move this all to a separate python file
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
    # when the abstract is null or empty string, it is not counted as short_abstract.
    #If needs to be counted, remove the ~Q(layer_abstract__exact='') condition
    layers_with_short_abstract = layers.annotate(
        abstract_length=Length('layer_abstract', output_field=IntegerField())
    ).filter(Q(abstract_length__lt=50) & ~Q(layer_abstract__isnull=True) & ~Q(layer_abstract__exact=''))
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

    #also get the wms's fees and accessconstraints
    wms_ids = layers.values_list('fkey_wms_id', flat=True)
    wms_fees = Wms.objects.filter(wms_id__in=wms_ids).values_list('fees', flat=True)
    wms_accessconstraints = Wms.objects.filter(wms_id__in=wms_ids).values_list('accessconstraints', flat=True)


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
        'layer_names': layer_names,
        'wms_fees': wms_fees,
        'wms_accessconstraints': wms_accessconstraints
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
            'layer_names': layer_stats['layer_names'],
            'wms_fees': wms.fees,
            'wms_accessconstraints': wms.accessconstraints
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
            'layer_names': layer_stats['layer_names'],
            'wms_fees': wms.fees,
            'wms_accessconstraints': wms.accessconstraints

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
            'layer_names': layer_stats['layer_names'],
            'wms_fees': wms.fees,
            'wms_accessconstraints': wms.accessconstraints

        })

    return JsonResponse({'results': results})
from useroperations.models import Keyword, Layer    
def get_layer_keywords(request, layer_id):
    try:
        layer = Layer.objects.get(layer_id=layer_id)
        keywords = Keyword.objects.filter(layerkeyword__fkey_layer=layer)
        
        context = {
            'layer': layer,
            'keywords': keywords,
        }
        return render(request, 'layer_keywords.html', context)
    except Layer.DoesNotExist:
        return render(request, 'layer_not_found.html')

def get_wmc_loadcount(request):
    # start of line graph
    start = request.GET.get('start')
    if start == None:
        start = datetime.now() - timedelta(days=50)
    end = request.GET.get('end')
    if end == None:
        end = datetime.now()
    wmc_id = request.GET.get('wmc_id')
    if wmc_id == None:
        wmc_id = 7107 #Boris Hessen 2024
   
    wmc_data = WMC.objects.all()
    
    if start:
        wmc_data = wmc_data.filter(date__gte=start)
    if end:
        wmc_data = wmc_data.filter(date__lte=end)
    if wmc_id:
        wmc_data = wmc_data.filter(wmc_id=wmc_id)
    x_data = [c.date for c in wmc_data]
    y_data = [int(c.actual_load) for c in wmc_data]
   
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x_data, y=y_data, mode='lines+markers'))
    fig.update_layout(
        title={
            'text': 'WMC Load Count',
            'font_size': 14,
            'xanchor': 'center',
            'x': 0.5
        })
    loadcount_chart = fig.to_html()
    response_data = {
        'loadcount_chart' : loadcount_chart,
        'start': start,
        'end': end,
        'wmc_id': wmc_id
    }  
    # if request.is_ajax():
    #     return JsonResponse(response_data)
    return loadcount_chart