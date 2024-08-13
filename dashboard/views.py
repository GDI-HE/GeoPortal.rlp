
from django.shortcuts import render
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from dashboard.models import SESSION_USER

def dashboard_view(request):
    # Get filter parameter from request
    filter_option = request.GET.get('filter', '7')  # Default to last 7 days

    now = timezone.now()

    if filter_option == '7':
        start_date = (now - timedelta(days=7)).replace(hour=0, minute=5, second=0, microsecond=0)
        end_date = now.replace(hour=23, minute=55, second=0, microsecond=0)
    elif filter_option == '24':
        start_date = (now - timedelta(hours=24)).replace(minute=5, second=0, microsecond=0)
        end_date = now.replace(minute=55, second=0, microsecond=0)
    else:
        start_date = (now - timedelta(days=7)).replace(hour=0, minute=5, second=0, microsecond=0)
        end_date = now.replace(hour=23, minute=55, second=0, microsecond=0)

    # Filter session user data
    session_data = SESSION_USER.objects.filter(datetime__gte=start_date, datetime__lte=end_date).order_by('datetime')

    # Prepare data for the chart
    dates = [data.datetime.strftime('%Y-%m-%d %H:%M:%S') for data in session_data]
    session_numbers = [data.session_number for data in session_data]

    context = {
        'dates': dates,
        'session_numbers': session_numbers,
        'filter_option': filter_option,
    }

    return render(request, 'dashboard.html', context)

