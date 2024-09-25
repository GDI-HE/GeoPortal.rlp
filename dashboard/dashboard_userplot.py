from useroperations.models import MbUser
import plotly.graph_objs as go
from collections import defaultdict
import os 
import io
import base64
from dashboard.dashboard_utils import get_time_period
from dashboard.dashboard_request import  fetch_deleted_users_data


def generate_user_plot(start_date, end_date, dropdown_value='monthly'):
    users_before_start_date_count = MbUser.objects.filter(timestamp_create__lt=start_date).count()
    users = MbUser.objects.filter(timestamp_create__range=[start_date, end_date])
    user_creation_counts = defaultdict(int)

    # Calculate user creation counts
    for user in users:
        time_period = get_time_period(user.timestamp_create, dropdown_value)
        user_creation_counts[time_period] += 1
    
    sorted_periods = sorted(user_creation_counts.keys())
    sorted_counts = [user_creation_counts[period] for period in sorted_periods]
    
    cumulative_counts = []
    cumulative_sum = users_before_start_date_count
    for count in sorted_counts:
        cumulative_sum += count
        cumulative_counts.append(cumulative_sum)
    
    # Fetch deleted user data
    deleted_dates, deleted_counts = fetch_deleted_users_data()
    deleted_user_counts = defaultdict(int)
    
    for date, count in zip(deleted_dates, deleted_counts):
        time_period = get_time_period(date, dropdown_value)
        deleted_user_counts[time_period] += count
    
    all_time_periods = set(sorted_periods).union(set(deleted_user_counts.keys()))
    sorted_periods = sorted(all_time_periods)
    sorted_deleted_counts = [-deleted_user_counts[period] for period in sorted_periods]  # Make deleted counts negative
    fig = go.Figure()
    # Add new users bar graph
    fig.add_trace(go.Bar(
        x=sorted_periods, 
        y=sorted_counts, 
        name=f'New Users per {dropdown_value.capitalize()}', 
        yaxis='y2', 
        marker=dict(color='rgba(255, 99, 132, 1)'),
        offset=1
    ))
    
    # Add cumulative new users line graph
    fig.add_trace(go.Scatter(
        x=sorted_periods, 
        y=cumulative_counts, 
        mode='lines+markers', 
        name=f'Cumulative New Users', 
        line=dict(color='rgba(54, 162, 235, 1)'),
    ))
    
    # Add deleted users bar graph
    fig.add_trace(go.Bar(
        x=sorted_periods, 
        y=sorted_deleted_counts, 
        name=f'Deleted Users per {dropdown_value.capitalize()}', 
        yaxis='y3', 
        marker=dict(color='rgba(255, 159, 64, 1)'),
        #visible='legendonly',
        
        # offsetgroup=1
    ))
    
    # Update layout
    fig.update_layout(
        title=f'User Statistics per {dropdown_value.capitalize()}',
        xaxis=dict(title='Time Period'),
        yaxis=dict(
            title='Cumulative New Users',
            titlefont=dict(color='rgba(54, 162, 235, 1)'),
            tickfont=dict(color='rgba(54, 162, 235, 1)')
        ),
        yaxis2=dict(
            title=f'New User per {dropdown_value.capitalize()}   ',
            titlefont=dict(color='rgba(255, 99, 132, 1)'),
            tickfont=dict(color='rgba(255, 99, 132, 1)'),
            overlaying='y',
            side='right'
        ),
        yaxis3=dict(
            title=f'Deleted Users per {dropdown_value.capitalize()}',
            titlefont=dict(color='rgba(255, 159, 64, 1)'),
            tickfont=dict(color='rgba(255, 159, 64, 1)'),
            anchor='free',
            overlaying='y',
            side='right',
            position=1,
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        ),
        barmode='group',
    )

    fig_html = fig.to_html(full_html=False, include_plotlyjs='cdn')

    # Save the figure as an image
    buffer = io.BytesIO()
    fig.write_image(buffer, format='png')
    buffer.seek(0)

    # Save the figure as an image file in static/images/
    image_path = 'static/images/plotly_image.png'
    full_image_path = os.path.join(os.path.dirname(__file__), image_path)
    fig.write_image(full_image_path)
    # Convert the in-memory image to base64
    image_base64 = base64.b64encode(buffer.read()).decode('utf-8')

    return fig_html, image_base64, image_path