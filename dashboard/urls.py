from django.urls import path
<<<<<<< HEAD
from . import views
app_name ='dashboard'
urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
    # Add more URL patterns here
]
=======

from . import views
app_name = 'dashboard'
urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    #path('dashboard/upload_file', views.upload_file, name='upload_file'),
    path('filter/', views.filter, name='filter'),
    path('download_csv/', views.download_csv, name='download_csv'),
]
>>>>>>> 100_dashboard_deepak
