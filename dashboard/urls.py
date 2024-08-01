from django.urls import path

from . import views
app_name = 'dashboard'
urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/upload', views.upload_file, name='upload_file'),
]
