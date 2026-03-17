from django.urls import path
from . import views

app_name = 'monitoring'

urlpatterns = [
    path('', views.monitoring_dashboard, name='monitoring_dashboard'),
    path('device/<int:device_id>/', views.device_monitoring, name='device_monitoring'),
    path('device/<int:device_id>/sensor/', views.sensor_data_api, name='sensor_data_api'),
    path('device/<int:device_id>/gps/', views.gps_data_api, name='gps_data_api'),
    path('devices/status/', views.all_devices_status, name='all_devices_status'),
]