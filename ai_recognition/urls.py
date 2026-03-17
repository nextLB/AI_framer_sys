from django.urls import path
from . import views

app_name = 'ai_recognition'

urlpatterns = [
    path('', views.recognition_dashboard, name='recognition_dashboard'),
    path('start/<int:device_id>/', views.start_recognition, name='start_recognition'),
    path('task/<int:task_id>/', views.recognition_task_detail, name='recognition_task_detail'),
    path('task/<int:task_id>/run/', views.run_recognition_api, name='run_recognition_api'),
    path('history/', views.recognition_history, name='recognition_history'),
    path('config/', views.recognition_config_list, name='recognition_config_list'),
    path('config/create/', views.recognition_config_create, name='recognition_config_create'),
    path('config/<int:config_id>/edit/', views.recognition_config_edit, name='recognition_config_edit'),
]