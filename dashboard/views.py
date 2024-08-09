from django.shortcuts import render, redirect
from useroperations.models import MbUser, Wms, Wfs
from Geoportal.utils import utils, php_session_data, mbConfReader
from Geoportal.settings import SESSION_NAME
from django.contrib import messages
from django.db.models.functions import TruncMonth
import plotly.graph_objs as go
from datetime import datetime, timedelta
from collections import defaultdict
import datetime as tm
import csv
from django.shortcuts import render
from .forms import UploadFileForm
from django.shortcuts import render, redirect
from django.shortcuts import render
from .models import SessionData
from django.http import JsonResponse
import os
from django.utils import timezone
from django.utils.timezone import make_aware
import pytz
import json

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

def render_template(request, template_name):
     # Default date range: last one year
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
    

    user = None

    users_before_start_date_count = MbUser.objects.filter(timestamp_create__lt=start_date).count()

    session_cookie = request.COOKIES.get(SESSION_NAME)
    if session_cookie is not None:
        session_data = php_session_data.get_mapbender_session_by_memcache(session_cookie)
        if session_data is not None:
            if b'mb_user_id' in session_data and session_data[b'mb_user_name'] != b'guest':
                userid = session_data[b'mb_user_id']
                try:
                    user = MbUser.objects.get(mb_user_id=userid)
                except MbUser.DoesNotExist:
                    # Handle the case where the user does not exist in the database
                    messages.add_message(request, messages.ERROR, ("The page is unavailable!"))

                    return redirect('useroperations:index')
                
            else:
                messages.add_message(request, messages.ERROR, ("The page is unavailable!"))
                return redirect('useroperations:index')
            
            if user is None:
        # we expect it to be read out of the session data until this point!!
                messages.add_message(request, messages.ERROR, ("The user could not be found. Please contact an administrator!"))
                return redirect('useroperations:index')
  

    import time
    user_count = MbUser.objects.count()
    wms_count = Wms.objects.count()
    wfs_count = Wfs.objects.count()
    
    users = MbUser.objects.filter(timestamp_create__range=[start_date, end_date])
  
    user_creation_counts = defaultdict(int)
    # Process each user's timestamp_create to extract the month and year, then count
    for user in users:
    # Assuming timestamp_create is a datetime object. If it's a string, parse it first:
    # user.timestamp_create = datetime.strptime(user.timestamp_create, '%Y-%m-%d %H:%M:%S.%f')
        month_year = user.timestamp_create.strftime('%Y-%m')
        user_creation_counts[month_year] += 1

        # Sort the dictionary by month
    sorted_months = sorted(user_creation_counts.keys())
    sorted_counts = [user_creation_counts[month] for month in sorted_months]

        # Calculate cumulative counts
    cumulative_counts = []
    cumulative_sum = users_before_start_date_count
    for count in sorted_counts:
                cumulative_sum += count
                cumulative_counts.append(cumulative_sum)

        # Plotting
    fig = go.Figure()

        # Add bar chart for new users per month with secondary y-axis
    fig.add_trace(go.Bar(x=sorted_months, y=sorted_counts, name='New Users per Month', yaxis='y2', marker=dict(color='rgba(255, 99, 132, 1)')))

        # Add line chart for cumulative new users
    fig.add_trace(go.Scatter(x=sorted_months, y=cumulative_counts, mode='lines+markers', name='Cumulative New Users', line=dict(color='rgba(54, 162, 235, 1)')))

        # Update layout to include secondary y-axis
    fig.update_layout(
        title_text='New and Cumulative New Users per Month',
        xaxis_title='Month',
        yaxis=dict(
            title='Cumulative Number of Users',
            titlefont=dict(color='rgba(54, 162, 235, 1)'),  # Color for the left y-axis
            tickfont=dict(color='rgba(54, 162, 235, 1)')    # Color for the left y-axis ticks
        ),
        yaxis2=dict(
            title='New Users per Month',
            titlefont=dict(color='rgba(255, 99, 132, 1)'),  # Color for the right y-axis
            tickfont=dict(color='rgba(255, 99, 132, 1)'),   # Color for the right y-axis ticks
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
        # Convert the figure to HTML for embedding in Django template
    fig_html = fig.to_html(full_html=False, include_plotlyjs='cdn')
    today_date = datetime.now().strftime('%Y-%m-%d')

    users_report = MbUser.objects.filter(timestamp_create__range=[start_date_report, end_date_report])

    import time
    user_count = MbUser.objects.count()
    wms_count = Wms.objects.count()
    wfs_count = Wfs.objects.count()

    # Determine the earliest user registration date
    earliest_user = MbUser.objects.earliest('timestamp_create')
    wms_timestamp = Wms.objects.earliest('wms_timestamp_create')
    wms_start = wms_timestamp.wms_timestamp_create
    start_of_data = earliest_user.timestamp_create

    users = MbUser.objects.filter(timestamp_create__range=[start_date, end_date])
    start_date_unix = int(time.mktime(start_date.timetuple()))
    end_date_unix = int(time.mktime(end_date.timetuple()))
    wms_all = Wms.objects.filter(wms_timestamp__range=[start_date_unix, end_date_unix])
    wms_counts = defaultdict(int)
    for wms in wms_all:
         wms_datetime = tm.datetime.fromtimestamp(wms.wms_timestamp_create)
         month_year_wms = wms_datetime.strftime('%Y-%m')
         wms_counts[month_year_wms] += 1
        
    sorted_months_wms = sorted(wms_counts.keys())
    sorted_counts_wms = [wms_counts[month] for month in sorted_months_wms]

    # Calculate cumulative counts
    cumulative_counts_wms = []
    cumulative_sum_wms = 0
    for count in sorted_counts_wms:
        cumulative_sum_wms += count
        cumulative_counts_wms.append(cumulative_sum_wms)

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
            tickfont=dict(color='rgba(54, 162, 235, 1)'),


        ),
        yaxis2=dict(
            title='WMS per Month',
            titlefont=dict(color='rgba(255, 99, 132, 1)'),
            tickfont=dict(color='rgba(255, 99, 132, 1)'),
            overlaying='y',
            side='right'
        )
    )
    fig_wms.update_layout(
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

    fig_wms = fig_wms.to_html(full_html=False, include_plotlyjs='cdn')

    users_report = MbUser.objects.filter(timestamp_create__range=[start_date_report, end_date_report])
    # # Generate the reporting date list
    reporting_date_list = []
    # start_year = 2014
    # end_year = 2027

    # for year in range(start_year, end_year + 1):
    #     reporting_date_list.append(tm.datetime.strptime(f'{year}-01-01', '%Y-%m-%d'))
    #     reporting_date_list.append(tm.datetime.strptime(f'{year}-06-01', '%Y-%m-%d'))
    
    reporting_date_list = upload_file(request)
    if isinstance(reporting_date_list, JsonResponse):
        print("reporting_date_list is a JsonResponse")
        reporting_date_list = json.loads(reporting_date_list.content)
        # Extract the reporting_date_list from the JSON response
        reporting_date_list = reporting_date_list.get('reporting_date_list', [])
    #convert tuple to list
    if reporting_date_list!=[]:
        reporting_date_list = list(reporting_date_list[1])
        # remove the key from the dict and only use the value
        reporting_date_list = [d['reporting_date'] for d in reporting_date_list]

        #convert it to tm.datetime.strptime
        reporting_date_list = [tm.datetime.strptime(date, '%Y-%m-%d') for date in reporting_date_list]
        
    else:
        # Use a default list of dates if reporting_date_list is empty
        default_dates = ['2014-03-01', '2014-07-01', '2015-07-01', '2015-03-01', '2016-02-01', '2016-12-01', '2017-01-01', '2017-06-01', '2018-01-01', '2018-06-01', '2019-01-01', '2019-06-01', '2020-01-01', '2020-06-01', '2021-01-01', '2021-06-01', '2022-01-01', '2022-06-01', '2023-01-01', '2023-06-01', '2024-01-01', '2024-06-01', '2025-01-01', '2025-06-01', '2026-01-01', '2029-12-01']
        reporting_date_list = [tm.datetime.strptime(date, '%Y-%m-%d') for date in default_dates]
    # sort it
    reporting_date_list = sorted(reporting_date_list)

    # Initialize the defaultdict for counting user creations
    user_creation_counts = defaultdict(int)
    # Handle the first data point separately
    first_start_date = reporting_date_list[0]
    count = 0
    for user in users_report:
        if user.timestamp_create < first_start_date:
            count += 1
    user_creation_counts[first_start_date] = count
    #print(f"Number of users created before {first_start_date}: {count}")

    # Calculate the number of users created between each pair of consecutive dates
    for i in range(len(reporting_date_list) - 1):
        start_date = reporting_date_list[i]
        end_date = reporting_date_list[i+1]
        count = 0

        #print(f"Start Date: {start_date} (Type: {type(start_date)})")
        for user in users_report:
            # print(f"User Timestamp: {user.timestamp_create} (Type: {type(user.timestamp_create)})")
            if start_date <= user.timestamp_create < end_date:
                count += 1
        #count = sum(1 for user in users if start_date <= user.timestamp_create < end_date)
        #month_year = start_date.strftime('%Y-%m')
        user_creation_counts[end_date] = count
        #user_creation_counts[end_date] += 0 
        #print(f"Number of users created between kiya {start_date} and {end_date}: {count}")


    # Sort the dictionary by month
    sorted_months = sorted(user_creation_counts.keys())
    sorted_counts = [user_creation_counts[month] for month in sorted_months]

    # Calculate cumulative counts
    cumulative_counts = []
    cumulative_sum = 0  # Initialize with users_before_start_date_count if needed
    for count in sorted_counts:
        cumulative_sum += count
        cumulative_counts.append(cumulative_sum)

    # Prepare the graph using Plotly
    fig_report = go.Figure()

    # Add trace for individual data points
    fig_report.add_trace(go.Scatter(
        x=sorted_months,
        y=sorted_counts,
        mode='lines+markers+text',
        name='User per interval',
        text=sorted_counts,
        textposition='top center'
        
    ))

    # Add trace for cumulative data
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
            tickformat='%Y-%m-%d',  # Format the ticks as Year-Month-Day
            #insert dtick from reporting date list
            #tickvals=reporting_date_list,
            #tickangle=45  # Rotate the tick labels for better readability
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
    

    # Convert the figure to HTML for embedding in Django template
    fig_html_report = fig_report.to_html(full_html=False, include_plotlyjs='cdn', config={'modeBarButtonsToRemove': ['zoom2d', 'pan2d', 'select2d', 'lasso2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d', 'hoverClosestCartesian', 'hoverCompareCartesian'],
    'modeBarButtonsToAdd': ['toImage']})
  
        


    latest_timestamp = timezone.now()
    start_time = latest_timestamp - timedelta(hours=72)

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
        
    context = {
        'fig_html_report': fig_html_report,
        'fig_html': fig_html,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'user_count': user_count,  
        'wms_count': wms_count,
        'wfs_count': wfs_count,
        'today_date': today_date,
        'form': UploadFileForm(),
        'fig_wms': fig_wms,
        #'reporting_date_list': reporting_date_list,
        'session_data': session_data,
        #'csv_data': csv_data,
        'image_path': '/' + image_path,
        'image_path_wms': '/' + image_path_wms,
        'image_path_session': '/' + image_path_session,
        'image_path_report': '/' + image_path_report,

    }    
    if request.is_ajax():
        #print ("AJAX request")
        return JsonResponse({ 'fig_html': fig_html,
        'fig_html_report': fig_html_report,
        'fig_wms': fig_wms,
        'session_data': session_data} )
    return render(request, template_name, context)

def dashboard(request):
   return render_template(request, 'dashboard.html')

def filter(request):
    return render_template(request, 'filter.html')

