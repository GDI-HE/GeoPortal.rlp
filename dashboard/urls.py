from django.urls import path

from . import views
app_name = 'dashboard'
urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    #path('dashboard/upload_file', views.upload_file, name='upload_file'),
    path('filter/', views.filter, name='filter'),
    path('download_csv/', views.download_csv, name='download_csv'),
    #delete some which are not necessary in future
     path('service-quality/<int:resource_id>/', views.display_service_quality, name='display_service_quality'),
    path('check-abstracts/', views.check_layer_abstracts_and_keywords, name='check_abstracts'),
    #path('layer-keywords/<int:layer_id>/', views.get_layer_keywords, name='layer_keywords'),
    path('load-more-data/', views.load_more_data, name='load_more_data'),
]
