from django.urls import include, path

from . import views
app_name = 'dashboard'
extra_patterns = [
    path("metadata-quality/", views.check_layer_abstracts_and_keywords, name='check_abstracts'),
]

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    #path('dashboard/upload_file', views.upload_file, name='upload_file'),
    path('filter/', views.filter, name='filter'),
    path('download_csv/', views.download_csv, name='download_csv'),
     #delete some which are not necessary in future
    path('service-quality/<int:resource_id>/', views.display_service_quality, name='display_service_quality'),
    path('dashboard/', include(extra_patterns)),
    path('layer-keywords/<int:layer_id>/', views.get_layer_keywords, name='layer_keywords'),
    path('load-more-data/', views.load_more_data, name='load_more_data'),
    path('search-data/', views.search_data, name='search_data'),
    path('metadata-quality/', views.metadata_quality, name='metadata_quality'),  #remove this later
    # path('update-service/', views.update_service, name='update_service'),
    path('add-keyword/', views.add_keyword, name='add_keyword'),
    path('add-abstract/', views.add_abstract, name='add_abstract'),
    path('add-license/', views.add_license, name='add_license'),
    path('add-constraint/', views.add_constraint, name='add_constraint'),
    path('get-layers-without-keywords/', views.get_layers_without_keywords, name='get_layers_without_keywords'),
    path('get-layers-without-abstracts/', views.get_layers_without_abstracts, name='get_layers_without_abstracts'),
    path('get-layers-with-short-abstract/', views.get_layers_with_short_abstract, name = 'get_layers_with_short_abstract'),
    path('get-abstract-matches-title/', views.get_abstract_matches_title, name = 'get_abstract_matches_title'),
    path('get-show-license/', views.get_license, name='get_license'),
    path('get-show-constraint/', views.get_constraint, name='get_constraint'),

]
