from django.urls import path

from . import views
app_name = 'dashboard'
urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('filter/', views.filter, name='filter'),
]
