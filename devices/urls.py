from django.urls import path
from . import views

app_name = 'devices'

urlpatterns = [
    path('', views.device_list, name='device_list'),
    path('<int:device_id>/', views.device_detail, name='device_detail'),
    path('register/', views.device_register, name='device_register'),
    path('<int:device_id>/edit/', views.device_edit, name='device_edit'),
    path('<int:device_id>/delete/', views.device_delete, name='device_delete'),
    path('<int:device_id>/config/', views.device_config, name='device_config'),
    path('<int:device_id>/status/', views.device_status_api, name='device_status_api'),
    path('<int:device_id>/mode/<str:mode>/', views.set_device_mode, name='set_mode'),
]