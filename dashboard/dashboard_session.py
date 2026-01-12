import plotly.graph_objs as go
from datetime import datetime, timedelta
from .models import SessionData
import os
from django.utils import timezone
import io
import base64

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

    fig_html_session = fig_session.to_html(full_html=False, include_plotlyjs=False)

    # Save the figure as an image
    buffer = io.BytesIO()
    fig_session.write_image(buffer, format='png')
    buffer.seek(0)

    # Save the figure as an image file in static/images/
    #image_path_session = 'static/images/plotly_image.png'
    #full_image_path = os.path.join(os.path.dirname(__file__), image_path_session)
    #fig_session.write_image(full_image_path)
    # Convert the in-memory image to base64
    image_base64_session = base64.b64encode(buffer.read()).decode('utf-8')

    return fig_html_session, image_base64_session

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

    session_data, image_base64_session = get_session_data(sessions, start_date=start_date, end_date=end_date)
    
    return session_data,  image_base64_session
