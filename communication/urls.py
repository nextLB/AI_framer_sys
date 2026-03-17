from django.urls import path
from . import views

urlpatterns = [
    path('', views.connection_list, name='connection_list'),
    path('<int:connection_id>/', views.connection_detail, name='connection_detail'),
    path('messages/', views.message_log_list, name='message_log_list'),
    path('status/', views.connection_status_api, name='connection_status_api'),
    path('device/<int:device_id>/config/', views.device_communication_config, name='device_communication_config'),
    path('robot/receive/', views.robot_receive_data, name='robot_receive_data'),
]